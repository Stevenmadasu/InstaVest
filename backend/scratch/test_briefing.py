import sys
import os

# Adjust path to import app correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.morning_briefing import compile_morning_briefing

try:
    print("Testing morning briefing compilation and running...")
    briefing = compile_morning_briefing()
    print("SUCCESS!")
    print(f"Compiled At: {briefing['compiled_at']}")
    print(f"Regime: {briefing['macro_regime']['regime']}")
    print(f"Watchlist Featured Stock: {briefing['featured_intelligence']['ticker']}")
    print(f"Featured Summary: {briefing['featured_intelligence']['summary']}")
    print(f"Thesis states count: {briefing['thesis_conviction']['stats']}")
    print(f"Active Signals generated: {len(briefing['prioritized_signals'])}")
    print(f"Action Items: {len(briefing['action_checklist'])}")
    print("All subsystems resolved flawlessly.")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
