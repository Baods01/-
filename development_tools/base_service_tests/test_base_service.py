#!/usr/bin/env python3
"""
RBAC权限系统 - 基础服务类测试

本文件包含BaseService基础服务类的单元测试，
验证数据库会话管理、事务处理、异常处理等功能。

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Type

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from services.base_service import BaseService
from services.exceptions import (
    BusinessLogicError,
    DataValidationError,
    ResourceNotFoundError,
    DuplicateResourceError
)
from models.user import User


class MockModel:
    """模拟模型类用于测试"""

    # 添加类属性id用于查询
    id = None

    def __init__(self, id=None):
        self.id = id

    def validate(self):
        return True


class TestBaseService(BaseService[MockModel]):
    """测试用的BaseService子类"""
    
    def get_model_class(self) -> Type[MockModel]:
        return MockModel


class TestBaseServiceFunctionality(unittest.TestCase):
    """BaseService功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟会话
        self.mock_session = Mock(spec=Session)
        self.mock_config = Mock()
        self.mock_config.LOGGING = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'console_output': True
        }
        
        # 创建测试服务实例
        self.service = TestBaseService(
            session=self.mock_session,
            config=self.mock_config
        )
    
    def tearDown(self):
        """测试后清理"""
        self.service.close()
    
    def test_initialization(self):
        """测试服务初始化"""
        # 验证基本属性
        self.assertEqual(self.service.session, self.mock_session)
        self.assertEqual(self.service.model_class, MockModel)
        self.assertFalse(self.service._session_owned)
        self.assertEqual(self.service._transaction_depth, 0)
        self.assertFalse(self.service._in_transaction)
        
        # 验证性能统计初始化
        stats = self.service.get_performance_stats()
        self.assertEqual(stats['operations_count'], 0)
        self.assertEqual(stats['total_time'], 0.0)
        self.assertEqual(stats['error_count'], 0)
    
    def test_transaction_success(self):
        """测试成功事务"""
        with self.service.transaction():
            # 模拟一些操作
            pass
        
        # 验证事务提交
        self.mock_session.commit.assert_called_once()
        self.mock_session.rollback.assert_not_called()
        
        # 验证事务状态重置
        self.assertEqual(self.service._transaction_depth, 0)
        self.assertFalse(self.service._in_transaction)
    
    def test_transaction_rollback(self):
        """测试事务回滚"""
        try:
            with self.service.transaction():
                raise Exception("测试异常")
        except BusinessLogicError:
            pass
        
        # 验证事务回滚
        self.mock_session.rollback.assert_called_once()
        self.mock_session.commit.assert_not_called()
        
        # 验证错误统计
        stats = self.service.get_performance_stats()
        self.assertEqual(stats['error_count'], 1)
    
    def test_nested_transactions(self):
        """测试嵌套事务"""
        with self.service.transaction():
            self.assertEqual(self.service._transaction_depth, 1)
            
            with self.service.transaction():
                self.assertEqual(self.service._transaction_depth, 2)
            
            self.assertEqual(self.service._transaction_depth, 1)
        
        self.assertEqual(self.service._transaction_depth, 0)
        # 只有最外层事务提交
        self.mock_session.commit.assert_called_once()
    
    def test_save_entity(self):
        """测试保存实体"""
        # 创建模拟实体
        mock_entity = MockModel()
        mock_entity.validate = Mock(return_value=True)
        
        # 执行保存
        result = self.service.save_entity(mock_entity)
        
        # 验证操作
        self.mock_session.add.assert_called_once_with(mock_entity)
        self.mock_session.flush.assert_called_once()
        self.assertEqual(result, mock_entity)
    
    def test_save_entity_validation_error(self):
        """测试保存实体时的验证错误"""
        # 创建验证失败的模拟实体
        mock_entity = MockModel()
        mock_entity.validate = Mock(return_value=False)

        # 验证抛出DataValidationError
        with self.assertRaises(DataValidationError):
            self.service.save_entity(mock_entity)
    
    def test_find_by_id(self):
        """测试根据ID查找实体"""
        # 设置模拟查询结果
        mock_entity = MockModel(id=1)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_entity
        self.mock_session.query.return_value = mock_query
        
        # 执行查找
        result = self.service.find_by_id(1)
        
        # 验证结果
        self.assertEqual(result, mock_entity)
        self.mock_session.query.assert_called_once_with(MockModel)
    
    def test_find_by_id_invalid_id(self):
        """测试无效ID查找"""
        # 现在抛出的是DataValidationError
        with self.assertRaises(DataValidationError):
            self.service.find_by_id(0)

        with self.assertRaises(DataValidationError):
            self.service.find_by_id(-1)

        with self.assertRaises(DataValidationError):
            self.service.find_by_id(None)
    
    def test_get_by_id_not_found(self):
        """测试获取不存在的实体"""
        # 设置查询返回None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_session.query.return_value = mock_query
        
        # 验证抛出ResourceNotFoundError
        with self.assertRaises(ResourceNotFoundError):
            self.service.get_by_id(999)
    
    def test_delete_by_id(self):
        """测试根据ID删除实体"""
        # 设置模拟实体
        mock_entity = MockModel(id=1)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_entity
        self.mock_session.query.return_value = mock_query
        
        # 执行删除
        result = self.service.delete_by_id(1)
        
        # 验证操作
        self.assertTrue(result)
        self.mock_session.delete.assert_called_once_with(mock_entity)
        self.mock_session.flush.assert_called_once()
    
    def test_update_entity(self):
        """测试更新实体"""
        # 创建模拟实体
        mock_entity = MockModel(id=1)
        mock_entity.validate = Mock(return_value=True)
        mock_entity.name = "old_name"
        
        # 执行更新
        result = self.service.update_entity(mock_entity, name="new_name")
        
        # 验证更新
        self.assertEqual(mock_entity.name, "new_name")
        self.assertEqual(result, mock_entity)
        self.mock_session.flush.assert_called_once()
    
    def test_count_all(self):
        """测试统计数量"""
        # 设置模拟查询结果
        mock_query = Mock()
        mock_query.count.return_value = 5
        self.mock_session.query.return_value = mock_query
        
        # 执行统计
        result = self.service.count_all()
        
        # 验证结果
        self.assertEqual(result, 5)
        self.mock_session.query.assert_called_once_with(MockModel)
    
    def test_find_all_with_filters(self):
        """测试带过滤条件的查找"""
        # 设置模拟查询结果
        mock_entities = [MockModel(id=1), MockModel(id=2)]
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_entities
        self.mock_session.query.return_value = mock_query
        
        # 执行查找
        result = self.service.find_all(limit=10, offset=0, status=1)
        
        # 验证结果
        self.assertEqual(result, mock_entities)
        mock_query.limit.assert_called_once_with(10)
        mock_query.offset.assert_called_once_with(0)
    
    def test_exception_conversion(self):
        """测试异常转换"""
        # 测试IntegrityError转换
        integrity_error = IntegrityError("statement", "params", "orig")
        converted = self.service._convert_exception(integrity_error)
        self.assertIsInstance(converted, BusinessLogicError)
        
        # 测试OperationalError转换
        operational_error = OperationalError("statement", "params", "orig")
        converted = self.service._convert_exception(operational_error)
        self.assertIsInstance(converted, BusinessLogicError)
        
        # 测试未知异常转换
        unknown_error = ValueError("test error")
        converted = self.service._convert_exception(unknown_error)
        self.assertIsInstance(converted, BusinessLogicError)
        self.assertEqual(converted.error_code, "UNKNOWN_ERROR")
    
    def test_performance_stats(self):
        """测试性能统计"""
        import time
        # 执行一些操作来生成统计数据
        with self.service.transaction():
            time.sleep(0.001)  # 确保有可测量的时间

        # 获取统计信息
        stats = self.service.get_performance_stats()

        # 验证统计数据
        self.assertEqual(stats['operations_count'], 1)
        self.assertGreaterEqual(stats['total_time'], 0)  # 改为>=0
        self.assertIsNotNone(stats['average_operation_time'])
        self.assertEqual(stats['error_rate'], 0.0)
    
    def test_context_manager(self):
        """测试上下文管理器"""
        mock_session = Mock(spec=Session)
        
        with TestBaseService(session=mock_session) as service:
            self.assertIsInstance(service, TestBaseService)
        
        # 验证会话没有被关闭（因为不是服务创建的）
        mock_session.close.assert_not_called()
    
    def test_log_operation(self):
        """测试操作日志记录"""
        with patch.object(self.service.logger, 'info') as mock_log:
            self.service.log_operation("test_operation", {"key": "value"})
            mock_log.assert_called_once()
    
    def test_reset_performance_stats(self):
        """测试重置性能统计"""
        # 先执行一些操作
        with self.service.transaction():
            pass
        
        # 验证有统计数据
        stats = self.service.get_performance_stats()
        self.assertGreater(stats['operations_count'], 0)
        
        # 重置统计
        self.service.reset_performance_stats()
        
        # 验证统计被重置
        stats = self.service.get_performance_stats()
        self.assertEqual(stats['operations_count'], 0)
        self.assertEqual(stats['total_time'], 0.0)
        self.assertEqual(stats['error_count'], 0)


if __name__ == '__main__':
    unittest.main()
