import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "http://localhost:8000/api/analyze",
            data={"resume_text": "I am a software engineer with 5 years of Python experience.", "job_description": "We need a Python software engineer."}
        )
        print(resp.status_code)
        print(resp.text)

asyncio.run(main())
