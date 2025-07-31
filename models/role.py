"""
RBAC系统角色模型模块

本模块定义了角色实体的ORM模型类，包含角色的基本信息字段、
关系映射、业务方法等。

Classes:
    Role: 角色模型类

Author: AI Assistant
Created: 2025-07-19
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, SmallInteger, String, DateTime, Integer, Index
from sqlalchemy.orm import relationship

from .base_model import BaseModel


class Role(BaseModel):
    """
    角色模型类
    
    用于表示系统中的角色实体，包含角色的基本信息如角色名称、角色代码等，
    以及与用户和权限的关联关系。
    
    Attributes:
        id (int): 角色唯一标识
        role_name (str): 角色显示名称，最大长度32字符
        role_code (str): 角色代码，用于程序中识别，最大长度32字符
        status (int): 角色状态，1=启用，0=禁用
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
        
    Relationships:
        user_roles: 角色的用户关联列表
        users: 拥有该角色的用户列表（通过user_roles）
        role_permissions: 角色的权限关联列表
        permissions: 角色拥有的权限列表（通过role_permissions）
    
    Example:
        >>> role = Role(role_name="管理员", role_code="admin")
        >>> role.is_active()
        True
        >>> role.validate_role_code("admin")
        True
    """
    
    __tablename__ = 'roles'
    __allow_unmapped__ = True  # 允许传统注解，兼容SQLAlchemy 2.0
    
    # 字段定义
    role_name = Column(
        String(32),
        nullable=False,
        comment='角色名称'
    )
    role_code = Column(
        String(32),
        nullable=False,
        unique=True,
        comment='角色代码'
    )
    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment='状态：1=启用，0=禁用'
    )
    
    # 索引定义
    __table_args__ = (
        Index('idx_role_code', 'role_code'),
        Index('idx_status', 'status'),
    )
    
    # 关系映射
    # 角色的用户关联（一对多）
    user_roles = relationship(
        "UserRole",
        foreign_keys="UserRole.role_id",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    # 角色的权限关联（一对多）
    role_permissions = relationship(
        "RolePermission",
        foreign_keys="RolePermission.role_id",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    def __init__(self, **kwargs):
        """
        构造方法
        
        Args:
            **kwargs: 字段值的关键字参数
        """
        super().__init__(**kwargs)
    
    def validate_role_code(self, role_code: str) -> bool:
        """
        验证角色代码格式
        
        角色代码规则：
        - 长度2-32字符
        - 只能包含小写字母、数字、下划线
        - 必须以字母开头
        
        Args:
            role_code (str): 要验证的角色代码
            
        Returns:
            bool: 验证是否通过
            
        Example:
            >>> role = Role()
            >>> role.validate_role_code("admin")
            True
            >>> role.validate_role_code("Admin")
            False
        """
        if not role_code or not isinstance(role_code, str):
            return False
        
        # 长度检查
        if len(role_code) < 2 or len(role_code) > 32:
            return False
        
        # 格式检查：小写字母开头，只包含小写字母、数字、下划线
        pattern = r'^[a-z][a-z0-9_]*$'
        return re.match(pattern, role_code) is not None
    
    def validate_role_name(self, role_name: str) -> bool:
        """
        验证角色名称格式
        
        Args:
            role_name (str): 要验证的角色名称
            
        Returns:
            bool: 验证是否通过
        """
        if not role_name or not isinstance(role_name, str):
            return False
        
        # 长度检查
        if len(role_name.strip()) < 2 or len(role_name) > 32:
            return False
        
        return True
    
    def is_active(self) -> bool:
        """
        检查角色是否启用
        
        Returns:
            bool: 如果角色状态为启用返回True，否则返回False
        """
        return self.status == 1
    
    def activate(self):
        """启用角色"""
        self.status = 1
        self.update_timestamp()
    
    def deactivate(self):
        """禁用角色"""
        self.status = 0
        self.update_timestamp()
    
    def get_users(self) -> List['User']:
        """
        获取拥有该角色的所有用户
        
        Returns:
            List[User]: 拥有该角色的用户列表
        """
        return [ur.user for ur in self.user_roles if ur.status == 1]
    
    def get_permissions(self) -> List['Permission']:
        """
        获取角色的所有权限
        
        Returns:
            List[Permission]: 角色拥有的权限列表
        """
        return [rp.permission for rp in self.role_permissions if rp.status == 1]
    
    def has_permission(self, permission_code: str) -> bool:
        """
        检查角色是否具有特定权限
        
        Args:
            permission_code (str): 权限代码
            
        Returns:
            bool: 如果角色具有该权限返回True，否则返回False
        """
        permissions = self.get_permissions()
        return any(permission.permission_code == permission_code for permission in permissions)
    
    def get_user_count(self) -> int:
        """
        获取拥有该角色的用户数量
        
        Returns:
            int: 用户数量
        """
        return len([ur for ur in self.user_roles if ur.status == 1])
    
    def get_permission_count(self) -> int:
        """
        获取角色拥有的权限数量
        
        Returns:
            int: 权限数量
        """
        return len([rp for rp in self.role_permissions if rp.status == 1])
    
    def get_permissions_by_resource(self, resource_type: str) -> List['Permission']:
        """
        获取角色在特定资源类型上的权限
        
        Args:
            resource_type (str): 资源类型
            
        Returns:
            List[Permission]: 该资源类型的权限列表
        """
        permissions = self.get_permissions()
        return [p for p in permissions if p.resource_type == resource_type]
    
    def can_access_resource(self, resource_type: str, action_type: str) -> bool:
        """
        检查角色是否可以对特定资源执行特定操作
        
        Args:
            resource_type (str): 资源类型
            action_type (str): 操作类型
            
        Returns:
            bool: 如果可以访问返回True，否则返回False
        """
        permissions = self.get_permissions()
        return any(
            p.resource_type == resource_type and p.action_type == action_type 
            for p in permissions
        )
    
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
        
        # 角色名称验证
        if not self.validate_role_name(self.role_name):
            raise ValueError("角色名称格式不正确：长度2-32字符，不能为空")
        
        # 角色代码验证
        if not self.validate_role_code(self.role_code):
            raise ValueError("角色代码格式不正确：长度2-32字符，小写字母开头，只能包含小写字母、数字、下划线")
        
        # 状态验证
        if self.status not in [0, 1]:
            raise ValueError("角色状态只能是0（禁用）或1（启用）")
        
        return True
    
    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Args:
            exclude_fields (list, optional): 要排除的字段列表
            
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        return super().to_dict(exclude_fields=exclude_fields)
    
    def to_detail_dict(self) -> Dict[str, Any]:
        """
        转换为详细的字典格式（包含统计信息）
        
        Returns:
            Dict[str, Any]: 详细的字典格式数据
        """
        base_dict = self.to_dict()
        base_dict.update({
            'is_active': self.is_active(),
            'user_count': self.get_user_count(),
            'permission_count': self.get_permission_count()
        })
        return base_dict
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 对象的字符串表示
        """
        return f"Role(id={self.id}, role_name='{self.role_name}', role_code='{self.role_code}', status={self.status})"
    
    def __repr__(self) -> str:
        """
        开发者表示
        
        Returns:
            str: 对象的开发者表示
        """
        return self.__str__()
