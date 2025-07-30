#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

from app.costs_tools import ToolCostLedger

artifacts_dir = "debug_shadow"
os.makedirs(artifacts_dir, exist_ok=True)

print("Creating ledger...")
ledger = ToolCostLedger(artifacts_dir)
print(f"Ledger created, artifacts_dir: {ledger.artifacts_dir}")

print("Adding cost entry...")
ledger.add("test_tool", calls=1, eur=0.01)
print(f"Added entry. by_tool: {ledger.by_tool}, total: {ledger.total_eur}")

# Check if file exists
tool_usage_path = os.path.join(artifacts_dir, "tool_usage.json")
if os.path.exists(tool_usage_path):
    print(f"✓ tool_usage.json created at: {tool_usage_path}")
    with open(tool_usage_path) as f:
        content = f.read()
    print(f"Content: {content}")
else:
    print(f"✗ tool_usage.json not found at: {tool_usage_path}")
    
print("Files in artifacts_dir:")
import os
for f in os.listdir(artifacts_dir):
    print(f"  {f}")
