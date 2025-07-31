"""
RBAC系统角色权限关联模型模块

本模块定义了角色权限关联实体的ORM模型类，处理角色与权限的多对多关系，
包含关联的审计信息和状态管理。

Classes:
    RolePermission: 角色权限关联模型类

Author: AI Assistant
Created: 2025-07-19
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, SmallInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base_model import BaseModel


class RolePermission(BaseModel):
    """
    角色权限关联模型类
    
    用于表示角色与权限之间的多对多关系，包含关联的审计信息如授权时间、
    授权人、状态等。使用复合主键确保角色权限关联的唯一性。
    
    Attributes:
        role_id (int): 角色ID，外键关联roles表
        permission_id (int): 权限ID，外键关联permissions表
        granted_at (datetime): 授权时间
        granted_by (int): 授权人ID，外键关联users表，可选
        status (int): 关联状态，1=启用，0=禁用
        
    Relationships:
        role: 关联的角色对象
        permission: 关联的权限对象
        granter: 授权人用户对象
    
    Example:
        >>> role_permission = RolePermission(role_id=1, permission_id=2, granted_by=3)
        >>> role_permission.is_active()
        True
        >>> role_permission.activate()
        >>> role_permission.deactivate()
    """
    
    __tablename__ = 'role_permissions'
    __allow_unmapped__ = True  # 允许传统注解，兼容SQLAlchemy 2.0
    
    # 覆盖父类的id字段，使用复合主键
    id = None  # 移除单一主键
    
    # 复合主键字段
    role_id = Column(
        SmallInteger,
        ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True,
        comment='角色ID'
    )
    permission_id = Column(
        SmallInteger,
        ForeignKey('permissions.id', ondelete='CASCADE'),
        primary_key=True,
        comment='权限ID'
    )

    # 审计字段
    granted_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='授权时间'
    )
    granted_by = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment='授权人ID'
    )
    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment='状态：1=启用，0=禁用'
    )
    
    # 索引定义
    __table_args__ = (
        Index('idx_role_perm_role_id', 'role_id'),
        Index('idx_role_perm_permission_id', 'permission_id'),
        Index('idx_role_perm_granted_by', 'granted_by'),
        Index('idx_role_perm_status_granted', 'status', 'granted_at'),
    )
    
    # 关系映射
    role = relationship(
        "Role", 
        foreign_keys=[role_id], 
        back_populates="role_permissions"
    )
    permission = relationship(
        "Permission", 
        foreign_keys=[permission_id], 
        back_populates="role_permissions"
    )
    granter = relationship(
        "User", 
        foreign_keys=[granted_by], 
        back_populates="granted_role_permissions"
    )
    
    def __init__(self, **kwargs):
        """
        构造方法
        
        Args:
            **kwargs: 字段值的关键字参数
        """
        # 设置授权时间
        if 'granted_at' not in kwargs:
            kwargs['granted_at'] = datetime.utcnow()
        
        # 调用父类构造方法，但跳过id相关处理
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # 设置时间戳（不包括id字段）
        now = datetime.utcnow()
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = now
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            self.updated_at = now
    
    def is_active(self) -> bool:
        """
        检查关联是否启用
        
        Returns:
            bool: 如果关联状态为启用返回True，否则返回False
        """
        return self.status == 1
    
    def activate(self):
        """启用关联"""
        self.status = 1
        self.update_timestamp()
    
    def deactivate(self):
        """禁用关联"""
        self.status = 0
        self.update_timestamp()
    
    def get_role_info(self) -> Dict[str, Any]:
        """
        获取关联角色的基本信息
        
        Returns:
            Dict[str, Any]: 角色基本信息
        """
        if self.role:
            return {
                'role_id': self.role.id,
                'role_name': self.role.role_name,
                'role_code': self.role.role_code,
                'role_status': self.role.status
            }
        return {}
    
    def get_permission_info(self) -> Dict[str, Any]:
        """
        获取关联权限的基本信息
        
        Returns:
            Dict[str, Any]: 权限基本信息
        """
        if self.permission:
            return {
                'permission_id': self.permission.id,
                'permission_name': self.permission.permission_name,
                'permission_code': self.permission.permission_code,
                'resource_type': self.permission.resource_type,
                'action_type': self.permission.action_type
            }
        return {}
    
    def get_granter_info(self) -> Dict[str, Any]:
        """
        获取授权人的基本信息
        
        Returns:
            Dict[str, Any]: 授权人基本信息
        """
        if self.granter:
            return {
                'granter_id': self.granter.id,
                'granter_username': self.granter.username,
                'granter_email': self.granter.email
            }
        return {}
    
    def is_granted_by_user(self, user_id: int) -> bool:
        """
        检查是否由特定用户授权
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 如果是由该用户授权返回True，否则返回False
        """
        return self.granted_by == user_id
    
    def get_grant_duration(self) -> Optional[int]:
        """
        获取授权持续时间（天数）
        
        Returns:
            Optional[int]: 授权持续天数，如果无法计算返回None
        """
        if self.granted_at:
            duration = datetime.utcnow() - self.granted_at
            return duration.days
        return None
    
    def is_system_permission(self) -> bool:
        """
        检查是否为系统级权限
        
        Returns:
            bool: 如果是系统级权限返回True，否则返回False
        """
        return self.permission and self.permission.is_system_permission()
    
    def is_read_permission(self) -> bool:
        """
        检查是否为只读权限
        
        Returns:
            bool: 如果是只读权限返回True，否则返回False
        """
        return self.permission and self.permission.is_read_permission()
    
    def is_write_permission(self) -> bool:
        """
        检查是否为写权限
        
        Returns:
            bool: 如果是写权限返回True，否则返回False
        """
        return self.permission and self.permission.is_write_permission()
    
    def get_permission_scope(self) -> str:
        """
        获取权限范围描述
        
        Returns:
            str: 权限范围描述
        """
        if self.permission:
            return f"{self.permission.resource_type}:{self.permission.action_type}"
        return "unknown:unknown"
    
    def validate(self) -> bool:
        """
        数据验证
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            ValueError: 当数据验证失败时
        """
        # 基础字段验证
        if not hasattr(self, 'created_at') or self.created_at is None:
            raise ValueError("创建时间不能为空")
        
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            raise ValueError("更新时间不能为空")
        
        # 角色ID验证
        if not self.role_id or self.role_id <= 0:
            raise ValueError("角色ID必须是正整数")
        
        # 权限ID验证
        if not self.permission_id or self.permission_id <= 0:
            raise ValueError("权限ID必须是正整数")
        
        # 授权时间验证
        if not self.granted_at:
            raise ValueError("授权时间不能为空")
        
        # 授权人ID验证（可选）
        if self.granted_by is not None and self.granted_by <= 0:
            raise ValueError("授权人ID必须是正整数")
        
        # 状态验证
        if self.status not in [0, 1]:
            raise ValueError("关联状态只能是0（禁用）或1（启用）")
        
        return True
    
    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Args:
            exclude_fields (list, optional): 要排除的字段列表
            
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        exclude_fields = exclude_fields or []
        result = {}
        
        # 手动添加字段（因为没有单一主键id）
        fields = ['role_id', 'permission_id', 'granted_at', 'granted_by', 'status', 'created_at', 'updated_at']
        
        for field_name in fields:
            if field_name not in exclude_fields and hasattr(self, field_name):
                value = getattr(self, field_name)
                # 处理datetime类型
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                else:
                    result[field_name] = value
        
        return result
    
    def to_detail_dict(self) -> Dict[str, Any]:
        """
        转换为详细的字典格式（包含关联对象信息）
        
        Returns:
            Dict[str, Any]: 详细的字典格式数据
        """
        base_dict = self.to_dict()
        base_dict.update({
            'is_active': self.is_active(),
            'grant_duration_days': self.get_grant_duration(),
            'permission_scope': self.get_permission_scope(),
            'is_system_permission': self.is_system_permission(),
            'is_read_permission': self.is_read_permission(),
            'is_write_permission': self.is_write_permission(),
            'role_info': self.get_role_info(),
            'permission_info': self.get_permission_info(),
            'granter_info': self.get_granter_info()
        })
        return base_dict
    
    def is_new(self) -> bool:
        """
        检查是否为新创建的对象（重写父类方法）
        
        Returns:
            bool: 如果是新对象返回True，否则返回False
        """
        # 对于复合主键，检查是否已经持久化到数据库
        return not (self.role_id and self.permission_id and self.created_at)
    
    def __eq__(self, other) -> bool:
        """
        相等性比较
        
        Args:
            other: 要比较的对象
            
        Returns:
            bool: 如果相等返回True，否则返回False
        """
        if not isinstance(other, RolePermission):
            return False
        
        return (self.role_id == other.role_id and 
                self.permission_id == other.permission_id)
    
    def __hash__(self) -> int:
        """
        哈希值计算
        
        Returns:
            int: 对象的哈希值
        """
        return hash((self.__class__.__name__, self.role_id, self.permission_id))
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 对象的字符串表示
        """
        return (f"RolePermission(role_id={self.role_id}, permission_id={self.permission_id}, "
                f"granted_at='{self.granted_at}', granted_by={self.granted_by}, "
                f"status={self.status})")
    
    def __repr__(self) -> str:
        """
        开发者表示
        
        Returns:
            str: 对象的开发者表示
        """
        return self.__str__()
