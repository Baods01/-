"""
RBAC系统数据访问层模块

本模块包含RBAC权限系统的所有DAO（数据访问对象）接口，提供标准的
数据库操作接口，包括CRUD操作、批量操作、事务支持等。

Classes:
    BaseDao: 基础DAO抽象类
    UserDao: 用户DAO接口
    RoleDao: 角色DAO接口
    PermissionDao: 权限DAO接口
    UserRoleDao: 用户角色关联DAO接口
    RolePermissionDao: 角色权限关联DAO接口

Author: AI Assistant
Created: 2025-07-19
"""

from .base_dao import BaseDao
from .user_dao import UserDao
from .role_dao import RoleDao
from .permission_dao import PermissionDao
from .user_role_dao import UserRoleDao
from .role_permission_dao import RolePermissionDao

__all__ = [
    'BaseDao',
    'UserDao',
    'RoleDao',
    'PermissionDao',
    'UserRoleDao',
    'RolePermissionDao'
]
