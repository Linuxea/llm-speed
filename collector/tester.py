"""LLM API tester with performance metrics."""

import asyncio
import time

from openai import AsyncOpenAI

from shared.models import ProviderConfig, CollectorConfig, MetricResult


async def test_all_models(
    providers: list[ProviderConfig],
    config: CollectorConfig
) -> list[MetricResult]:
    """Test all models from all providers.

    Args:
        providers: List of provider configurations.
        config: Collector configuration.

    Returns:
        List of MetricResult for all tested models.
    """
    results = []

    for provider in providers:
        if not provider.api_key:
            for model in provider.models:
                results.append(MetricResult(
                    provider_name=provider.name,
                    model_id=model.id,
                    success=False,
                    error_message="API key not configured"
                ))
            continue

        client = AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
            timeout=config.timeout_seconds,
        )

        for model in provider.models:
            result = await _test_single_model(client, model.id, provider.name, config)
            results.append(result)

            # Small delay between tests to avoid rate limits
            await asyncio.sleep(1)

    return results


async def _test_single_model(
    client: AsyncOpenAI,
    model_id: str,
    provider_name: str,
    config: CollectorConfig
) -> MetricResult:
    """Test a single model and calculate metrics.

    Args:
        client: OpenAI async client.
        model_id: Model identifier.
        provider_name: Provider name for result.
        config: Collector configuration.

    Returns:
        MetricResult with performance data.
    """
    start_time = time.time()

    try:
        response = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": config.test_prompt}],
            max_tokens=config.max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )

        # Measure TTFT (Time To First Token)
        # Note: Reasoning models (like GLM-5) use reasoning_content instead of content
        first_chunk = None

        async for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                # Check for regular content
                if delta.content:
                    first_chunk = chunk
                    break
                # Check for reasoning content (GLM-5, DeepSeek Reasoner, etc.)
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    first_chunk = chunk
                    break

        ttft_ms = (time.time() - start_time) * 1000 if first_chunk else None

        # Consume remaining stream and get usage
        completion_tokens = 0
        prompt_tokens = 0

        async for chunk in response:
            if chunk.usage:
                completion_tokens = chunk.usage.completion_tokens
                prompt_tokens = chunk.usage.prompt_tokens

        total_time_ms = (time.time() - start_time) * 1000

        # Calculate tokens per second
        tokens_per_second = None
        if ttft_ms and completion_tokens:
            generation_time_ms = total_time_ms - ttft_ms
            if generation_time_ms > 0:
                tokens_per_second = completion_tokens / (generation_time_ms / 1000)

        return MetricResult(
            provider_name=provider_name,
            model_id=model_id,
            ttft_ms=ttft_ms,
            total_time_ms=total_time_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            tokens_per_second=tokens_per_second,
            success=True,
        )

    except Exception as e:
        total_time_ms = (time.time() - start_time) * 1000
        return MetricResult(
            provider_name=provider_name,
            model_id=model_id,
            total_time_ms=total_time_ms,
            success=False,
            error_message=str(e),
        )
