import asyncio
import logging

from cloudflare_dynamic_dns.api_tools import set_cloudflare_dns_records
from cloudflare_dynamic_dns.config import get_config, Config
from cloudflare_dynamic_dns.ip_tools import get_public_ipv4_address


def _setup_logging(log_level: str):
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=log_level)
    # Disable httpx info logs.
    logging.getLogger("httpx").disabled = True
    logging.getLogger("httpcore.connection").disabled = True
    logging.getLogger("httpcore.http11").disabled = True


async def _refresh_dns_record(config: Config):
    ip = await get_public_ipv4_address()
    await set_cloudflare_dns_records(config, ip)


async def main():
    config = get_config()
    _setup_logging(config.log_level)
    await _refresh_dns_record(config)

    # Optionally continue looping instead of shutting down.
    while config.looping:
        await asyncio.sleep(config.loop_interval)
        await _refresh_dns_record(config)


if __name__ == "__main__":
    asyncio.run(main())
