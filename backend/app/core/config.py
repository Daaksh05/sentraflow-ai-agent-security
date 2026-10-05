"""Core configuration for SentraFlow backend application."""

import os
from typing import List, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Server & Environment
    PROJECT_NAME: str = "SentraFlow"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", description="Execution environment (development, staging, production)")
    LOG_LEVEL: str = Field(default="INFO", description="Application log level")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Enforcement & Security Mode ('ENFORCE' or 'AUDIT_ONLY')
    ENFORCEMENT_MODE: str = Field(default="ENFORCE", description="Interception mode: 'ENFORCE' or 'AUDIT_ONLY'")
    ACTIVE_POLICY_PROFILE: str = Field(default="default_strict", description="Default policy profile identifier or path")

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database (PostgreSQL)
    POSTGRES_USER: str = "sentraflow_user"
    POSTGRES_PASSWORD: str = "sentraflow_password"
    POSTGRES_DB: str = "sentraflow_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sentraflow_user:sentraflow_password@localhost:5432/sentraflow_db",
        description="Async database connection string"
    )

    # State & Event Handling (Redis)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection string")

    # NVIDIA Nemotron & AI Configuration
    # Supported values: 'mock', 'nemotron_api', 'nemotron_nim'
    AI_MODEL_PROVIDER: str = Field(default="mock", description="Active AI model provider")
    NVIDIA_API_KEY: str = Field(default="", description="NVIDIA API Key for cloud Nemotron / NIM")
    NVIDIA_MODEL: str = Field(default="nvidia/nemotron-4-340b-instruct", description="NVIDIA Nemotron model identifier")
    NVIDIA_BASE_URL: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="NVIDIA NIM or API base URL"
    )


settings = Settings()
