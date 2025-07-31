"""
RBAC系统权限模型模块

本模块定义了权限实体的ORM模型类，包含权限的基本信息字段、
关系映射、业务方法等。

Classes:
    Permission: 权限模型类

Author: AI Assistant
Created: 2025-07-19
"""

import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Set

from sqlalchemy import Column, SmallInteger, String, DateTime, Index
from sqlalchemy.orm import relationship

from .base_model import BaseModel


class Permission(BaseModel):
    """
    权限模型类
    
    用于表示系统中的权限实体，包含权限的基本信息如权限名称、权限代码、
    资源类型、操作类型等，以及与角色的关联关系。
    
    Attributes:
        id (int): 权限唯一标识
        permission_name (str): 权限显示名称，最大长度64字符
        permission_code (str): 权限代码，用于程序中识别，最大长度64字符
        resource_type (str): 资源类型，最大长度32字符
        action_type (str): 操作类型，最大长度16字符
        created_at (datetime): 创建时间
        
    Relationships:
        role_permissions: 权限的角色关联列表
        roles: 拥有该权限的角色列表（通过role_permissions）
    
    Example:
        >>> permission = Permission(
        ...     permission_name="用户管理-查看",
        ...     permission_code="user:view",
        ...     resource_type="user",
        ...     action_type="view"
        ... )
        >>> permission.get_full_permission()
        "user:view"
        >>> permission.matches_resource_action("user", "view")
        True
    """
    
    __tablename__ = 'permissions'
    __allow_unmapped__ = True  # 允许传统注解，兼容SQLAlchemy 2.0
    
    # 字段定义
    permission_name = Column(
        String(64),
        nullable=False,
        comment='权限名称'
    )
    permission_code = Column(
        String(64),
        nullable=False,
        unique=True,
        comment='权限代码'
    )
    resource_type = Column(
        String(32),
        nullable=False,
        comment='资源类型'
    )
    action_type = Column(
        String(16),
        nullable=False,
        comment='操作类型'
    )
    
    # 权限表只有创建时间，没有更新时间
    updated_at = None  # 覆盖父类的updated_at字段
    
    # 索引定义
    __table_args__ = (
        Index('idx_permission_code', 'permission_code'),
        Index('idx_resource_action', 'resource_type', 'action_type'),
    )
    
    # 常用的资源类型
    RESOURCE_TYPES: Set[str] = {
        'user', 'role', 'permission', 'system', 'report', 'audit'
    }
    
    # 常用的操作类型
    ACTION_TYPES: Set[str] = {
        'view', 'create', 'edit', 'delete', 'export', 'import', 'approve'
    }
    
    # 关系映射
    # 权限的角色关联（一对多）
    role_permissions = relationship(
        "RolePermission",
        foreign_keys="RolePermission.permission_id",
        back_populates="permission",
        cascade="all, delete-orphan"
    )
    
    def __init__(self, **kwargs):
        """
        构造方法
        
        Args:
            **kwargs: 字段值的关键字参数
        """
        # 权限表没有updated_at字段，从kwargs中移除
        if 'updated_at' in kwargs:
            del kwargs['updated_at']
        
        super().__init__(**kwargs)
        
        # 权限创建后不再更新，所以不需要updated_at
        if hasattr(self, 'updated_at'):
            delattr(self, 'updated_at')
    
    def validate_permission_code(self, permission_code: str) -> bool:
        """
        验证权限代码格式
        
        权限代码规则：
        - 格式：resource_type:action_type
        - 长度5-64字符
        - 只能包含小写字母、数字、下划线、冒号
        
        Args:
            permission_code (str): 要验证的权限代码
            
        Returns:
            bool: 验证是否通过
            
        Example:
            >>> permission = Permission()
            >>> permission.validate_permission_code("user:view")
            True
            >>> permission.validate_permission_code("User:View")
            False
        """
        if not permission_code or not isinstance(permission_code, str):
            return False
        
        # 长度检查
        if len(permission_code) < 5 or len(permission_code) > 64:
            return False
        
        # 格式检查：resource:action格式
        if ':' not in permission_code:
            return False
        
        parts = permission_code.split(':')
        if len(parts) != 2:
            return False
        
        resource, action = parts
        
        # 检查resource和action部分的格式
        pattern = r'^[a-z][a-z0-9_]*$'
        return (re.match(pattern, resource) is not None and 
                re.match(pattern, action) is not None)
    
    def validate_resource_type(self, resource_type: str) -> bool:
        """
        验证资源类型格式
        
        Args:
            resource_type (str): 要验证的资源类型
            
        Returns:
            bool: 验证是否通过
        """
        if not resource_type or not isinstance(resource_type, str):
            return False
        
        # 长度检查
        if len(resource_type) < 2 or len(resource_type) > 32:
            return False
        
        # 格式检查：小写字母开头，只包含小写字母、数字、下划线
        pattern = r'^[a-z][a-z0-9_]*$'
        return re.match(pattern, resource_type) is not None
    
    def validate_action_type(self, action_type: str) -> bool:
        """
        验证操作类型格式
        
        Args:
            action_type (str): 要验证的操作类型
            
        Returns:
            bool: 验证是否通过
        """
        if not action_type or not isinstance(action_type, str):
            return False
        
        # 长度检查
        if len(action_type) < 2 or len(action_type) > 16:
            return False
        
        # 格式检查：小写字母开头，只包含小写字母、数字、下划线
        pattern = r'^[a-z][a-z0-9_]*$'
        return re.match(pattern, action_type) is not None
    
    def get_full_permission(self) -> str:
        """
        获取完整权限描述
        
        Returns:
            str: 完整权限描述，格式为"resource_type:action_type"
        """
        return f"{self.resource_type}:{self.action_type}"
    
    def matches_resource_action(self, resource_type: str, action_type: str) -> bool:
        """
        匹配资源和操作类型
        
        Args:
            resource_type (str): 资源类型
            action_type (str): 操作类型
            
        Returns:
            bool: 如果匹配返回True，否则返回False
        """
        return (self.resource_type == resource_type and 
                self.action_type == action_type)
    
    def get_roles(self) -> List['Role']:
        """
        获取拥有该权限的所有角色
        
        Returns:
            List[Role]: 拥有该权限的角色列表
        """
        return [rp.role for rp in self.role_permissions if rp.status == 1]
    
    def get_role_count(self) -> int:
        """
        获取拥有该权限的角色数量
        
        Returns:
            int: 角色数量
        """
        return len([rp for rp in self.role_permissions if rp.status == 1])
    
    def is_system_permission(self) -> bool:
        """
        检查是否为系统级权限
        
        Returns:
            bool: 如果是系统级权限返回True，否则返回False
        """
        return self.resource_type == 'system'
    
    def is_read_permission(self) -> bool:
        """
        检查是否为只读权限
        
        Returns:
            bool: 如果是只读权限返回True，否则返回False
        """
        return self.action_type in ['view', 'list', 'read']
    
    def is_write_permission(self) -> bool:
        """
        检查是否为写权限
        
        Returns:
            bool: 如果是写权限返回True，否则返回False
        """
        return self.action_type in ['create', 'edit', 'update', 'delete', 'write']
    
    @classmethod
    def get_resource_types(cls) -> Set[str]:
        """
        获取所有资源类型
        
        Returns:
            Set[str]: 资源类型集合
        """
        return cls.RESOURCE_TYPES.copy()
    
    @classmethod
    def get_action_types(cls) -> Set[str]:
        """
        获取所有操作类型
        
        Returns:
            Set[str]: 操作类型集合
        """
        return cls.ACTION_TYPES.copy()
    
    @classmethod
    def create_permission_code(cls, resource_type: str, action_type: str) -> str:
        """
        创建权限代码
        
        Args:
            resource_type (str): 资源类型
            action_type (str): 操作类型
            
        Returns:
            str: 权限代码
        """
        return f"{resource_type}:{action_type}"
    
    def validate(self) -> bool:
        """
        数据验证
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            ValueError: 当数据验证失败时
        """
        # 调用父类验证（但跳过updated_at检查）
        if not hasattr(self, 'id') or self.id is None:
            pass
        
        if not hasattr(self, 'created_at') or self.created_at is None:
            raise ValueError("创建时间不能为空")
        
        # 权限名称验证
        if not self.permission_name or len(self.permission_name.strip()) < 2 or len(self.permission_name) > 64:
            raise ValueError("权限名称格式不正确：长度2-64字符，不能为空")
        
        # 权限代码验证
        if not self.validate_permission_code(self.permission_code):
            raise ValueError("权限代码格式不正确：格式为resource:action，只能包含小写字母、数字、下划线")
        
        # 资源类型验证
        if not self.validate_resource_type(self.resource_type):
            raise ValueError("资源类型格式不正确：长度2-32字符，小写字母开头，只能包含小写字母、数字、下划线")
        
        # 操作类型验证
        if not self.validate_action_type(self.action_type):
            raise ValueError("操作类型格式不正确：长度2-16字符，小写字母开头，只能包含小写字母、数字、下划线")
        
        # 检查权限代码与资源类型、操作类型的一致性
        expected_code = self.create_permission_code(self.resource_type, self.action_type)
        if self.permission_code != expected_code:
            raise ValueError(f"权限代码与资源类型、操作类型不一致：期望{expected_code}，实际{self.permission_code}")
        
        return True
    
    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Args:
            exclude_fields (list, optional): 要排除的字段列表
            
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        # 权限表没有updated_at字段
        if exclude_fields is None:
            exclude_fields = ['updated_at']
        elif 'updated_at' not in exclude_fields:
            exclude_fields.append('updated_at')
        
        return super().to_dict(exclude_fields=exclude_fields)
    
    def to_detail_dict(self) -> Dict[str, Any]:
        """
        转换为详细的字典格式（包含统计信息）
        
        Returns:
            Dict[str, Any]: 详细的字典格式数据
        """
        base_dict = self.to_dict()
        base_dict.update({
            'full_permission': self.get_full_permission(),
            'role_count': self.get_role_count(),
            'is_system_permission': self.is_system_permission(),
            'is_read_permission': self.is_read_permission(),
            'is_write_permission': self.is_write_permission()
        })
        return base_dict
    
    def update_timestamp(self):
        """权限不支持更新时间戳"""
        pass  # 权限创建后不再更新
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 对象的字符串表示
        """
        return (f"Permission(id={self.id}, permission_name='{self.permission_name}', "
                f"permission_code='{self.permission_code}', resource_type='{self.resource_type}', "
                f"action_type='{self.action_type}')")
    
    def __repr__(self) -> str:
        """
        开发者表示
        
        Returns:
            str: 对象的开发者表示
        """
        return self.__str__()
