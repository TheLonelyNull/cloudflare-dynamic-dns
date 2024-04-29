import logging

import httpx
from httpx import HTTPError

from cloudflare_dynamic_dns.config import Config, DomainConfig

BASE_URL = "https://api.cloudflare.com/client/v4/zones/"
GET_PATH = "/dns_records"
CREATE_PATH = "/dns_records"
OVERWRITE_PATH = "/dns_records"
TIMEOUT = 10

LOGGER = logging.getLogger(__name__)


async def set_cloudflare_dns_records(config: Config, ip: str):
    for domain_config in config.domain_configs:
        existing_record = await _get_existing_dns_record(
            config.zone_id, config.bearer_token, domain_config.domain_name
        )
        if existing_record and existing_record.get("result"):
            # Overwrite
            record = existing_record.get("result")[0]
            if _is_equivalent(record, ip, domain_config):
                LOGGER.info(f"{domain_config.domain_name} up to date. Skipping...")
                continue

            record_id = record["id"]
            await _overwrite_dns_record(
                config.zone_id, config.bearer_token, record_id, ip, domain_config
            )
            LOGGER.info(f"Successfully updated DNS record for {domain_config.domain_name}")

        else:
            # Create a new A record
            await _create_new_dns_record(
                config.zone_id, config.bearer_token, ip, domain_config
            )
            LOGGER.info(f"Successfully created DNS record for {domain_config.domain_name}")


async def _get_existing_dns_record(zone_id: str, bearer_token: str, domain_name: str) -> dict | None:
    url = BASE_URL + zone_id + GET_PATH
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"name": domain_name},
                headers={"Authorization": f"Bearer {bearer_token}"},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
    except (HTTPError, TimeoutError) as e:
        LOGGER.error(f"Error retrieving DNS record for {domain_name}", exc_info=e)
        return None


async def _create_new_dns_record(
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
                    "Comment": domain_config.comment,
                    "tags": domain_config.tags,
                    "ttl": domain_config.ttl
                },
            )
            response.raise_for_status()
            return response.json()
    except (HTTPError, TimeoutError) as e:
        LOGGER.error(f"Error creating DNS record for {domain_config.domain_name}", exc_info=e)


async def _overwrite_dns_record(
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
                    "tags": domain_config.tags,
                    "ttl": domain_config.ttl
                },
            )
            response.raise_for_status()
            return response.json()
    except (HTTPError, TimeoutError) as e:
        LOGGER.error(f"Error updating DNS record for {domain_config.domain_name}", exc_info=e)


def _is_equivalent(existing_record: dict, ip: str, domain_config: DomainConfig) -> bool:
    if existing_record.get("content") != ip:
        return False

    if existing_record.get("proxied") != domain_config.proxied:
        return False

    if existing_record.get("comment") != domain_config.comment:
        return False

    if len(set(existing_record.get("tags")) - set(domain_config.tags)) > 0:
        return False

    if existing_record.get("ttl") != domain_config.ttl:
        return False

    return True
