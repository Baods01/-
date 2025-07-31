#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限系统工具包
包含密码加密、数据库连接等核心工具类

作者：RBAC权限系统
创建时间：2025-07-17
"""

from .password_utils import (
    PasswordUtils,
    hash_password,
    verify_password,
    generate_password,
    check_password_strength
)

from .db_utils import (
    DatabaseConfig,
    DatabaseManager,
    execute_query,
    execute_update,
    execute_batch
)

__version__ = "1.0.0"
__author__ = "RBAC权限系统"

__all__ = [
    # 密码工具
    'PasswordUtils',
    'hash_password',
    'verify_password', 
    'generate_password',
    'check_password_strength',
    
    # 数据库工具
    'DatabaseConfig',
    'DatabaseManager',
    'execute_query',
    'execute_update',
    'execute_batch'
]
