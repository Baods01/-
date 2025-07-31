#!/usr/bin/env python3
"""
RBAC权限系统 - 用户服务验证脚本

验证UserService用户业务服务类的功能完整性和正确性。

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import sys
import os
import asyncio
import traceback
from typing import Type

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.user_service import UserService
from services.exceptions import (
    AuthenticationError,
    DataValidationError,
    DuplicateResourceError,
    ResourceNotFoundError
)
from models.user import User


def test_service_initialization():
    """测试服务初始化"""
    print("🔍 测试服务初始化...")
    
    try:
        service = UserService()
        
        # 验证基本属性
        assert service.model_class == User, "模型类设置错误"
        assert hasattr(service, 'user_dao'), "UserDao未初始化"
        assert hasattr(service, 'password_utils'), "PasswordUtils未初始化"
        assert service.session is not None, "数据库会话未初始化"
        assert service.logger is not None, "日志记录器未初始化"
        
        service.close()
        print("  ✅ 服务初始化测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 服务初始化测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_data_validation():
    """测试数据验证功能"""
    print("🔍 测试数据验证功能...")
    
    try:
        service = UserService()
        
        # 测试用户名验证
        try:
            service._validate_username("ab")  # 太短
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        try:
            service._validate_username("123user")  # 数字开头
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        # 测试有效用户名
        service._validate_username("validuser")  # 应该通过
        
        # 测试邮箱验证
        try:
            service._validate_email("invalid-email")  # 格式错误
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        # 测试有效邮箱
        service._validate_email("valid@example.com")  # 应该通过
        
        service.close()
        print("  ✅ 数据验证功能测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 数据验证功能测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_password_validation():
    """测试密码验证功能"""
    print("🔍 测试密码验证功能...")
    
    try:
        service = UserService()
        
        # 测试弱密码
        try:
            service._validate_password_strength("weak")
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        # 测试强密码（假设PasswordUtils会验证）
        # 这里只测试方法调用，不测试具体逻辑
        service.password_utils.check_password_strength = lambda x: (True, "强密码")
        service._validate_password_strength("StrongPass123!")  # 应该通过
        
        service.close()
        print("  ✅ 密码验证功能测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 密码验证功能测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def test_async_methods():
    """测试异步方法"""
    print("🔍 测试异步方法...")
    
    try:
        service = UserService()
        
        # 测试方法存在性和可调用性
        assert hasattr(service, 'create_user'), "create_user方法不存在"
        assert callable(service.create_user), "create_user不可调用"
        
        assert hasattr(service, 'authenticate_user'), "authenticate_user方法不存在"
        assert callable(service.authenticate_user), "authenticate_user不可调用"
        
        assert hasattr(service, 'change_password'), "change_password方法不存在"
        assert callable(service.change_password), "change_password不可调用"
        
        assert hasattr(service, 'get_user_permissions'), "get_user_permissions方法不存在"
        assert callable(service.get_user_permissions), "get_user_permissions不可调用"
        
        assert hasattr(service, 'enable_user'), "enable_user方法不存在"
        assert callable(service.enable_user), "enable_user不可调用"
        
        assert hasattr(service, 'disable_user'), "disable_user方法不存在"
        assert callable(service.disable_user), "disable_user不可调用"
        
        service.close()
        print("  ✅ 异步方法测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 异步方法测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_helper_methods():
    """测试辅助方法"""
    print("🔍 测试辅助方法...")
    
    try:
        service = UserService()
        
        # 测试辅助方法存在性
        assert hasattr(service, 'get_user_by_username'), "get_user_by_username方法不存在"
        assert hasattr(service, 'get_user_by_email'), "get_user_by_email方法不存在"
        assert hasattr(service, 'check_user_permission'), "check_user_permission方法不存在"
        assert hasattr(service, 'get_active_users'), "get_active_users方法不存在"
        assert hasattr(service, 'search_users'), "search_users方法不存在"
        assert hasattr(service, 'get_user_statistics'), "get_user_statistics方法不存在"
        assert hasattr(service, 'batch_create_users'), "batch_create_users方法不存在"
        
        # 测试可调用性
        assert callable(service.get_user_by_username), "get_user_by_username不可调用"
        assert callable(service.get_user_by_email), "get_user_by_email不可调用"
        assert callable(service.check_user_permission), "check_user_permission不可调用"
        assert callable(service.get_active_users), "get_active_users不可调用"
        assert callable(service.search_users), "search_users不可调用"
        assert callable(service.get_user_statistics), "get_user_statistics不可调用"
        assert callable(service.batch_create_users), "batch_create_users不可调用"
        
        service.close()
        print("  ✅ 辅助方法测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 辅助方法测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_exception_handling():
    """测试异常处理"""
    print("🔍 测试异常处理...")
    
    try:
        service = UserService()
        
        # 测试异常类导入
        from services.exceptions import (
            AuthenticationError,
            DataValidationError,
            DuplicateResourceError,
            ResourceNotFoundError
        )
        
        # 测试异常类实例化
        auth_error = AuthenticationError("测试认证异常")
        assert auth_error.error_code == "AUTH_ERROR", "认证异常错误码错误"

        validation_error = DataValidationError("测试验证异常")
        assert validation_error.error_code == "VALIDATION_ERROR", "验证异常错误码错误"

        duplicate_error = DuplicateResourceError("User", "username", "test")
        assert duplicate_error.error_code == "DUPLICATE_RESOURCE", "重复资源异常错误码错误"

        not_found_error = ResourceNotFoundError("User", "123")
        assert not_found_error.error_code == "RESOURCE_NOT_FOUND", "资源不存在异常错误码错误"
        
        service.close()
        print("  ✅ 异常处理测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 异常处理测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_base_service_integration():
    """测试BaseService集成"""
    print("🔍 测试BaseService集成...")
    
    try:
        service = UserService()
        
        # 测试继承的方法
        assert hasattr(service, 'transaction'), "transaction方法不存在"
        assert hasattr(service, 'save_entity'), "save_entity方法不存在"
        assert hasattr(service, 'find_by_id'), "find_by_id方法不存在"
        assert hasattr(service, 'get_by_id'), "get_by_id方法不存在"
        assert hasattr(service, 'delete_by_id'), "delete_by_id方法不存在"
        assert hasattr(service, 'update_entity'), "update_entity方法不存在"
        assert hasattr(service, 'count_all'), "count_all方法不存在"
        assert hasattr(service, 'find_all'), "find_all方法不存在"
        assert hasattr(service, 'log_operation'), "log_operation方法不存在"
        assert hasattr(service, 'get_performance_stats'), "get_performance_stats方法不存在"
        
        # 测试模型类
        assert service.get_model_class() == User, "模型类返回错误"
        
        service.close()
        print("  ✅ BaseService集成测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ BaseService集成测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_context_manager():
    """测试上下文管理器"""
    print("🔍 测试上下文管理器...")
    
    try:
        # 测试同步上下文管理器
        with UserService() as service:
            assert isinstance(service, UserService), "上下文管理器返回类型错误"
            assert service.session is not None, "会话未正确初始化"
        
        print("  ✅ 上下文管理器测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 上下文管理器测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🚀 UserService用户业务服务验证开始")
    print("=" * 50)
    
    tests = [
        ("服务初始化", test_service_initialization),
        ("数据验证功能", test_data_validation),
        ("密码验证功能", test_password_validation),
        ("异步方法", test_async_methods),
        ("辅助方法", test_helper_methods),
        ("异常处理", test_exception_handling),
        ("BaseService集成", test_base_service_integration),
        ("上下文管理器", test_context_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
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
        print("🎉 所有验证通过！UserService用户业务服务开发完成。")
        return 0
    else:
        print("⚠️  部分验证失败，请检查并修复问题。")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
