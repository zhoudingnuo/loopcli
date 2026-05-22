"""Test bug fixes"""
import sys
import json
sys.path.insert(0, "main/webui")

from server import query_usage_summary, get_main_agent_activity

print("=== Test 1: Usage API ===")
result = query_usage_summary()
if "error" in result:
    print(f"[FAIL] {result['error']}")
else:
    print(f"[OK] {result['total_tokens']:,} tokens, ${result['estimated_cost_usd']:.2f}")

print("\n=== Test 2: Agent Activity API ===")
activity = get_main_agent_activity()
print(f"Status: {activity['status']}")
print(f"Log file exists: {activity['log_file_exists']}")
print(f"Last update: {activity.get('last_log_time', 'N/A')}")
print(f"Latest output count: {len(activity.get('latest_output', []))}")
