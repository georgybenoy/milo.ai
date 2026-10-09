"""
Run live Q&A with Gemini to answer the four example questions from §0.3.
Prints the transcript of tool calls and the final answer for each.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.data_loader import load_orders
from app.config import CSV_PATH, GEMINI_API_KEY, GEMINI_MODEL
from app.agent import chat

QUESTIONS = [
    ("Order Lookup", "Where is order ORD-1025?"),
    ("Cancelled Orders Count", "How many orders were cancelled?"),
    ("Electronics August Revenue", "What was our revenue from Electronics in August 2026?"),
    ("Top Customer", "Who is our top customer by total spend?"),
]


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY is not set in .env. Cannot run live QA.")
        sys.exit(1)

    load_orders(CSV_PATH)
    print(f"Running live QA using model '{GEMINI_MODEL}'...\n")

    for title, q in QUESTIONS:
        print(f"==================================================")
        print(f"QUERY: {title}")
        print(f"USER: {q}")
        print(f"--------------------------------------------------")
        try:
            result = await chat(q)
            history = result.get("tool_calls_history", [])
            print(f"TOOL CALLS ({len(history)}):")
            for idx, call in enumerate(history, 1):
                print(f"  [{idx}] {call['tool']}({call['args']})")
            print(f"\nMILO REPLY:\n{result['reply']}")
        except Exception as e:
            print(f"ERROR: {e}")
        print(f"==================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
