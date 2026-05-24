import sys
import os
import datetime

# Adjust path to import app correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.repositories import (
    users_repository,
    watchlists_repository,
    thesis_repository,
    filings_repository,
    intelligence_repository,
)
from app.services.intelligence_snapshot import get_or_compute_snapshot
from app.models.reverse_dcf import run_reverse_dcf
from app.db.models import User, Watchlist, ThesisBoard, Filing

def run_advanced_qa():
    print("======================================================================")
    print("          InstaVest - Advanced Operational QA Verification Suite       ")
    print("======================================================================\n")

    db = SessionLocal()
    
    passes = 0
    failures = 0

    try:
        # ─────────────────────────────────────────────────────────────
        # Part 1: COLD-START PIPELINE QA
        # ─────────────────────────────────────────────────────────────
        print("[TEST 1] Cold-Start Pipeline QA: Checking new ticker (TSLA)...")
        # Ensure clean cache by deleting any existing TSLA snapshots
        db.query(Base.metadata.tables["company_intelligence_snapshots"]).filter_by(ticker="TSLA").delete(synchronize_session=False)
        db.commit()
        
        # Trigger first-time snapshot compute
        start_time = datetime.datetime.now()
        snapshot = get_or_compute_snapshot(ticker="TSLA", db=db, force_refresh=True)
        compute_duration = (datetime.datetime.now() - start_time).total_seconds()
        
        if "error" not in snapshot:
            print("  ✅ PASS: TSLA Cold-Start Precomputations compiled smoothly.")
            print(f"     Duration: {compute_duration:.3f} seconds.")
            print(f"     Financial version token: {snapshot.get('financial_version')}")
            print(f"     Signal version token: {snapshot.get('signal_version')}")
            print(f"     AI Synthesis model version: {snapshot.get('ai_version')}")
            
            # Check cached snapshot persistence in DB
            db_snap = intelligence_repository.get_latest_company_snapshot(db, "TSLA")
            if db_snap:
                print("  ✅ PASS: Snapshot cached successfully in PostgreSQL.")
                passes += 2
            else:
                print("  ❌ FAIL: Snapshot computed but not saved in DB.")
                failures += 1
        else:
            print(f"  ❌ FAIL: TSLA Cold-start precomputation failed. Error: {snapshot.get('error')}")
            failures += 2

        # ─────────────────────────────────────────────────────────────
        # Part 2: AUTH / USER SCOPING QA
        # ─────────────────────────────────────────────────────────────
        print("\n[TEST 2] Auth/User Scoping QA: Ensuring user isolation & data boundaries...")
        
        # 1. Setup two clean test users
        email_a = "user_a@instavest.ai"
        email_b = "user_b@instavest.ai"
        
        # Cleanup if they exist with all dependent cascade records
        existing_users = db.query(User).filter(User.email.in_([email_a, email_b])).all()
        existing_user_ids = [u.id for u in existing_users]
        if existing_user_ids:
            # Delete dependent WatchlistItems
            existing_wls = db.query(Watchlist).filter(Watchlist.user_id.in_(existing_user_ids)).all()
            existing_wl_ids = [wl.id for wl in existing_wls]
            if existing_wl_ids:
                db.query(Base.metadata.tables["watchlist_items"]).filter(Base.metadata.tables["watchlist_items"].c.watchlist_id.in_(existing_wl_ids)).delete(synchronize_session=False)
                
            # Delete dependent ThesisStocks and ThesisAssumptions
            existing_tbs = db.query(ThesisBoard).filter(ThesisBoard.user_id.in_(existing_user_ids)).all()
            existing_tb_ids = [tb.id for tb in existing_tbs]
            if existing_tb_ids:
                db.query(Base.metadata.tables["thesis_stocks"]).filter(Base.metadata.tables["thesis_stocks"].c.thesis_board_id.in_(existing_tb_ids)).delete(synchronize_session=False)
                db.query(Base.metadata.tables["thesis_assumptions"]).filter(Base.metadata.tables["thesis_assumptions"].c.thesis_board_id.in_(existing_tb_ids)).delete(synchronize_session=False)
                
            # Delete Watchlists and ThesisBoards
            db.query(Watchlist).filter(Watchlist.user_id.in_(existing_user_ids)).delete(synchronize_session=False)
            db.query(ThesisBoard).filter(ThesisBoard.user_id.in_(existing_user_ids)).delete(synchronize_session=False)
            
            # Delete Users
            db.query(User).filter(User.id.in_(existing_user_ids)).delete(synchronize_session=False)
            db.commit()
        
        user_a = users_repository.get_or_create_user(
            db, email=email_a, name="User Alpha", firebase_uid="fb_uid_alpha", display_name="Alpha"
        )
        user_b = users_repository.get_or_create_user(
            db, email=email_b, name="User Beta", firebase_uid="fb_uid_beta", display_name="Beta"
        )
        
        print(f"     Created User A (ID: {user_a.id}, UID: {user_a.firebase_uid})")
        print(f"     Created User B (ID: {user_b.id}, UID: {user_b.firebase_uid})")
        
        # 2. Create Watchlist and Thesis Board for User A
        wl_a = watchlists_repository.create_watchlist(db, user_id=user_a.id, name="User A Growth Tickers")
        watchlists_repository.add_item(db, watchlist_id=wl_a.id, ticker="NVDA")
        
        tb_a = thesis_repository.create_board(
            db, user_id=user_a.id, title="User A AI Supercycle", description="User A conviction board", time_horizon="long"
        )
        thesis_repository.add_stock(db, board_id=tb_a.id, ticker="NVDA")
        
        print(f"     Created Watchlist (ID: {wl_a.id}) and Thesis Board (ID: {tb_a.id}) linked exclusively to User A.")
        
        # 3. Retrieve watchlists for User A and User B separately
        wls_retrieved_a = watchlists_repository.list_watchlists(db, user_id=user_a.id)
        wls_retrieved_b = watchlists_repository.list_watchlists(db, user_id=user_b.id)
        
        # Assert A sees A's watchlist
        a_contains_watchlist = any(w.id == wl_a.id for w in wls_retrieved_a)
        # Assert B DOES NOT see A's watchlist
        b_contains_watchlist = any(w.id == wl_a.id for w in wls_retrieved_b)
        
        if a_contains_watchlist and not b_contains_watchlist:
            print("  ✅ PASS: Watchlist query correctly scoped to current user_id. No data leaks found.")
            passes += 1
        else:
            print(f"  ❌ FAIL: Watchlist data leak or query error. User A has watchlist: {a_contains_watchlist}, User B has watchlist: {b_contains_watchlist}")
            failures += 1

        # 4. Retrieve Thesis Boards for User A and User B
        tbs_retrieved_a = thesis_repository.list_boards(db, user_id=user_a.id)
        tbs_retrieved_b = thesis_repository.list_boards(db, user_id=user_b.id)
        
        a_contains_board = any(b.id == tb_a.id for b in tbs_retrieved_a)
        b_contains_board = any(b.id == tb_a.id for b in tbs_retrieved_b)
        
        if a_contains_board and not b_contains_board:
            print("  ✅ PASS: Monitored Conviction Thesis Boards correctly scoped to current user_id. User isolation verified.")
            passes += 1
        else:
            print(f"  ❌ FAIL: Thesis board data leak or query error. User A has board: {a_contains_board}, User B has board: {b_contains_board}")
            failures += 1

        # Cleanup test users and their cascade records
        # A. Delete WatchlistItems
        wl_ids = [wl.id for wl in wls_retrieved_a] + [wl.id for wl in wls_retrieved_b]
        if wl_ids:
            db.query(Base.metadata.tables["watchlist_items"]).filter(Base.metadata.tables["watchlist_items"].c.watchlist_id.in_(wl_ids)).delete(synchronize_session=False)
            
        # B. Delete ThesisStocks & ThesisAssumptions
        tb_ids = [tb.id for tb in tbs_retrieved_a] + [tb.id for tb in tbs_retrieved_b]
        if tb_ids:
            db.query(Base.metadata.tables["thesis_stocks"]).filter(Base.metadata.tables["thesis_stocks"].c.thesis_board_id.in_(tb_ids)).delete(synchronize_session=False)
            db.query(Base.metadata.tables["thesis_assumptions"]).filter(Base.metadata.tables["thesis_assumptions"].c.thesis_board_id.in_(tb_ids)).delete(synchronize_session=False)

        db.query(Watchlist).filter(Watchlist.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db.query(ThesisBoard).filter(ThesisBoard.user_id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_([user_a.id, user_b.id])).delete(synchronize_session=False)
        db.commit()

        # ─────────────────────────────────────────────────────────────
        # Part 3: SEC INGESTION PIPELINE QA
        # ─────────────────────────────────────────────────────────────
        print("\n[TEST 3] SEC Ingestion QA: Parsing and registering regulatory filings...")
        
        ticker = "AMZN"
        form_type = "10-K"
        filing_date = datetime.date.today()
        accession = "0001018724-26-000005"
        cik = "0001018724"
        filing_url = "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000005/amzn-20261231.htm"
        
        # Ingest filing
        filing = filings_repository.upsert_filing(
            db=db,
            ticker=ticker,
            cik=cik,
            accession_number=accession,
            form_type=form_type,
            filing_date=filing_date,
            report_date=datetime.date(2026, 12, 31),
            filing_url=filing_url,
            raw_text_path="/var/sec/storage/AMZN_10K_2026.txt",
            source="sec_edgar"
        )
        
        if filing and filing.accession_number == accession:
            print("  ✅ PASS: SEC Filing successfully upserted into SQL database.")
            
            # Fetch filings
            all_filings = filings_repository.get_filings(db, ticker)
            matched_filings = [f for f in all_filings if f.accession_number == accession]
            
            if matched_filings:
                print("  ✅ PASS: Filing accurately retrieved by ticker.")
                print(f"     Ticker: {matched_filings[0].ticker}")
                print(f"     Accession Number: {matched_filings[0].accession_number}")
                print(f"     Form Type: {matched_filings[0].form_type}")
                print(f"     Filing Date: {matched_filings[0].filing_date}")
                print(f"     URL Link: {matched_filings[0].filing_url}")
                passes += 2
            else:
                print("  ❌ FAIL: Filing upserted but not retrieved.")
                failures += 1
        else:
            print("  ❌ FAIL: SEC Ingestion database upsert returned empty or mismatch.")
            failures += 2

        # Cleanup filing
        db.query(Filing).filter(Filing.accession_number == accession).delete(synchronize_session=False)
        db.commit()

    except Exception as e:
        print(f"\n⚠️ SYSTEM ERROR RUNNING QA ENGINES: {e}")
        import traceback
        traceback.print_exc()
        failures += 1
    finally:
        db.close()

    print("\n======================================================================")
    print("                          QA SUMMARY                                  ")
    print("======================================================================")
    print(f"  TOTAL TESTS PASSED: {passes}")
    print(f"  TOTAL TESTS FAILED: {failures}")
    if failures == 0:
        print("\n🏆 COLD-START, USER-ISOLATION, AND SEC INGESTION PIPELINES PASSED 100%!")
    else:
        print("\n⚠️ SYSTEM INCONSISTENCY DETECTED. REVIEW PIPELINE DEFICIENCIES.")
    print("======================================================================\n")

if __name__ == "__main__":
    run_qa = run_advanced_qa()
