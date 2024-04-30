import json
import logging
import os

from pydantic import BaseModel, Field, field_validator, ValidationError, model_validator

LOGGER = logging.getLogger(__name__)


class DomainConfig(BaseModel):
    domain_name: str
    tags: list[str] = Field(default_factory=list)
    ttl: int | None = None
    proxied: bool = False
    comment: str | None = None


class Config(BaseModel):
    zone_id: str = Field(..., alias="ZONE_ID")
    bearer_token: str = Field(..., alias="BEARER_TOKEN")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    looping: bool = Field(False, alias="LOOPING")
    loop_interval: int | None = Field(None, alias="LOOP_INTERVAL")
    domain_configs: list[DomainConfig] = Field(
        default_factory=list, alias="DOMAIN_CONFIGS", min_length=1
    )
    ipv4_providers: list[str] | None = Field(None, alias="IPV4_PROVIDERS")

    @model_validator(mode="after")
    def _validate_loop_interval(self):
        if self.loop_interval and not self.loop_interval:
            raise ValidationError(
                "Please provide a loop interval when setting looping to true."
            )

    @field_validator("ipv4_providers")
    @classmethod
    def _validate_ipv4_providers(cls, v) -> list[str]:
        if v is not None and not v:
            raise ValidationError(
                "Provided an empty list for IP providers config. Provide at least one or do not"
                " configure this field in order to use the default list of providers "
                "(see README)."
            )
        return v


def get_config() -> Config:
    environment_variables = dict(os.environ)
    if "DOMAIN_CONFIGS" in environment_variables:
        environment_variables["DOMAIN_CONFIGS"] = json.loads(
            environment_variables["DOMAIN_CONFIGS"]
        )
    return Config(**environment_variables)
