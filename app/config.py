"""Single source of truth for application settings (DRY).

Every value has a sensible default and can be overridden with an environment
variable, so the SAME image runs unchanged on a laptop, in Docker and in
Kubernetes. Nothing else in the code base hardcodes these values.
"""
import os
from dataclasses import dataclass, field


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: _env("APP_NAME", "flask-app"))
    app_version: str = field(default_factory=lambda: _env("APP_VERSION", "dev"))
    app_env: str = field(default_factory=lambda: _env("APP_ENV", "local"))
    port: int = field(default_factory=lambda: int(_env("PORT", "5000")))
    # Inside Kubernetes HOSTNAME is the pod name, which shows which replica answered.
    hostname: str = field(default_factory=lambda: _env("HOSTNAME", "localhost"))


settings = Settings()
