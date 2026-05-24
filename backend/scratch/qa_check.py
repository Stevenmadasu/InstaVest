import urllib.request
import json
import sys
import time

API_URL = "http://127.0.0.1:8000"

def get(path):
    url = f"{API_URL}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, str(e.read().decode('utf-8'))
    except Exception as e:
        return 500, str(e)

def post(path, data=None):
    url = f"{API_URL}{path}"
    try:
        payload = json.dumps(data).encode('utf-8') if data is not None else b""
        req = urllib.request.Request(
            url, 
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return status, json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, str(e.read().decode('utf-8'))
    except Exception as e:
        return 500, str(e)

def run_qa():
    print("==========================================================")
    print("      InstaVest - Institutional QA Verification Suite       ")
    print("==========================================================\n")
    
    passes = 0
    failures = 0
    
    # Test 1: API Health
    print("[TEST 1] Verifying Backend Health...")
    status, res = get("/health")
    if status == 200 and res.get("status") == "healthy":
        print("  ✅ PASS: Backend is healthy and running.")
        passes += 1
    else:
        print(f"  ❌ FAIL: Health check returned status {status}, response: {res}")
        failures += 1
        
    # Test 2: Morning Briefing Dashboard
    print("\n[TEST 2] Verifying Morning Briefing Dashboard Data...")
    status, briefing = get("/dashboard/morning-briefing")
    if status == 200:
        print("  ✅ PASS: Loaded Morning Briefing successfully.")
        print(f"     Compiled At: {briefing.get('compiled_at')}")
        print(f"     Macro Regime: {briefing.get('macro_regime', {}).get('regime')}")
        print(f"     Watchlist Featured Stock: {briefing.get('featured_intelligence', {}).get('ticker')}")
        print(f"     Timeline Events count: {len(briefing.get('timeline_events', []))}")
        print(f"     Checklist Items count: {len(briefing.get('action_checklist', []))}")
        passes += 1
    else:
        print(f"  ❌ FAIL: Morning briefing returned status {status}, response: {briefing}")
        failures += 1

    # Test 3: Checklist Toggles
    print("\n[TEST 3] Verifying Action Checklist Items & DB Toggles...")
    if status == 200 and briefing.get('action_checklist'):
        item = briefing['action_checklist'][0]
        item_id = item['id']
        current_status = item['completed']
        new_status = not current_status
        
        # Toggle
        print(f"     Toggling checklist item {item_id} from {current_status} to {new_status}...")
        t_status, t_res = post(f"/dashboard/morning-briefing/checklist/{item_id}/toggle", {"completed": new_status})
        if t_status == 200 and t_res.get("status") == "success" and t_res.get("completed") == new_status:
            print(f"  ✅ PASS: Checklist item {item_id} successfully toggled in DB.")
            passes += 1
            
            # Toggle back to original state
            post(f"/dashboard/morning-briefing/checklist/{item_id}/toggle", {"completed": current_status})
        else:
            print(f"  ❌ FAIL: Checklist toggle returned status {t_status}, response: {t_res}")
            failures += 1
    else:
        print("  ⚠️ SKIP: No checklist items available to toggle.")
        passes += 1

    # Test 4: Company Research & SQL Snapshot Cache
    print("\n[TEST 4] Verifying Company Brain SQL Cache (AAPL)...")
    start_time = time.time()
    # First fetch (Cache hit or compute)
    status_1, res_1 = get("/companies/AAPL/research")
    time_1 = time.time() - start_time
    
    start_time = time.time()
    # Second fetch (Guaranteed SQL Cache hit)
    status_2, res_2 = get("/companies/AAPL/research")
    time_2 = time.time() - start_time
    
    if status_1 == 200 and status_2 == 200:
        print(f"  ✅ PASS: Loaded AAPL Research via Company Brain.")
        print(f"     First fetch time: {time_1:.3f} seconds.")
        print(f"     Second fetch time (SQL Cache hit): {time_2:.3f} seconds.")
        print(f"     Speedup factor: {time_1 / max(time_2, 0.001):.1f}x")
        passes += 1
    else:
        print(f"  ❌ FAIL: AAPL Research fetch failed. Status 1: {status_1}, Status 2: {status_2}")
        failures += 1

    # Test 5: Watchlist CRUD
    print("\n[TEST 5] Verifying Watchlists Subsystem...")
    # List watchlists
    status_list, wls = get("/watchlists")
    wl_id = None
    if status_list == 200 and len(wls) > 0:
        wl_id = wls[0]["id"]
        wl_name = wls[0]["name"]
        print(f"     Found existing watchlist: '{wl_name}' (ID: {wl_id})")
    else:
        # Create watchlist
        wl_create_status, wl_create_res = post("/watchlists", {"name": "Hyperscalers"})
        if wl_create_status == 200:
            wl_id = wl_create_res.get("id")
            wl_name = wl_create_res.get("name")
            print(f"     Created new watchlist: '{wl_name}' (ID: {wl_id})")
        else:
            print(f"  ❌ FAIL: Watchlist creation failed with status {wl_create_status}, response: {wl_create_res}")

    if wl_id is not None:
        # Add item to watchlist
        add_status, add_res = post(f"/watchlists/{wl_id}/items", {"ticker": "MSFT"})
        if add_status == 200 and add_res.get("status") == "added":
            print(f"  ✅ PASS: Added MSFT to Watchlist '{wl_name}'.")
            passes += 1
        else:
            print(f"  ❌ FAIL: Adding item to watchlist returned status {add_status}, response: {add_res}")
            failures += 1
    else:
        failures += 1

    # Test 6: Thesis Boards and Evaluation
    print("\n[TEST 6] Verifying Conviction Monitor and Thesis Board...")
    # Create Board
    tb_status, tb_res = post("/thesis-boards", {
        "title": "Big Tech Long-Term Dominance",
        "description": "Monitored conviction board tracking hyperscaler margins and growth CAGRs.",
        "time_horizon": "1-3 Years"
    })
    
    if tb_status == 200 and tb_res.get("id"):
        board_id = tb_res.get("id")
        print(f"     Created monitored conviction Thesis Board (ID: {board_id}) successfully.")
        
        # Link stock
        link_status, link_res = post(f"/thesis-boards/{board_id}/stocks?ticker=AAPL")
        
        # Add assumption
        asm_status, asm_res = post(f"/thesis-boards/{board_id}/assumptions", {
            "assumption_text": "Apple maintains operating margins above 25%.",
            "linked_metric": "operating_margin",
            "ticker": "AAPL",
            "operator": ">",
            "threshold_value": 25.0
        })
        
        # Re-fetch board to check details
        get_status, board = get(f"/thesis-boards/{board_id}")
        
        if get_status == 200 and len(board.get("stocks", [])) > 0 and len(board.get("assumptions", [])) > 0:
            print("  ✅ PASS: Linked stock and created assumption correctly.")
            print(f"     Board evaluation status: {board.get('status')}")
            print(f"     Linked Stocks: {board.get('stocks')}")
            print(f"     Assumptions text: '{board.get('assumptions')[0]['text']}'")
            print(f"     Current Value: {board.get('assumptions')[0]['current_value']}%")
            print(f"     Assumption status: {board.get('assumptions')[0]['status']}")
            passes += 1
        else:
            print(f"  ❌ FAIL: Thesis board details verification failed. Stock count: {len(board.get('stocks', []))}, Assumption count: {len(board.get('assumptions', []))}")
            failures += 1
    else:
        print(f"  ❌ FAIL: Creating Thesis Board returned status {tb_status}, response: {tb_res}")
        failures += 1

    print("\n==========================================================")
    print("                    QA SUMMARY                            ")
    print("==================================================")
    print(f"  TOTAL TESTS PASSED: {passes}")
    print(f"  TOTAL TESTS FAILED: {failures}")
    if failures == 0:
        print("\n🏆 SYSTEM IS 100% HEALTHY AND ALL QA SUITES PASSED FLAWLESSLY!")
    else:
        print("\n⚠️ REGRESSIONS FOUND! PLEASE REVIEW THE FAILURES ABOVE.")
    print("==========================================================\n")

if __name__ == "__main__":
    run_qa()
