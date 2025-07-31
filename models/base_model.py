"""
RBAC系统基础模型模块

本模块定义了所有ORM模型类的基础类，提供通用的字段、方法和功能。

Classes:
    BaseModel: 基础模型抽象类

Author: AI Assistant
Created: 2025-07-19
"""

from datetime import datetime
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from sqlalchemy import Column, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 创建基础模型类
Base = declarative_base()


class BaseModelMeta(type(Base), type(ABC)):
    """解决元类冲突的元类"""
    pass


class BaseModel(Base, ABC, metaclass=BaseModelMeta):
    """
    基础模型抽象类
    
    为所有实体模型提供通用的字段和方法，包括主键、时间戳字段、
    序列化方法等基础功能。
    
    Attributes:
        id (int): 主键，自增整数
        created_at (datetime): 创建时间，自动设置
        updated_at (datetime): 更新时间，自动维护
    
    Methods:
        to_dict(): 转换为字典格式
        from_dict(): 从字典创建实例
        validate(): 数据验证
        __str__(): 字符串表示
        __repr__(): 开发者表示
    """
    
    __abstract__ = True  # 标记为抽象类，不会创建对应的数据库表
    __allow_unmapped__ = True  # 允许传统注解，兼容SQLAlchemy 2.0
    
    # 通用字段定义
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='创建时间'
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment='更新时间'
    )
    
    def __init__(self, **kwargs):
        """
        构造方法
        
        Args:
            **kwargs: 字段值的关键字参数
        """
        # 设置字段值
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # 设置时间戳
        now = datetime.utcnow()
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = now
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            self.updated_at = now
    
    def to_dict(self, exclude_fields: Optional[list] = None) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Args:
            exclude_fields (list, optional): 要排除的字段列表
            
        Returns:
            Dict[str, Any]: 字典格式的数据
            
        Example:
            >>> user = User(username="admin", email="admin@example.com")
            >>> user_dict = user.to_dict(exclude_fields=['password_hash'])
        """
        exclude_fields = exclude_fields or []
        result = {}
        
        # 获取所有列
        for column in self.__table__.columns:
            field_name = column.name
            if field_name not in exclude_fields:
                value = getattr(self, field_name)
                # 处理datetime类型
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                else:
                    result[field_name] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        从字典创建实例
        
        Args:
            data (Dict[str, Any]): 字典格式的数据
            
        Returns:
            BaseModel: 创建的模型实例
            
        Raises:
            ValueError: 当数据格式不正确时
            
        Example:
            >>> data = {"username": "admin", "email": "admin@example.com"}
            >>> user = User.from_dict(data)
        """
        try:
            # 过滤掉不存在的字段
            filtered_data = {}
            for key, value in data.items():
                if hasattr(cls, key):
                    # 处理datetime字符串
                    if key in ['created_at', 'updated_at'] and isinstance(value, str):
                        try:
                            filtered_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            # 如果解析失败，跳过该字段，使用默认值
                            continue
                    else:
                        filtered_data[key] = value
            
            return cls(**filtered_data)
        except Exception as e:
            raise ValueError(f"无法从字典创建{cls.__name__}实例: {str(e)}") from e
    
    def validate(self) -> bool:
        """
        数据验证
        
        子类应该重写此方法来实现具体的验证逻辑
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            ValueError: 当数据验证失败时
        """
        # 基础验证：检查必填字段
        if not hasattr(self, 'id') or self.id is None:
            # 新创建的对象可以没有ID
            pass
        
        if not hasattr(self, 'created_at') or self.created_at is None:
            raise ValueError("创建时间不能为空")
        
        if not hasattr(self, 'updated_at') or self.updated_at is None:
            raise ValueError("更新时间不能为空")
        
        return True
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.utcnow()
    
    def is_new(self) -> bool:
        """
        检查是否为新创建的对象（未保存到数据库）
        
        Returns:
            bool: 如果是新对象返回True，否则返回False
        """
        return self.id is None
    
    @abstractmethod
    def __str__(self) -> str:
        """
        字符串表示
        
        子类必须实现此方法
        
        Returns:
            str: 对象的字符串表示
        """
        pass
    
    def __repr__(self) -> str:
        """
        开发者表示
        
        Returns:
            str: 对象的开发者表示
        """
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        """
        相等性比较
        
        Args:
            other: 要比较的对象
            
        Returns:
            bool: 如果相等返回True，否则返回False
        """
        if not isinstance(other, self.__class__):
            return False
        
        # 如果都有ID，比较ID
        if self.id is not None and other.id is not None:
            return self.id == other.id
        
        # 如果没有ID，比较所有字段
        return self.to_dict() == other.to_dict()
    
    def __hash__(self) -> int:
        """
        哈希值计算
        
        Returns:
            int: 对象的哈希值
        """
        if self.id is not None:
            return hash((self.__class__.__name__, self.id))
        else:
            # 对于没有ID的新对象，使用对象地址
            return hash(id(self))


# 数据库配置类
class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self, database_url: str = "sqlite:///rbac_system.db"):
        """
        初始化数据库配置
        
        Args:
            database_url (str): 数据库连接URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """创建所有表"""
        # 确保所有模型类都已导入并注册到metadata中
        # 使用绝对导入确保模型类被正确加载
        import sys
        import os

        # 添加当前目录到Python路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # 强制导入所有模型类
        from models.user import User
        from models.role import Role
        from models.permission import Permission
        from models.user_role import UserRole
        from models.role_permission import RolePermission

        # 打印调试信息
        print(f"  ✓ 已注册 {len(Base.metadata.tables)} 个表到metadata")

        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'engine') and self.engine:
            self.engine.dispose()
            print("  ✓ 数据库引擎已关闭")

    def clear_metadata(self):
        """清理metadata缓存"""
        # 不要清理metadata，因为这会导致模型类无法重新注册
        # 只是打印信息，实际不执行清理
        print("  ✓ 保留metadata缓存（避免重新注册问题）")


# 全局数据库配置实例
db_config = DatabaseConfig()
