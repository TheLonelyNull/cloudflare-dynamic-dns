import httpx
from httpx import HTTPError

from cloudflare_dynamic_dns.config import Config, DomainConfig

BASE_URL = "https://api.cloudflare.com/client/v4/zones/"
GET_PATH = "/dns_records"
CREATE_PATH = "/dns_records"
OVERWRITE_PATH = "/dns_records"
TIMEOUT = 10


async def set_cloudflare_dns_records(config: Config, ip: str):
    for domain_config in config.domain_configs:
        existing_record = await get_existing_dns_record(
            config.zone_id, config.bearer_token, domain_config.domain_name
        )
        if existing_record.get("result"):
            # Overwrite
            # TODO check equivalence to avoid unnnecisary update calls, probably log?
            record = existing_record.get("result")[0]
            record_id = record["id"]
            await overwrite_dns_record(
                config.zone_id, config.bearer_token, record_id, ip, domain_config
            )

        else:
            # Create a new A record
            await create_new_dns_record(
                config.zone_id, config.bearer_token, ip, domain_config
            )


async def get_existing_dns_record(zone_id: str, bearer_token: str, domain_name: str):
    url = BASE_URL + zone_id + GET_PATH
    try:
        async with httpx.AsyncClient() as client:
            # TODO different types of auth
            response = await client.get(
                url,
                params={"name": domain_name},
                headers={"Authorization": f"Bearer {bearer_token}"},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
    except (HTTPError, TimeoutError):
        return None


async def create_new_dns_record(
    zone_id: str, bearer_token: str, ip: str, domain_config: DomainConfig
):
    url = BASE_URL + zone_id + CREATE_PATH
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {bearer_token}"},
                timeout=TIMEOUT,
                json={
                    "name": domain_config.domain_name,
                    "content": ip,
                    "proxied": domain_config.proxied,
                    "type": "A",
                    # TODO comment, tags, ttl
                },
            )
            response.raise_for_status()
            return response.json()
    except (HTTPError, TimeoutError):
        return None


async def overwrite_dns_record(
    zone_id: str,
    bearer_token: str,
    dns_record_id: str,
    ip: str,
    domain_config: DomainConfig,
):
    url = BASE_URL + zone_id + CREATE_PATH + "/" + dns_record_id
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers={"Authorization": f"Bearer {bearer_token}"},
                timeout=TIMEOUT,
                json={
                    "name": domain_config.domain_name,
                    "content": ip,
                    "proxied": domain_config.proxied,
                    "type": "A",
                    "Comment": domain_config.comment,
                    # TODO tags, ttl
                },
            )
            response.raise_for_status()
            return response.json()
    except (HTTPError, TimeoutError):
        return None
