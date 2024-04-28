import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


class ConfigFileNotFoundError(Exception):
    """Exception to raise of config file can not be located."""


class NoDomainsConfiguredError(Exception):
    """Exception to raise if config does not specify any domains for DDNS."""


class EmptyListOfIPProviders(Exception):
    """Exception to raise if an empty list is provided for IP providers config."""


class NoLoopIntervalProvidedError(Exception):
    """Exception to raise if set to looping but no interval is provided."""


@dataclass
class DomainConfig:
    domain_name: str
    tags: list[str] = field(default_factory=list)
    ttl: int | None = None
    proxied: bool = False
    comment: str | None = None


@dataclass
class Config:
    zone_id: str
    bearer_token: str
    looping: bool = False
    loop_interval: int | None = None
    domain_configs: list[DomainConfig] = field(default_factory=list)
    ipv4_providers: list[str] | None = None
    get_ip_request_timeout: int = 10
    cloudflare_request_timeout: int = 10

    def __post_init__(self):
        self._validate_domain_configs()
        self._validate_ipv4_providers()

    def _validate_domain_configs(self):
        if not self.domain_configs:
            raise NoDomainsConfiguredError(
                "At least one domain must be configured to use for DDNS"
            )

    def _validate_ipv4_providers(self):
        if self.ipv4_providers is not None and not self.ipv4_providers:
            raise EmptyListOfIPProviders(
                "Provided an empty list for IP providers config. Provide at least one or do not"
                " configure this field in order to use the default list of providers "
                "(see README)."
            )

    def _validate_loop_interval(self):
        if self.loop_interval and not self.loop_interval:
            raise NoLoopIntervalProvidedError(
                "Please provide a loop interval when setting looping to true."
            )


def _get_config_file_path() -> Path:
    parser = argparse.ArgumentParser(
        prog="Cloudflare DDNS",
        description="Dynamically determines the public IPV4 address of the running host and sets the specified "
        "cloudflare DNS records to point to this address",
        epilog="For help on what the config should contain please see the README located at "
        "https://github.com/TheLonelyNull/cloudflare-dynamic-dns/blob/main/README.md",
    )
    parser.add_argument(
        "--config",
        help="Path to config file (default: ./config.json)",
        required=False,
        default=Path("config.json"),
    )
    args = parser.parse_args()
    path = Path(args.config)

    # Check file exists
    if not path.is_file():
        raise ConfigFileNotFoundError(
            f"Config file could not be found at {path.resolve()}"
        )

    return path


def _get_config_from_file(path: Path) -> Config:
    contents = path.open("r").read()
    contents_json = json.loads(contents)
    config = Config(**contents_json)
    config.domain_configs = [
        DomainConfig(**domain_config) for domain_config in config.domain_configs
    ]
    return config


def get_config() -> Config:
    config_path = _get_config_file_path()
    return _get_config_from_file(config_path)
