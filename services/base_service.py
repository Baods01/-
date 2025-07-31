"""
RBAC权限系统 - 基础服务类

本模块定义了所有业务服务的基础抽象类，提供统一的数据库会话管理、
事务处理、异常处理和日志记录功能。

Classes:
    BaseService: 基础服务抽象类

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional, Any, Dict, List, TypeVar, Generic, Type
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError

# 导入现有组件
from models.base_model import BaseModel, db_config
from dao.base_dao import DatabaseError, ValidationError, NotFoundError
from services.exceptions import (
    BusinessLogicError,
    AuthenticationError,
    AuthorizationError,
    DataValidationError,
    ResourceNotFoundError,
    DuplicateResourceError
)
from config.test_config import TestConfig

# 泛型类型变量
T = TypeVar('T', bound=BaseModel)


class BaseService(ABC, Generic[T]):
    """
    基础服务抽象类
    
    为所有业务服务提供统一的基础功能，包括数据库会话管理、
    事务处理、异常处理和日志记录。
    
    Features:
        - 数据库会话生命周期管理
        - 自动事务提交和回滚
        - 统一异常处理和转换
        - 业务操作日志记录
        - 性能监控和统计
        - 上下文管理器支持
    
    Type Parameters:
        T: 主要操作的模型类型，必须继承自BaseModel
    
    Attributes:
        session (Session): 数据库会话
        logger (Logger): 日志记录器
        config (TestConfig): 配置对象
        _transaction_depth (int): 事务嵌套深度
        _performance_stats (Dict): 性能统计信息
    
    Example:
        >>> class UserService(BaseService[User]):
        ...     def get_model_class(self) -> Type[User]:
        ...         return User
        ...     
        ...     def create_user(self, username: str, email: str) -> User:
        ...         with self.transaction():
        ...             user = User(username=username, email=email)
        ...             return self.save_entity(user)
    """
    
    def __init__(self, session: Optional[Session] = None, config: Optional[TestConfig] = None):
        """
        初始化基础服务
        
        Args:
            session (Session, optional): 数据库会话，如果不提供则创建新会话
            config (TestConfig, optional): 配置对象，如果不提供则使用默认配置
        """
        # 数据库会话管理
        self.session = session or db_config.get_session()
        self._session_owned = session is None  # 标记会话是否由本服务创建
        
        # 配置和日志
        self.config = config or TestConfig()
        self.logger = self._setup_logger()
        
        # 事务管理
        self._transaction_depth = 0
        self._in_transaction = False
        
        # 性能统计
        self._performance_stats = {
            'operations_count': 0,
            'total_time': 0.0,
            'error_count': 0,
            'last_operation_time': None
        }
        
        # 获取模型类
        self.model_class = self.get_model_class()
        
        self.logger.debug(f"{self.__class__.__name__} 初始化完成")
    
    @abstractmethod
    def get_model_class(self) -> Type[T]:
        """
        获取服务对应的主要模型类
        
        子类必须实现此方法来指定主要操作的模型类型
        
        Returns:
            Type[T]: 模型类
        """
        pass
    
    def _setup_logger(self) -> logging.Logger:
        """
        设置日志记录器
        
        Returns:
            Logger: 配置好的日志记录器
        """
        logger = logging.getLogger(self.__class__.__name__)
        
        # 如果还没有配置处理器，则配置
        if not logger.handlers:
            # 设置日志级别
            log_level = getattr(logging, self.config.LOGGING['level'], logging.INFO)
            logger.setLevel(log_level)
            
            # 创建格式化器
            formatter = logging.Formatter(self.config.LOGGING['format'])
            
            # 控制台处理器
            if self.config.LOGGING.get('console_output', True):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
            
            # 文件处理器
            if self.config.LOGGING.get('file'):
                import os
                log_dir = os.path.dirname(self.config.LOGGING['file'])
                os.makedirs(log_dir, exist_ok=True)
                
                file_handler = logging.FileHandler(self.config.LOGGING['file'])
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        return logger
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        支持嵌套事务，自动处理提交和回滚。
        
        Yields:
            Session: 数据库会话
            
        Raises:
            BusinessLogicError: 业务逻辑错误
            DatabaseError: 数据库操作错误
            
        Example:
            >>> with service.transaction():
            ...     user = service.create_user("admin", "admin@example.com")
            ...     role = service.assign_role(user.id, "admin")
        """
        start_time = time.time()
        self._transaction_depth += 1
        
        try:
            # 只在最外层事务开始时记录
            if self._transaction_depth == 1:
                self._in_transaction = True
                self.logger.debug("开始事务")
            
            yield self.session
            
            # 只在最外层事务提交
            if self._transaction_depth == 1:
                self.session.commit()
                self.logger.debug("事务提交成功")
                
        except Exception as e:
            # 任何异常都回滚到最外层
            if self._in_transaction:
                self.session.rollback()
                self.logger.error(f"事务回滚: {str(e)}")
                self._in_transaction = False
            
            # 转换异常类型
            converted_exception = self._convert_exception(e)
            self._performance_stats['error_count'] += 1
            
            raise converted_exception
            
        finally:
            self._transaction_depth -= 1
            if self._transaction_depth == 0:
                self._in_transaction = False
            
            # 记录性能统计
            operation_time = time.time() - start_time
            self._performance_stats['total_time'] += operation_time
            self._performance_stats['operations_count'] += 1
            self._performance_stats['last_operation_time'] = datetime.now(timezone.utc)
    
    def _convert_exception(self, exception: Exception) -> BusinessLogicError:
        """
        将数据库异常转换为业务异常
        
        Args:
            exception (Exception): 原始异常
            
        Returns:
            BusinessLogicError: 转换后的业务异常
        """
        if isinstance(exception, BusinessLogicError):
            return exception
        
        if isinstance(exception, ValidationError):
            return exception
        
        if isinstance(exception, NotFoundError):
            return ResourceNotFoundError(
                resource_type=self.model_class.__name__,
                details={'original_error': str(exception)}
            )
        
        if isinstance(exception, IntegrityError):
            # 解析完整性约束错误
            error_msg = str(exception)
            if 'UNIQUE constraint failed' in error_msg or 'Duplicate entry' in error_msg:
                return DuplicateResourceError(
                    resource_type=self.model_class.__name__,
                    field_name="unknown",
                    field_value="unknown",
                    details={'original_error': error_msg}
                )
            else:
                return BusinessLogicError(
                    message=f"数据完整性错误: {error_msg}",
                    error_code="INTEGRITY_ERROR",
                    details={'original_error': error_msg}
                )
        
        if isinstance(exception, OperationalError):
            return BusinessLogicError(
                message=f"数据库操作错误: {str(exception)}",
                error_code="DATABASE_OPERATIONAL_ERROR",
                details={'original_error': str(exception)}
            )
        
        if isinstance(exception, SQLAlchemyError):
            return BusinessLogicError(
                message=f"数据库错误: {str(exception)}",
                error_code="DATABASE_ERROR",
                details={'original_error': str(exception)}
            )
        
        # 其他未知异常
        return BusinessLogicError(
            message=f"未知错误: {str(exception)}",
            error_code="UNKNOWN_ERROR",
            details={'original_error': str(exception), 'exception_type': type(exception).__name__}
        )
    
    def save_entity(self, entity: T) -> T:
        """
        保存实体对象
        
        Args:
            entity (T): 要保存的实体对象
            
        Returns:
            T: 保存后的实体对象
            
        Raises:
            ValidationError: 数据验证失败
            BusinessLogicError: 业务逻辑错误
        """
        try:
            # 数据验证
            if not entity.validate():
                raise DataValidationError(f"{self.model_class.__name__} 数据验证失败")
            
            # 保存到数据库
            self.session.add(entity)
            self.session.flush()  # 获取生成的ID
            
            self.logger.info(f"保存 {self.model_class.__name__} 成功: ID={entity.id}")
            return entity

        except Exception as e:
            raise self._convert_exception(e)

    def delete_by_id(self, entity_id: int) -> bool:
        """
        根据ID删除实体

        Args:
            entity_id (int): 实体ID

        Returns:
            bool: 删除成功返回True

        Raises:
            ResourceNotFoundError: 实体不存在
            BusinessLogicError: 其他业务逻辑错误
        """
        try:
            entity = self.get_by_id(entity_id)
            self.session.delete(entity)
            self.session.flush()

            self.logger.info(f"删除 {self.model_class.__name__} 成功: ID={entity_id}")
            return True

        except Exception as e:
            raise self._convert_exception(e)

    def update_entity(self, entity: T, **kwargs) -> T:
        """
        更新实体对象

        Args:
            entity (T): 要更新的实体对象
            **kwargs: 要更新的字段

        Returns:
            T: 更新后的实体对象

        Raises:
            ValidationError: 数据验证失败
            BusinessLogicError: 业务逻辑错误
        """
        try:
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            # 数据验证
            if not entity.validate():
                raise DataValidationError(f"{self.model_class.__name__} 数据验证失败")

            # 更新到数据库
            self.session.flush()

            self.logger.info(f"更新 {self.model_class.__name__} 成功: ID={entity.id}")
            return entity

        except Exception as e:
            raise self._convert_exception(e)

    def count_all(self, **filters) -> int:
        """
        统计实体数量

        Args:
            **filters: 过滤条件

        Returns:
            int: 实体数量

        Raises:
            BusinessLogicError: 业务逻辑错误
        """
        try:
            query = self.session.query(self.model_class)

            # 应用过滤条件
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)

            return query.count()

        except Exception as e:
            raise self._convert_exception(e)

    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None, **filters) -> List[T]:
        """
        查找所有实体

        Args:
            limit (int, optional): 限制数量
            offset (int, optional): 偏移量
            **filters: 过滤条件

        Returns:
            List[T]: 实体列表

        Raises:
            BusinessLogicError: 业务逻辑错误
        """
        try:
            query = self.session.query(self.model_class)

            # 应用过滤条件
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)

            # 应用分页
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return query.all()

        except Exception as e:
            raise self._convert_exception(e)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息

        Returns:
            Dict[str, Any]: 性能统计信息
        """
        stats = self._performance_stats.copy()

        # 计算平均操作时间
        if stats['operations_count'] > 0:
            stats['average_operation_time'] = stats['total_time'] / stats['operations_count']
        else:
            stats['average_operation_time'] = 0.0

        # 计算错误率
        if stats['operations_count'] > 0:
            stats['error_rate'] = stats['error_count'] / stats['operations_count']
        else:
            stats['error_rate'] = 0.0

        return stats

    def reset_performance_stats(self):
        """重置性能统计信息"""
        self._performance_stats = {
            'operations_count': 0,
            'total_time': 0.0,
            'error_count': 0,
            'last_operation_time': None
        }
        self.logger.debug("性能统计信息已重置")

    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """
        记录业务操作日志

        Args:
            operation (str): 操作名称
            details (Dict[str, Any], optional): 操作详情
        """
        log_message = f"业务操作: {operation}"
        if details:
            log_message += f" - 详情: {details}"

        self.logger.info(log_message)

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        try:
            if exc_type is None:
                # 没有异常，提交事务
                if self._in_transaction:
                    self.session.commit()
                    self.logger.debug("上下文管理器: 事务提交成功")
            else:
                # 有异常，回滚事务
                if self._in_transaction:
                    self.session.rollback()
                    self.logger.error(f"上下文管理器: 事务回滚 - {exc_val}")
        finally:
            # 如果会话是由本服务创建的，则关闭它
            if self._session_owned and self.session:
                self.session.close()
                self.logger.debug("上下文管理器: 数据库会话已关闭")

        # 不抑制异常
        return False

    def close(self):
        """
        关闭服务，清理资源
        """
        try:
            if self._session_owned and self.session:
                self.session.close()
                self.logger.debug(f"{self.__class__.__name__} 服务已关闭")
        except Exception as e:
            self.logger.error(f"关闭服务时发生错误: {str(e)}")

    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.close()
        except:
            pass  # 忽略析构函数中的异常
    
    def find_by_id(self, entity_id: int) -> Optional[T]:
        """
        根据ID查找实体
        
        Args:
            entity_id (int): 实体ID
            
        Returns:
            Optional[T]: 找到的实体对象，如果不存在则返回None
            
        Raises:
            BusinessLogicError: 业务逻辑错误
        """
        try:
            if entity_id is None or entity_id <= 0:
                raise DataValidationError("实体ID必须是正整数")
            
            entity = self.session.query(self.model_class).filter(
                self.model_class.id == entity_id
            ).first()
            
            return entity
            
        except Exception as e:
            raise self._convert_exception(e)
    
    def get_by_id(self, entity_id: int) -> T:
        """
        根据ID获取实体（如果不存在则抛出异常）
        
        Args:
            entity_id (int): 实体ID
            
        Returns:
            T: 找到的实体对象
            
        Raises:
            ResourceNotFoundError: 实体不存在
            BusinessLogicError: 其他业务逻辑错误
        """
        entity = self.find_by_id(entity_id)
        if entity is None:
            raise ResourceNotFoundError(
                resource_type=self.model_class.__name__,
                resource_id=str(entity_id)
            )
        return entity
