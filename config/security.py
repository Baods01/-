#!/usr/bin/env python3
"""
RBAC权限系统 - 安全配置

管理JWT密钥、密码策略、安全参数等配置。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import os
import secrets
from typing import Optional


class SecurityConfig:
    """安全配置类"""
    
    # JWT配置
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', None)
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    JWT_REMEMBER_ME_EXPIRE_DAYS: int = int(os.getenv('JWT_REMEMBER_ME_EXPIRE_DAYS', '30'))
    
    # 密码策略
    PASSWORD_MIN_LENGTH: int = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
    PASSWORD_REQUIRE_UPPERCASE: bool = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_LOWERCASE: bool = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_DIGITS: bool = os.getenv('PASSWORD_REQUIRE_DIGITS', 'true').lower() == 'true'
    PASSWORD_REQUIRE_SPECIAL: bool = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true'
    
    # 登录安全
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    LOGIN_LOCKOUT_MINUTES: int = int(os.getenv('LOGIN_LOCKOUT_MINUTES', '30'))
    
    # bcrypt配置
    BCRYPT_ROUNDS: int = int(os.getenv('BCRYPT_ROUNDS', '12'))
    
    # 会话安全
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
    
    # API安全
    API_RATE_LIMIT_PER_MINUTE: int = int(os.getenv('API_RATE_LIMIT_PER_MINUTE', '100'))
    
    @classmethod
    def get_jwt_secret(cls) -> str:
        """获取JWT密钥，如果不存在则生成一个"""
        if not cls.JWT_SECRET_KEY:
            # 生产环境中应该从安全的地方获取密钥
            if os.getenv('ENVIRONMENT') == 'production':
                raise ValueError("生产环境必须设置JWT_SECRET_KEY环境变量")
            
            # 开发环境生成临时密钥
            cls.JWT_SECRET_KEY = secrets.token_urlsafe(32)
            print("⚠️  警告: 使用临时生成的JWT密钥，生产环境请设置JWT_SECRET_KEY环境变量")
        
        return cls.JWT_SECRET_KEY
    
    @classmethod
    def validate_password_strength(cls, password: str) -> tuple[bool, str]:
        """验证密码强度"""
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return False, f"密码长度至少{cls.PASSWORD_MIN_LENGTH}个字符"
        
        if cls.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "密码必须包含大写字母"
        
        if cls.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "密码必须包含小写字母"
        
        if cls.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"
        
        if cls.PASSWORD_REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                return False, "密码必须包含特殊字符"
        
        return True, "密码强度符合要求"
    
    @classmethod
    def is_development(cls) -> bool:
        """判断是否为开发环境"""
        return os.getenv('ENVIRONMENT', 'development') == 'development'
    
    @classmethod
    def is_production(cls) -> bool:
        """判断是否为生产环境"""
        return os.getenv('ENVIRONMENT') == 'production'


# 创建全局配置实例
security_config = SecurityConfig()


def generate_secure_key() -> str:
    """生成安全的密钥"""
    return secrets.token_urlsafe(32)


def create_env_template():
    """创建环境变量模板文件"""
    template = """# RBAC权限系统环境配置
# 复制此文件为.env并修改相应配置

# 环境设置
ENVIRONMENT=development

# JWT配置
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_REMEMBER_ME_EXPIRE_DAYS=30

# 密码策略
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
PASSWORD_REQUIRE_SPECIAL=true

# 登录安全
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=30

# bcrypt配置
BCRYPT_ROUNDS=12

# 会话安全
SESSION_TIMEOUT_MINUTES=30

# API安全
API_RATE_LIMIT_PER_MINUTE=100

# 数据库配置
DATABASE_URL=sqlite:///rbac_system.db
""".format(jwt_secret=generate_secure_key())
    
    return template


if __name__ == "__main__":
    # 生成环境配置模板
    template = create_env_template()
    
    with open('.env.template', 'w', encoding='utf-8') as f:
        f.write(template)
    
    print("✅ 环境配置模板已生成: .env.template")
    print("📋 请复制为.env文件并根据需要修改配置")
    print(f"🔑 已生成安全的JWT密钥: {generate_secure_key()}")
