"""
Smoke test script for discovery agent.

Usage:
    python scripts/test_discovery.py https://example.com
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.automation.discovery_agent import DiscoveryAgent


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_discovery.py <seed_url>")
        print("Example: python scripts/test_discovery.py https://stripe.com")
        sys.exit(1)
    
    seed_url = sys.argv[1]
    
    print(f"\n{'='*60}")
    print(f"Discovery Agent Smoke Test")
    print(f"{'='*60}\n")
    print(f"Seed URL: {seed_url}")
    print(f"Running discovery...\n")
    
    agent = DiscoveryAgent(headless=True, timeout=60000)
    success, discovered = await agent.discover_programs(seed_url)
    
    print(f"\n{'='*60}")
    print(f"Results")
    print(f"{'='*60}\n")
    print(f"Success: {success}")
    print(f"Discovered Programs: {len(discovered)}\n")
    
    if discovered:
        for i, program in enumerate(discovered, 1):
            print(f"{i}. {program['name']}")
            print(f"   Signup URL: {program['signup_url']}")
            print(f"   Confidence: {program['confidence']}")
            print(f"   Link Text: {program.get('link_text', 'N/A')[:50]}...")
            print()
    else:
        print("No programs discovered.")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
