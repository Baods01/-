"""
RBAC权限系统 - JWT认证配置模块

本模块定义JWT令牌的各种配置参数，
包括密钥、算法、过期时间等安全相关配置。

配置项包括：
- JWT密钥和算法
- 令牌过期时间
- 刷新令牌配置
- 安全策略配置

作者: RBAC System Development Team
创建时间: 2025-07-21
版本: 1.0.0
"""

import os
import secrets
from datetime import timedelta
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class JWTConfig(BaseSettings):
    """JWT配置类"""
    
    # JWT密钥配置
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT签名密钥"
    )
    algorithm: str = Field(default="HS256", description="JWT签名算法")
    
    # 访问令牌配置
    access_token_expire_minutes: int = Field(
        default=15, 
        description="访问令牌过期时间（分钟）"
    )
    
    # 刷新令牌配置
    refresh_token_expire_days: int = Field(
        default=7,
        description="刷新令牌过期时间（天）"
    )
    
    # 记住我功能配置
    remember_me_expire_days: int = Field(
        default=30,
        description="记住我功能令牌过期时间（天）"
    )
    
    # 令牌发行者和受众
    issuer: str = Field(default="rbac-system", description="令牌发行者")
    audience: str = Field(default="rbac-users", description="令牌受众")
    
    # 安全配置
    require_https: bool = Field(default=False, description="是否要求HTTPS")
    token_url: str = Field(default="/api/auth/token", description="获取令牌的URL")
    
    # 令牌黑名单配置
    enable_token_blacklist: bool = Field(
        default=True,
        description="是否启用令牌黑名单"
    )
    blacklist_check_interval: int = Field(
        default=300,
        description="黑名单检查间隔（秒）"
    )
    
    # 密码重置令牌配置
    password_reset_expire_minutes: int = Field(
        default=30,
        description="密码重置令牌过期时间（分钟）"
    )
    
    # 邮箱验证令牌配置
    email_verify_expire_hours: int = Field(
        default=24,
        description="邮箱验证令牌过期时间（小时）"
    )
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """验证密钥长度"""
        if len(v) < 32:
            raise ValueError("JWT密钥长度至少需要32个字符")
        return v
    
    @validator("algorithm")
    def validate_algorithm(cls, v):
        """验证签名算法"""
        allowed_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in allowed_algorithms:
            raise ValueError(f"不支持的算法: {v}")
        return v
    
    def get_access_token_expire_delta(self) -> timedelta:
        """获取访问令牌过期时间间隔"""
        return timedelta(minutes=self.access_token_expire_minutes)
    
    def get_refresh_token_expire_delta(self, remember_me: bool = False) -> timedelta:
        """获取刷新令牌过期时间间隔"""
        if remember_me:
            return timedelta(days=self.remember_me_expire_days)
        return timedelta(days=self.refresh_token_expire_days)
    
    def get_password_reset_expire_delta(self) -> timedelta:
        """获取密码重置令牌过期时间间隔"""
        return timedelta(minutes=self.password_reset_expire_minutes)
    
    def get_email_verify_expire_delta(self) -> timedelta:
        """获取邮箱验证令牌过期时间间隔"""
        return timedelta(hours=self.email_verify_expire_hours)
    
    class Config:
        env_file = ".env"
        env_prefix = "JWT_"
        case_sensitive = False


class DevelopmentJWTConfig(JWTConfig):
    """开发环境JWT配置"""
    
    # 开发环境使用较长的过期时间，便于调试
    access_token_expire_minutes: int = 60  # 1小时
    refresh_token_expire_days: int = 30    # 30天
    require_https: bool = False


class ProductionJWTConfig(JWTConfig):
    """生产环境JWT配置"""
    
    # 生产环境使用较短的过期时间，提高安全性
    access_token_expire_minutes: int = 15  # 15分钟
    refresh_token_expire_days: int = 7     # 7天
    require_https: bool = True
    
    @validator("secret_key")
    def validate_production_secret_key(cls, v):
        """生产环境密钥验证"""
        if v == "your-secret-key" or len(v) < 64:
            raise ValueError("生产环境必须使用强密钥（至少64个字符）")
        return v


class TestJWTConfig(JWTConfig):
    """测试环境JWT配置"""
    
    # 测试环境使用固定密钥和较短过期时间
    secret_key: str = "test-secret-key-for-testing-only-32chars"
    access_token_expire_minutes: int = 5   # 5分钟
    refresh_token_expire_days: int = 1     # 1天
    require_https: bool = False


def get_jwt_config() -> JWTConfig:
    """根据环境变量获取JWT配置实例"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionJWTConfig()
    elif env == "testing":
        return TestJWTConfig()
    else:
        return DevelopmentJWTConfig()


# 全局JWT配置实例
jwt_config = get_jwt_config()

# 导出配置类和实例
__all__ = [
    "JWTConfig",
    "DevelopmentJWTConfig",
    "ProductionJWTConfig", 
    "TestJWTConfig",
    "get_jwt_config",
    "jwt_config"
]
