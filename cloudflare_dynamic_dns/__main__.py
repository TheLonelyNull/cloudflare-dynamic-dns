import asyncio

from cloudflare_dynamic_dns.api_tools import set_cloudflare_dns_records
from cloudflare_dynamic_dns.config import get_config
from cloudflare_dynamic_dns.ip_tools import get_public_ipv4_address


async def main():
    config = get_config()
    ip = await get_public_ipv4_address()
    await set_cloudflare_dns_records(config, ip)


if __name__ == "__main__":
    asyncio.run(main())
