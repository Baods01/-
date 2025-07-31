"""
RBAC系统模型层模块

本模块包含RBAC权限系统的所有ORM模型类，包括用户、角色、权限等核心实体
以及它们之间的关联关系模型。

Classes:
    BaseModel: 基础模型类，提供通用功能
    User: 用户模型类
    Role: 角色模型类
    Permission: 权限模型类
    UserRole: 用户角色关联模型类
    RolePermission: 角色权限关联模型类

Author: AI Assistant
Created: 2025-07-19
"""

from .base_model import BaseModel
from .user import User
from .role import Role
from .permission import Permission
from .user_role import UserRole
from .role_permission import RolePermission

__all__ = [
    'BaseModel',
    'User',
    'Role', 
    'Permission',
    'UserRole',
    'RolePermission'
]
