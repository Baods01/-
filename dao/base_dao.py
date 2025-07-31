"""
RBAC系统基础DAO模块

本模块定义了基础DAO抽象类，提供通用的数据访问接口和数据库操作功能。

Classes:
    BaseDao: 基础DAO抽象类

Author: AI Assistant
Created: 2025-07-19
"""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, desc, asc

from models.base_model import BaseModel, db_config

# 泛型类型变量
T = TypeVar('T', bound=BaseModel)


class DatabaseError(Exception):
    """数据库操作异常"""
    pass


class ValidationError(Exception):
    """数据验证异常"""
    pass


class NotFoundError(Exception):
    """数据不存在异常"""
    pass


class BaseDao(Generic[T], ABC):
    """
    基础DAO抽象类
    
    提供通用的数据访问接口，包括标准CRUD操作、批量操作、事务支持等。
    所有具体的DAO类都应该继承此类并实现抽象方法。
    
    Type Parameters:
        T: 模型类型，必须继承自BaseModel
    
    Attributes:
        model_class: 对应的模型类
        session: 数据库会话
        logger: 日志记录器
    
    Methods:
        create: 创建单个记录
        find_by_id: 根据ID查询
        find_all: 查询所有记录
        update: 更新记录
        delete_by_id: 删除记录
        batch_create: 批量创建
        batch_update: 批量更新
        batch_delete: 批量删除
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化DAO
        
        Args:
            session (Session, optional): 数据库会话，如果不提供则使用默认会话
        """
        self.session = session or db_config.get_session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_class = self._get_model_class()
    
    @abstractmethod
    def _get_model_class(self) -> type:
        """
        获取模型类
        
        子类必须实现此方法来指定对应的模型类
        
        Returns:
            type: 模型类
        """
        pass
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        Yields:
            Session: 数据库会话
            
        Example:
            >>> with dao.transaction():
            ...     dao.create(user)
            ...     dao.create(role)
        """
        try:
            yield self.session
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"事务回滚: {str(e)}")
            raise
    
    def create(self, entity: T) -> T:
        """
        创建单个记录
        
        Args:
            entity (T): 要创建的实体对象
            
        Returns:
            T: 创建后的实体对象（包含生成的ID）
            
        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        try:
            # 数据验证
            if not entity.validate():
                raise ValidationError("实体数据验证失败")
            
            # 添加到会话
            self.session.add(entity)
            self.session.flush()  # 获取生成的ID
            
            self.logger.info(f"创建{self.model_class.__name__}成功: {entity}")
            return entity
            
        except ValidationError:
            raise
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"数据完整性错误: {str(e)}")
            raise DatabaseError(f"数据完整性错误: {str(e)}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"创建{self.model_class.__name__}失败: {str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def find_by_id(self, entity_id: int) -> Optional[T]:
        """
        根据ID查询记录
        
        Args:
            entity_id (int): 实体ID
            
        Returns:
            Optional[T]: 找到的实体对象，如果不存在则返回None
            
        Raises:
            ValueError: ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if entity_id is None or entity_id <= 0:
                raise ValueError("实体ID必须是正整数")
            
            entity = self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first()
            
            return entity
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询{self.model_class.__name__}失败: entity_id={entity_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        查询所有记录
        
        Args:
            limit (int, optional): 限制返回记录数
            offset (int, optional): 偏移量
            
        Returns:
            List[T]: 实体对象列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            query = self.session.query(self.model_class)
            
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            return query.all()
            
        except SQLAlchemyError as e:
            self.logger.error(f"查询所有{self.model_class.__name__}失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def update(self, entity: T) -> T:
        """
        更新记录
        
        Args:
            entity (T): 要更新的实体对象
            
        Returns:
            T: 更新后的实体对象
            
        Raises:
            ValidationError: 数据验证失败
            NotFoundError: 记录不存在
            DatabaseError: 数据库操作失败
        """
        try:
            # 数据验证
            if not entity.validate():
                raise ValidationError("实体数据验证失败")
            
            # 检查记录是否存在
            if hasattr(entity, 'id') and entity.id:
                existing = self.find_by_id(entity.id)
                if not existing:
                    raise NotFoundError(f"{self.model_class.__name__} ID {entity.id} 不存在")
            
            # 更新时间戳
            if hasattr(entity, 'update_timestamp'):
                entity.update_timestamp()
            
            # 合并到会话
            merged_entity = self.session.merge(entity)
            self.session.flush()
            
            self.logger.info(f"更新{self.model_class.__name__}成功: {merged_entity}")
            return merged_entity
            
        except (ValidationError, NotFoundError):
            raise
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"数据完整性错误: {str(e)}")
            raise DatabaseError(f"数据完整性错误: {str(e)}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"更新{self.model_class.__name__}失败: {str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def delete_by_id(self, entity_id: int) -> bool:
        """
        根据ID删除记录
        
        Args:
            entity_id (int): 实体ID
            
        Returns:
            bool: 删除成功返回True，记录不存在返回False
            
        Raises:
            ValueError: ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if entity_id is None or entity_id <= 0:
                raise ValueError("实体ID必须是正整数")
            
            # 查找记录
            entity = self.find_by_id(entity_id)
            if not entity:
                return False
            
            # 删除记录
            self.session.delete(entity)
            self.session.flush()
            
            self.logger.info(f"删除{self.model_class.__name__}成功: ID={entity_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"删除{self.model_class.__name__}失败: entity_id={entity_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def batch_create(self, entities: List[T]) -> List[T]:
        """
        批量创建记录
        
        Args:
            entities (List[T]): 要创建的实体对象列表
            
        Returns:
            List[T]: 创建后的实体对象列表
            
        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        try:
            if not entities:
                return []
            
            # 批量验证
            for entity in entities:
                if not entity.validate():
                    raise ValidationError(f"实体数据验证失败: {entity}")
            
            # 批量添加
            self.session.add_all(entities)
            self.session.flush()
            
            self.logger.info(f"批量创建{self.model_class.__name__}成功: {len(entities)}条记录")
            return entities
            
        except ValidationError:
            raise
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"批量创建数据完整性错误: {str(e)}")
            raise DatabaseError(f"数据完整性错误: {str(e)}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"批量创建{self.model_class.__name__}失败: {str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def batch_update(self, entities: List[T]) -> List[T]:
        """
        批量更新记录
        
        Args:
            entities (List[T]): 要更新的实体对象列表
            
        Returns:
            List[T]: 更新后的实体对象列表
            
        Raises:
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        try:
            if not entities:
                return []
            
            updated_entities = []
            for entity in entities:
                updated_entity = self.update(entity)
                updated_entities.append(updated_entity)
            
            self.logger.info(f"批量更新{self.model_class.__name__}成功: {len(updated_entities)}条记录")
            return updated_entities
            
        except (ValidationError, NotFoundError, DatabaseError):
            raise
    
    def batch_delete(self, entity_ids: List[int]) -> int:
        """
        批量删除记录
        
        Args:
            entity_ids (List[int]): 要删除的实体ID列表
            
        Returns:
            int: 实际删除的记录数
            
        Raises:
            ValueError: ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not entity_ids:
                return 0
            
            # 验证ID
            for entity_id in entity_ids:
                if entity_id is None or entity_id <= 0:
                    raise ValueError(f"实体ID必须是正整数: {entity_id}")
            
            # 批量删除
            deleted_count = self.session.query(self.model_class).filter(
                self.model_class.id.in_(entity_ids)
            ).delete(synchronize_session=False)
            
            self.session.flush()
            
            self.logger.info(f"批量删除{self.model_class.__name__}成功: {deleted_count}条记录")
            return deleted_count
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"批量删除{self.model_class.__name__}失败: {str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def count(self, **filters) -> int:
        """
        统计记录数
        
        Args:
            **filters: 过滤条件
            
        Returns:
            int: 记录数
        """
        try:
            query = self.session.query(self.model_class)
            
            # 应用过滤条件
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.filter(getattr(self.model_class, field) == value)
            
            return query.count()
            
        except SQLAlchemyError as e:
            self.logger.error(f"统计{self.model_class.__name__}记录数失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def exists(self, entity_id: int) -> bool:
        """
        检查记录是否存在
        
        Args:
            entity_id (int): 实体ID
            
        Returns:
            bool: 存在返回True，否则返回False
        """
        try:
            if entity_id is None or entity_id <= 0:
                return False
            
            return self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first() is not None
            
        except SQLAlchemyError as e:
            self.logger.error(f"检查{self.model_class.__name__}存在性失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def close(self):
        """关闭数据库会话"""
        if self.session:
            self.session.close()
