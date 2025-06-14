"""
Core configuration settings for the Unified Memory Server
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    MCP_PORT: int = Field(default=9000, env="MCP_PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    DISABLE_AUTH: bool = Field(default=True, env="DISABLE_AUTH")  # Default to disabled for development
    JWT_SECRET: Optional[str] = Field(default=None, env="JWT_SECRET")
    OAUTH2_ISSUER_URL: Optional[str] = Field(default=None, env="OAUTH2_ISSUER_URL")
    OAUTH2_AUDIENCE: Optional[str] = Field(default=None, env="OAUTH2_AUDIENCE")
    OAUTH2_ALGORITHMS: List[str] = Field(default=["RS256"], env="OAUTH2_ALGORITHMS")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Neo4j Configuration
    NEO4J_ENABLED: bool = Field(default=True, env="NEO4J_ENABLED")
    NEO4J_URL: str = Field(default="bolt://localhost:7687", env="NEO4J_URL")
    NEO4J_USERNAME: str = Field(default="neo4j", env="NEO4J_USERNAME")
    NEO4J_PASSWORD: str = Field(default="password", env="NEO4J_PASSWORD")
    NEO4J_MCP_MEMORY_URL: str = Field(default="http://localhost:8001", env="NEO4J_MCP_MEMORY_URL")
    NEO4J_MCP_CYPHER_URL: str = Field(default="http://localhost:8002", env="NEO4J_MCP_CYPHER_URL")
    
    # Basic Memory Configuration  
    BASIC_MEMORY_ENABLED: bool = Field(default=True, env="BASIC_MEMORY_ENABLED")
    BASIC_MEMORY_URL: str = Field(default="http://localhost:8080", env="BASIC_MEMORY_URL")
    BASIC_MEMORY_AUTH_TOKEN: Optional[str] = Field(default=None, env="BASIC_MEMORY_AUTH_TOKEN")
    
    # Memory Configuration
    LONG_TERM_MEMORY: bool = Field(default=True, env="LONG_TERM_MEMORY")
    WINDOW_SIZE: int = Field(default=20, env="WINDOW_SIZE")
    ENABLE_TOPIC_EXTRACTION: bool = Field(default=True, env="ENABLE_TOPIC_EXTRACTION")
    ENABLE_NER: bool = Field(default=True, env="ENABLE_NER")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Documentation
    ENABLE_SWAGGER_UI: bool = Field(default=True, env="ENABLE_SWAGGER_UI")
    
    # CAB Monitoring
    CAB_MONITORING_ENABLED: bool = Field(default=True, env="CAB_MONITORING_ENABLED")
    CAB_LOG_PATH: str = Field(default="/var/log/unified-memory/cab-suggestions.log", env="CAB_LOG_PATH")
    CAB_SEVERITY_THRESHOLD: str = Field(default="MEDIUM", env="CAB_SEVERITY_THRESHOLD")
    
    model_config = {
        "env_file": [".env.production", ".env.local", ".env"],
        "env_file_encoding": "utf-8"
    }


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings