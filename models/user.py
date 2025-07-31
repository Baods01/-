"""
RBAC系统用户模型模块

本模块定义了用户实体的ORM模型类，包含用户的基本信息字段、
关系映射、业务方法等。

Classes:
    User: 用户模型类

Author: AI Assistant
Created: 2025-07-19
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.orm import relationship

from .base_model import BaseModel


class User(BaseModel):
    """
    用户模型类
    
    用于表示系统中的用户实体，包含用户的基本信息如用户名、邮箱、
    密码哈希等，以及与角色的关联关系。
    
    Attributes:
        id (int): 用户唯一标识
        username (str): 用户名，用于登录，最大长度32字符
        email (str): 邮箱地址，用于登录和通知，最大长度64字符
        password_hash (str): 密码哈希值，最大长度255字符
        status (int): 用户状态，1=启用，0=禁用
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
        
    Relationships:
        user_roles: 用户的角色关联列表
        roles: 用户拥有的角色列表（通过user_roles）
        assigned_user_roles: 用户分配的角色关联列表（作为分配人）
        granted_role_permissions: 用户授权的权限关联列表（作为授权人）
    
    Example:
        >>> user = User(username="admin", email="admin@example.com")
        >>> user.is_active()
        True
        >>> user.validate_email("test@example.com")
        True
    """
    
    __tablename__ = 'users'
    __allow_unmapped__ = True  # 允许传统注解，兼容SQLAlchemy 2.0
    
    # 字段定义
    username = Column(
        String(32),
        nullable=False,
        unique=True,
        comment='用户名'
    )
    email = Column(
        String(64),
        nullable=False,
        unique=True,
        comment='邮箱地址'
    )
    password_hash = Column(
        String(255),
        nullable=False,
        comment='密码哈希值(bcrypt)'
    )
    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment='状态：1=启用，0=禁用'
    )
    
    # 索引定义
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_email', 'email'),
        Index('idx_status_created', 'status', 'created_at'),
    )
    
    # 关系映射
    # 用户的角色关联（一对多）
    user_roles = relationship(
        "UserRole",
        foreign_keys="UserRole.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # 用户分配的角色关联（自引用，一对多）
    assigned_user_roles = relationship(
        "UserRole",
        foreign_keys="UserRole.assigned_by",
        back_populates="assigner"
    )

    # 用户授权的权限关联（自引用，一对多）
    granted_role_permissions = relationship(
        "RolePermission",
        foreign_keys="RolePermission.granted_by",
        back_populates="granter"
    )
    
    def __init__(self, **kwargs):
        """
        构造方法

        Args:
            **kwargs: 字段值的关键字参数
        """
        super().__init__(**kwargs)
    
    def validate_username(self, username: str) -> bool:
        """
        验证用户名格式
        
        用户名规则：
        - 长度3-32字符
        - 只能包含字母、数字、下划线
        - 必须以字母开头
        
        Args:
            username (str): 要验证的用户名
            
        Returns:
            bool: 验证是否通过
            
        Example:
            >>> user = User()
            >>> user.validate_username("admin123")
            True
            >>> user.validate_username("123admin")
            False
        """
        if not username or not isinstance(username, str):
            return False
        
        # 长度检查
        if len(username) < 3 or len(username) > 32:
            return False
        
        # 格式检查：字母开头，只包含字母、数字、下划线
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
        return re.match(pattern, username) is not None
    
    def validate_email(self, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email (str): 要验证的邮箱地址
            
        Returns:
            bool: 验证是否通过
            
        Example:
            >>> user = User()
            >>> user.validate_email("admin@example.com")
            True
            >>> user.validate_email("invalid-email")
            False
        """
        if not email or not isinstance(email, str):
            return False
        
        # 长度检查
        if len(email) > 64:
            return False
        
        # 邮箱格式检查
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_active(self) -> bool:
        """
        检查用户是否启用
        
        Returns:
            bool: 如果用户状态为启用返回True，否则返回False
        """
        return self.status == 1
    
    def activate(self):
        """启用用户"""
        self.status = 1
        self.update_timestamp()
    
    def deactivate(self):
        """禁用用户"""
        self.status = 0
        self.update_timestamp()
    
    def set_password_hash(self, password_hash: str):
        """
        设置密码哈希值
        
        Args:
            password_hash (str): 密码哈希值
            
        Raises:
            ValueError: 当密码哈希值格式不正确时
        """
        if not password_hash or len(password_hash) > 255:
            raise ValueError("密码哈希值不能为空且长度不能超过255字符")
        
        self.password_hash = password_hash
        self.update_timestamp()
    
    def get_roles(self) -> List['Role']:
        """
        获取用户的所有角色
        
        Returns:
            List[Role]: 用户拥有的角色列表
        """
        return [ur.role for ur in self.user_roles if ur.status == 1]
    
    def has_role(self, role_code: str) -> bool:
        """
        检查用户是否具有特定角色
        
        Args:
            role_code (str): 角色代码
            
        Returns:
            bool: 如果用户具有该角色返回True，否则返回False
        """
        roles = self.get_roles()
        return any(role.role_code == role_code for role in roles)
    
    def get_permissions(self) -> List['Permission']:
        """
        获取用户的所有权限（通过角色）
        
        Returns:
            List[Permission]: 用户拥有的权限列表
        """
        permissions = []
        roles = self.get_roles()
        
        for role in roles:
            role_permissions = role.get_permissions()
            permissions.extend(role_permissions)
        
        # 去重
        unique_permissions = []
        seen_codes = set()
        for permission in permissions:
            if permission.permission_code not in seen_codes:
                unique_permissions.append(permission)
                seen_codes.add(permission.permission_code)
        
        return unique_permissions
    
    def has_permission(self, permission_code: str) -> bool:
        """
        检查用户是否具有特定权限
        
        Args:
            permission_code (str): 权限代码
            
        Returns:
            bool: 如果用户具有该权限返回True，否则返回False
        """
        permissions = self.get_permissions()
        return any(permission.permission_code == permission_code for permission in permissions)
    
    def validate(self) -> bool:
        """
        数据验证
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            ValueError: 当数据验证失败时
        """
        # 调用父类验证
        super().validate()
        
        # 用户名验证
        if not self.validate_username(self.username):
            raise ValueError("用户名格式不正确：长度3-32字符，字母开头，只能包含字母、数字、下划线")
        
        # 邮箱验证
        if not self.validate_email(self.email):
            raise ValueError("邮箱格式不正确")
        
        # 密码哈希验证
        if not self.password_hash or len(self.password_hash) > 255:
            raise ValueError("密码哈希值不能为空且长度不能超过255字符")
        
        # 状态验证
        if self.status not in [0, 1]:
            raise ValueError("用户状态只能是0（禁用）或1（启用）")
        
        return True
    
    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Args:
            exclude_fields (list, optional): 要排除的字段列表
            
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        # 默认排除敏感字段
        if exclude_fields is None:
            exclude_fields = ['password_hash']
        elif 'password_hash' not in exclude_fields:
            exclude_fields.append('password_hash')
        
        return super().to_dict(exclude_fields=exclude_fields)
    
    def to_public_dict(self) -> Dict[str, Any]:
        """
        转换为公开的字典格式（排除敏感信息）
        
        Returns:
            Dict[str, Any]: 公开的字典格式数据
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'status': self.status,
            'is_active': self.is_active(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 对象的字符串表示
        """
        return f"User(id={self.id}, username='{self.username}', email='{self.email}', status={self.status})"
    
    def __repr__(self) -> str:
        """
        开发者表示
        
        Returns:
            str: 对象的开发者表示
        """
        return self.__str__()
