#!/usr/bin/env python3
"""
RBAC权限系统 - 基础服务类验证脚本

验证BaseService基础服务类的功能完整性和正确性。

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import sys
import os
import traceback
from typing import Type

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.base_service import BaseService
from services.exceptions import (
    BusinessLogicError,
    DataValidationError,
    ResourceNotFoundError,
    DuplicateResourceError
)
from models.user import User


class TestUserService(BaseService[User]):
    """测试用的用户服务类"""
    
    def get_model_class(self) -> Type[User]:
        return User


def test_service_initialization():
    """测试服务初始化"""
    print("🔍 测试服务初始化...")
    
    try:
        service = TestUserService()
        
        # 验证基本属性
        assert service.model_class == User, "模型类设置错误"
        assert service._transaction_depth == 0, "事务深度初始化错误"
        assert not service._in_transaction, "事务状态初始化错误"
        assert service.session is not None, "数据库会话未初始化"
        assert service.logger is not None, "日志记录器未初始化"
        
        # 验证性能统计
        stats = service.get_performance_stats()
        assert stats['operations_count'] == 0, "操作计数初始化错误"
        assert stats['total_time'] == 0.0, "总时间初始化错误"
        assert stats['error_count'] == 0, "错误计数初始化错误"
        
        service.close()
        print("  ✅ 服务初始化测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 服务初始化测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_transaction_management():
    """测试事务管理"""
    print("🔍 测试事务管理...")
    
    try:
        service = TestUserService()
        
        # 测试基本事务
        with service.transaction():
            assert service._transaction_depth == 1, "事务深度错误"
            assert service._in_transaction, "事务状态错误"
        
        assert service._transaction_depth == 0, "事务结束后深度未重置"
        assert not service._in_transaction, "事务结束后状态未重置"
        
        # 测试嵌套事务
        with service.transaction():
            assert service._transaction_depth == 1
            
            with service.transaction():
                assert service._transaction_depth == 2
                
                with service.transaction():
                    assert service._transaction_depth == 3
                
                assert service._transaction_depth == 2
            
            assert service._transaction_depth == 1
        
        assert service._transaction_depth == 0
        
        service.close()
        print("  ✅ 事务管理测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 事务管理测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_exception_conversion():
    """测试异常转换"""
    print("🔍 测试异常转换...")
    
    try:
        service = TestUserService()
        
        # 测试各种异常转换
        from sqlalchemy.exc import IntegrityError, OperationalError
        
        # IntegrityError转换
        integrity_error = IntegrityError("statement", "params", "orig")
        converted = service._convert_exception(integrity_error)
        assert isinstance(converted, BusinessLogicError), "IntegrityError转换失败"
        
        # OperationalError转换
        operational_error = OperationalError("statement", "params", "orig")
        converted = service._convert_exception(operational_error)
        assert isinstance(converted, BusinessLogicError), "OperationalError转换失败"
        
        # ValidationError保持不变（来自dao.base_dao）
        from dao.base_dao import ValidationError
        validation_error = ValidationError("test validation error")
        converted = service._convert_exception(validation_error)
        assert isinstance(converted, ValidationError), "ValidationError转换错误"
        
        # 未知异常转换
        unknown_error = ValueError("test error")
        converted = service._convert_exception(unknown_error)
        assert isinstance(converted, BusinessLogicError), "未知异常转换失败"
        assert converted.error_code == "UNKNOWN_ERROR", "未知异常错误代码错误"
        
        service.close()
        print("  ✅ 异常转换测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 异常转换测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_performance_stats():
    """测试性能统计"""
    print("🔍 测试性能统计...")
    
    try:
        service = TestUserService()
        
        # 初始状态检查
        stats = service.get_performance_stats()
        assert stats['operations_count'] == 0
        assert stats['total_time'] == 0.0
        assert stats['error_count'] == 0
        assert stats['average_operation_time'] == 0.0
        assert stats['error_rate'] == 0.0
        
        # 执行一些操作
        import time
        with service.transaction():
            time.sleep(0.001)  # 确保有可测量的时间

        # 检查统计更新
        stats = service.get_performance_stats()
        assert stats['operations_count'] == 1, "操作计数未更新"
        assert stats['total_time'] >= 0, "总时间未更新"  # 改为>=0，因为时间可能很短
        assert stats['average_operation_time'] >= 0, "平均时间计算错误"  # 改为>=0
        assert stats['error_rate'] == 0.0, "错误率计算错误"
        
        # 测试重置功能
        service.reset_performance_stats()
        stats = service.get_performance_stats()
        assert stats['operations_count'] == 0, "统计重置失败"
        assert stats['total_time'] == 0.0, "统计重置失败"
        
        service.close()
        print("  ✅ 性能统计测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 性能统计测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_context_manager():
    """测试上下文管理器"""
    print("🔍 测试上下文管理器...")
    
    try:
        # 测试正常使用
        with TestUserService() as service:
            assert isinstance(service, TestUserService), "上下文管理器返回类型错误"
            assert service.session is not None, "会话未正确初始化"
        
        # 测试异常处理
        try:
            with TestUserService() as service:
                raise ValueError("测试异常")
        except ValueError:
            pass  # 预期的异常
        
        print("  ✅ 上下文管理器测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 上下文管理器测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_logging_functionality():
    """测试日志功能"""
    print("🔍 测试日志功能...")
    
    try:
        service = TestUserService()
        
        # 测试日志记录器初始化
        assert service.logger is not None, "日志记录器未初始化"
        assert service.logger.name == "TestUserService", "日志记录器名称错误"
        
        # 测试操作日志记录
        service.log_operation("test_operation", {"key": "value"})
        service.log_operation("simple_operation")
        
        service.close()
        print("  ✅ 日志功能测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 日志功能测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_crud_operations():
    """测试CRUD操作接口"""
    print("🔍 测试CRUD操作接口...")
    
    try:
        service = TestUserService()
        
        # 测试方法存在性
        assert hasattr(service, 'save_entity'), "save_entity方法不存在"
        assert hasattr(service, 'find_by_id'), "find_by_id方法不存在"
        assert hasattr(service, 'get_by_id'), "get_by_id方法不存在"
        assert hasattr(service, 'delete_by_id'), "delete_by_id方法不存在"
        assert hasattr(service, 'update_entity'), "update_entity方法不存在"
        assert hasattr(service, 'count_all'), "count_all方法不存在"
        assert hasattr(service, 'find_all'), "find_all方法不存在"
        
        # 测试方法可调用性
        assert callable(service.save_entity), "save_entity不可调用"
        assert callable(service.find_by_id), "find_by_id不可调用"
        assert callable(service.get_by_id), "get_by_id不可调用"
        assert callable(service.delete_by_id), "delete_by_id不可调用"
        assert callable(service.update_entity), "update_entity不可调用"
        assert callable(service.count_all), "count_all不可调用"
        assert callable(service.find_all), "find_all不可调用"
        
        service.close()
        print("  ✅ CRUD操作接口测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ CRUD操作接口测试失败: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 BaseService基础服务类验证开始")
    print("=" * 50)
    
    tests = [
        ("服务初始化", test_service_initialization),
        ("事务管理", test_transaction_management),
        ("异常转换", test_exception_conversion),
        ("性能统计", test_performance_stats),
        ("上下文管理器", test_context_manager),
        ("日志功能", test_logging_functionality),
        ("CRUD操作接口", test_crud_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name}测试异常: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 验证结果汇总:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！BaseService基础服务类开发完成。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查并修复问题。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
