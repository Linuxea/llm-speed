#!/usr/bin/env python
"""Test script to explore LLM API response formats."""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


async def test_provider(
    provider_name: str,
    base_url: str,
    api_key: str,
    model_id: str,
):
    """Test a single model and print detailed response info."""

    print(f"\n{'='*60}")
    print(f"Testing: {provider_name}/{model_id}")
    print(f"Base URL: {base_url}")
    print(f"{'='*60}")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60,
    )

    # Test 1: Non-streaming request
    print("\n[1] Non-streaming request:")
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "说一个数字"}],
            max_tokens=20,
            stream=False,
        )

        print(f"  Response type: {type(response)}")
        print(f"  ID: {response.id}")
        print(f"  Model: {response.model}")
        print(f"  Content: {response.choices[0].message.content}")

        if response.usage:
            print(f"  Usage:")
            print(f"    prompt_tokens: {response.usage.prompt_tokens}")
            print(f"    completion_tokens: {response.usage.completion_tokens}")
            print(f"    total_tokens: {response.usage.total_tokens}")
        else:
            print(f"  Usage: None ❌")

    except Exception as e:
        print(f"  Error: {e}")

    # Test 2: Streaming request
    print("\n[2] Streaming request:")
    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "说一个数字"}],
            max_tokens=20,
            stream=True,
            stream_options={"include_usage": True},
        )

        chunks = []
        usage_data = None

        async for chunk in response:
            chunks.append(chunk)

            # Check for usage in chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_data = chunk.usage

            # Print first few chunks
            if len(chunks) <= 3:
                print(f"  Chunk {len(chunks)}: {chunk.model_dump_json()[:200]}...")

        print(f"  Total chunks: {len(chunks)}")

        # Check last chunk
        if chunks:
            last_chunk = chunks[-1]
            print(f"  Last chunk: {last_chunk.model_dump_json()[:300]}...")

            if hasattr(last_chunk, 'usage') and last_chunk.usage:
                usage_data = last_chunk.usage

        if usage_data:
            print(f"  Usage from stream:")
            print(f"    prompt_tokens: {usage_data.prompt_tokens}")
            print(f"    completion_tokens: {usage_data.completion_tokens}")
            print(f"    total_tokens: {usage_data.total_tokens}")
        else:
            print(f"  Usage: None ❌")

    except Exception as e:
        print(f"  Error: {e}")

    # Test 3: Check raw response headers
    print("\n[3] Checking response structure:")
    try:
        # Make a simple request and inspect the raw response
        import httpx

        async with httpx.AsyncClient(timeout=60) as http_client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": model_id,
                "messages": [{"role": "user", "content": "说一个数字"}],
                "max_tokens": 20,
                "stream": False,
            }

            resp = await http_client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=data,
            )

            print(f"  Status: {resp.status_code}")
            print(f"  Headers: {dict(resp.headers)}")

            resp_json = resp.json()
            print(f"  Response keys: {resp_json.keys()}")

            if 'usage' in resp_json:
                print(f"  Usage: {resp_json['usage']}")
            else:
                print(f"  Usage: Not in response ❌")

            # Print full response (truncated)
            print(f"  Full response: {json.dumps(resp_json, ensure_ascii=False, indent=2)[:1000]}...")

    except Exception as e:
        print(f"  Error: {e}")


async def main():
    """Test all configured providers."""

    # Get API keys
    zhipu_key = os.getenv("ZHIPU_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    # Test GLM-5 series
    if zhipu_key:
        print("\n" + "="*60)
        print("Testing ZHIPU GLM-5 Series")
        print("="*60)

        await test_provider(
            "zhipu",
            "https://open.bigmodel.cn/api/paas/v4",
            zhipu_key,
            "glm-4-flash",  # Known working
        )

        await test_provider(
            "zhipu",
            "https://open.bigmodel.cn/api/paas/v4",
            zhipu_key,
            "glm-5-turbo",
        )

        await test_provider(
            "zhipu",
            "https://open.bigmodel.cn/api/paas/v4",
            zhipu_key,
            "glm-5",
        )

    # Test DeepSeek for comparison
    if deepseek_key:
        print("\n" + "="*60)
        print("Testing DeepSeek (for comparison)")
        print("="*60)

        await test_provider(
            "deepseek",
            "https://api.deepseek.com/v1",
            deepseek_key,
            "deepseek-chat",
        )


if __name__ == "__main__":
    asyncio.run(main())
