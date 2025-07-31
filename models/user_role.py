"""
RBAC系统用户角色关联模型模块

本模块定义了用户角色关联实体的ORM模型类，处理用户与角色的多对多关系，
包含关联的审计信息和状态管理。

Classes:
    UserRole: 用户角色关联模型类

Author: AI Assistant
Created: 2025-07-19
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, SmallInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base_model import BaseModel


class UserRole(BaseModel):
    """
    用户角色关联模型类
    
    用于表示用户与角色之间的多对多关系，包含关联的审计信息如分配时间、
    分配人、状态等。使用复合主键确保用户角色关联的唯一性。
    
    Attributes:
        user_id (int): 用户ID，外键关联users表
        role_id (int): 角色ID，外键关联roles表
        assigned_at (datetime): 分配时间
        assigned_by (int): 分配人ID，外键关联users表，可选
        status (int): 关联状态，1=启用，0=禁用
        
    Relationships:
        user: 关联的用户对象
        role: 关联的角色对象
        assigner: 分配人用户对象
    
    Example:
        >>> user_role = UserRole(user_id=1, role_id=2, assigned_by=3)
        >>> user_role.is_active()
        True
        >>> user_role.activate()
        >>> user_role.deactivate()
    """
    
    __tablename__ = 'user_roles'
    __allow_unmapped__ = True  # 允许传统注解，兼容SQLAlchemy 2.0
    
    # 覆盖父类的id字段，使用复合主键
    id = None  # 移除单一主键
    
    # 复合主键字段
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
        comment='用户ID'
    )
    role_id = Column(
        SmallInteger,
        ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True,
        comment='角色ID'
    )

    # 审计字段
    assigned_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='分配时间'
    )
    assigned_by = Column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment='分配人ID'
    )
    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment='状态：1=启用，0=禁用'
    )
    
    # 索引定义
    __table_args__ = (
        Index('idx_user_role_user_id', 'user_id'),
        Index('idx_user_role_role_id', 'role_id'),
        Index('idx_user_role_assigned_by', 'assigned_by'),
        Index('idx_user_role_status_assigned', 'status', 'assigned_at'),
    )
    
    # 关系映射
    user = relationship(
        "User", 
        foreign_keys=[user_id], 
        back_populates="user_roles"
    )
    role = relationship(
        "Role", 
        foreign_keys=[role_id], 
        back_populates="user_roles"
    )
    assigner = relationship(
        "User", 
        foreign_keys=[assigned_by], 
        back_populates="assigned_user_roles"
    )
    
    def __init__(self, **kwargs):
        """
        构造方法
        
        Args:
            **kwargs: 字段值的关键字参数
        """
        # 设置分配时间
        if 'assigned_at' not in kwargs:
            kwargs['assigned_at'] = datetime.utcnow()
        
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
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取关联用户的基本信息
        
        Returns:
            Dict[str, Any]: 用户基本信息
        """
        if self.user:
            return {
                'user_id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'user_status': self.user.status
            }
        return {}
    
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
    
    def get_assigner_info(self) -> Dict[str, Any]:
        """
        获取分配人的基本信息
        
        Returns:
            Dict[str, Any]: 分配人基本信息
        """
        if self.assigner:
            return {
                'assigner_id': self.assigner.id,
                'assigner_username': self.assigner.username,
                'assigner_email': self.assigner.email
            }
        return {}
    
    def is_assigned_by_user(self, user_id: int) -> bool:
        """
        检查是否由特定用户分配
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 如果是由该用户分配返回True，否则返回False
        """
        return self.assigned_by == user_id
    
    def get_assignment_duration(self) -> Optional[int]:
        """
        获取分配持续时间（天数）
        
        Returns:
            Optional[int]: 分配持续天数，如果无法计算返回None
        """
        if self.assigned_at:
            duration = datetime.utcnow() - self.assigned_at
            return duration.days
        return None
    
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
        
        # 用户ID验证
        if not self.user_id or self.user_id <= 0:
            raise ValueError("用户ID必须是正整数")
        
        # 角色ID验证
        if not self.role_id or self.role_id <= 0:
            raise ValueError("角色ID必须是正整数")
        
        # 分配时间验证
        if not self.assigned_at:
            raise ValueError("分配时间不能为空")
        
        # 分配人ID验证（可选）
        if self.assigned_by is not None and self.assigned_by <= 0:
            raise ValueError("分配人ID必须是正整数")
        
        # 状态验证
        if self.status not in [0, 1]:
            raise ValueError("关联状态只能是0（禁用）或1（启用）")
        
        # 业务逻辑验证：用户不能给自己分配角色（如果有分配人）
        if self.assigned_by is not None and self.assigned_by == self.user_id:
            raise ValueError("用户不能给自己分配角色")
        
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
        fields = ['user_id', 'role_id', 'assigned_at', 'assigned_by', 'status', 'created_at', 'updated_at']
        
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
            'assignment_duration_days': self.get_assignment_duration(),
            'user_info': self.get_user_info(),
            'role_info': self.get_role_info(),
            'assigner_info': self.get_assigner_info()
        })
        return base_dict
    
    def is_new(self) -> bool:
        """
        检查是否为新创建的对象（重写父类方法）
        
        Returns:
            bool: 如果是新对象返回True，否则返回False
        """
        # 对于复合主键，检查是否已经持久化到数据库
        return not (self.user_id and self.role_id and self.created_at)
    
    def __eq__(self, other) -> bool:
        """
        相等性比较
        
        Args:
            other: 要比较的对象
            
        Returns:
            bool: 如果相等返回True，否则返回False
        """
        if not isinstance(other, UserRole):
            return False
        
        return (self.user_id == other.user_id and 
                self.role_id == other.role_id)
    
    def __hash__(self) -> int:
        """
        哈希值计算
        
        Returns:
            int: 对象的哈希值
        """
        return hash((self.__class__.__name__, self.user_id, self.role_id))
    
    def __str__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 对象的字符串表示
        """
        return (f"UserRole(user_id={self.user_id}, role_id={self.role_id}, "
                f"assigned_at='{self.assigned_at}', assigned_by={self.assigned_by}, "
                f"status={self.status})")
    
    def __repr__(self) -> str:
        """
        开发者表示
        
        Returns:
            str: 对象的开发者表示
        """
        return self.__str__()
