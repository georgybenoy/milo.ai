"""
Tiny verification script for Gemini API.
Verifies:
1. GEMINI_API_KEY exists.
2. The configured GEMINI_MODEL exists for this API key.
3. Function calling is supported.
4. Quota and response work properly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

api_key = os.getenv("GEMINI_API_KEY", "").strip()
model_id = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

if not api_key:
    print(f"ERROR: GEMINI_API_KEY is not set in {project_root / '.env'}.")
    print("Please set GEMINI_API_KEY in .env before running verification.")
    sys.exit(1)

print(f"Testing model '{model_id}' with google-genai SDK...")

try:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Test function declaration
    test_tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="ping",
                description="Test ping function.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "message": types.Schema(
                            type=types.Type.STRING,
                            description="A message to echo back",
                        )
                    },
                    required=["message"],
                ),
            )
        ]
    )

    response = client.models.generate_content(
        model=model_id,
        contents="Call the ping function with message='hello'.",
        config=types.GenerateContentConfig(
            tools=[test_tool],
            temperature=0.0,
        ),
    )

    # Check function call
    candidate = response.candidates[0] if response.candidates else None
    if not candidate or not candidate.content or not candidate.content.parts:
        print(f"FAILED: Empty candidate received from model '{model_id}'.")
        sys.exit(2)

    function_calls = [p for p in candidate.content.parts if p.function_call]
    if function_calls:
        fc = function_calls[0].function_call
        print(f"SUCCESS: Function calling verified on '{model_id}'. Function called: {fc.name} with args: {dict(fc.args) if fc.args else {}}")
        sys.exit(0)
    else:
        # Fallback check if text was returned instead of function call
        print(f"Model returned text instead of function call: {[p.text for p in candidate.content.parts if p.text]}")
        print("Function calling test did not trigger as expected.")
        sys.exit(3)

except Exception as exc:
    print(f"FAILED: Error communicating with Gemini API: {exc}")
    sys.exit(4)
