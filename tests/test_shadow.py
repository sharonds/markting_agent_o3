#!/usr/bin/env python3
"""
Test PR-S shadow functionality independently
"""
import os
import sys
sys.path.insert(0, '.')

# Set environment
os.environ["SHADOW"] = "1"
os.environ["PROVIDER_SEARCH"] = "none"
os.environ["PROVIDER_KEYWORDS"] = "llm"

def test_shadow():
    try:
        from app.costs_tools import ToolCostLedger
        from tools.search import SearchAdapter
        from tools.keywords import KeywordAdapter
        
        print("✓ All imports successful")
        
        # Create test artifacts directory
        artifacts_dir = "test_shadow"
        os.makedirs(artifacts_dir, exist_ok=True)
        
        goal = "PR-S shadow test"
        ledger = ToolCostLedger(artifacts_dir)
        print("✓ ToolCostLedger created")
        
        # Test search
        provider_search = os.getenv("PROVIDER_SEARCH", "none")
        sa = SearchAdapter(artifacts_dir, ledger)
        print(f"✓ SearchAdapter created with provider: {provider_search}")
        
        result = sa.search(provider_search, goal)
        print(f"✓ Search completed: {len(result) if result else 0} results")
        
        # Test keywords
        provider_kw = os.getenv("PROVIDER_KEYWORDS", "llm")
        seeds = [w for w in goal.split() if len(w) > 3][:5]
        ka = KeywordAdapter(artifacts_dir, ledger)
        print(f"✓ KeywordAdapter created with provider: {provider_kw}")
        print(f"✓ Seeds: {seeds}")
        
        result2 = ka.enrich(provider_kw, seeds)
        print(f"✓ Keywords completed: {len(result2) if result2 else 0} results")
        
        # Check for shadow files
        shadow_files = [
            os.path.join(artifacts_dir, "search_shadow.json"),
            os.path.join(artifacts_dir, "keywords_shadow.json"),
            os.path.join(artifacts_dir, "tool_usage.json")
        ]
        
        for path in shadow_files:
            if os.path.exists(path):
                print(f"✓ Created: {path}")
            else:
                print(f"✗ Missing: {path}")
        
        print("\n🎯 Shadow test completed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_shadow()
