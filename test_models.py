import asyncio
from app.ai.models import models

async def main():
    for name, func in models.get_fallback_chain():
        print(f"\nTesting {name}...")
        try:
            response = ""
            async for token in func("Reply with only: Hello"):
                response += token
            print(f"SUCCESS: {response}")
        except Exception as e:
            print(f"FAILED: {e}")

asyncio.run(main())