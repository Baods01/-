"""
RBAC权限系统 - API配置模块

本模块定义FastAPI应用的各种配置参数，
支持开发环境和生产环境的配置区分。

配置项包括：
- 应用基本信息
- 服务器配置
- 数据库配置
- 日志配置
- 安全配置

作者: RBAC System Development Team
创建时间: 2025-07-21
版本: 1.0.0
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API配置类"""
    
    # 应用基本信息
    app_name: str = Field(default="RBAC权限系统API", description="应用名称")
    app_description: str = Field(
        default="基于角色的访问控制系统WebAPI，提供完整的用户、角色、权限管理功能",
        description="应用描述"
    )
    app_version: str = Field(default="1.0.0", description="应用版本")
    
    # 服务器配置
    host: str = Field(default="127.0.0.1", description="服务器地址")
    port: int = Field(default=8000, description="服务器端口")
    debug: bool = Field(default=True, description="调试模式")
    reload: bool = Field(default=True, description="自动重载")
    
    # API文档配置
    docs_url: str = Field(default="/docs", description="Swagger文档URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc文档URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI规范URL")
    
    # CORS配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许的跨域源"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="允许的HTTP方法"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        description="允许的请求头"
    )
    
    # 分页配置
    default_page_size: int = Field(default=20, description="默认分页大小")
    max_page_size: int = Field(default=100, description="最大分页大小")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # 环境配置
    environment: str = Field(default="development", description="运行环境")
    
    class Config:
        env_file = ".env"
        env_prefix = "API_"
        case_sensitive = False


class DevelopmentConfig(APIConfig):
    """开发环境配置"""
    
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"
    environment: str = "development"


class ProductionConfig(APIConfig):
    """生产环境配置"""
    
    debug: bool = False
    reload: bool = False
    log_level: str = "WARNING"
    environment: str = "production"
    
    # 生产环境安全配置
    docs_url: Optional[str] = None  # 生产环境禁用文档
    redoc_url: Optional[str] = None
    openapi_url: Optional[str] = None


class TestConfig(APIConfig):
    """测试环境配置"""
    
    debug: bool = True
    reload: bool = False
    log_level: str = "DEBUG"
    environment: str = "testing"
    
    # 测试数据库配置
    database_url: str = "sqlite:///./test_rbac.db"


def get_config() -> APIConfig:
    """根据环境变量获取配置实例"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestConfig()
    else:
        return DevelopmentConfig()


# 全局配置实例
config = get_config()

# 导出配置类和实例
__all__ = [
    "APIConfig",
    "DevelopmentConfig", 
    "ProductionConfig",
    "TestConfig",
    "get_config",
    "config"
]
