import asyncio
from collections import Counter

import httpx
from httpx import HTTPError

IPV4_PROVIDER_URLS: list[str] = [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://api.seeip.org/",
]
TIMEOUT = 10


async def get_public_ipv4_address(ip_provider_urls: list[str] | None = None) -> str:
    ip_provider_urls = ip_provider_urls or IPV4_PROVIDER_URLS  # TODO probably move this
    tasks = [_request_ipv4_address(url) for url in ip_provider_urls]
    results = [result for result in await asyncio.gather(*tasks) if result]
    frequency_count = Counter(results)
    return max(frequency_count.items())[0]  # TODO raise if none found


async def _request_ipv4_address(url: str):  # TODO allow passing in headers, params etc
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.read().decode("utf-8").strip()
    except (HTTPError, TimeoutError):
        return None
