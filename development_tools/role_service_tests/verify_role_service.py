#!/usr/bin/env python3
"""
RBAC权限系统 - 角色服务验证脚本

验证RoleService角色业务服务类的功能完整性和正确性。

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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.role_service import RoleService
from services.exceptions import (
    BusinessLogicError,
    DataValidationError,
    DuplicateResourceError,
    ResourceNotFoundError
)
from models.role import Role


def test_service_initialization():
    """测试服务初始化"""
    print("🔍 测试服务初始化...")
    
    try:
        service = RoleService()
        
        # 验证基本属性
        assert service.model_class == Role, "模型类设置错误"
        assert hasattr(service, 'role_dao'), "RoleDao未初始化"
        assert hasattr(service, 'role_permission_dao'), "RolePermissionDao未初始化"
        assert hasattr(service, 'user_role_dao'), "UserRoleDao未初始化"
        assert hasattr(service, 'permission_dao'), "PermissionDao未初始化"
        assert hasattr(service, 'user_dao'), "UserDao未初始化"
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
        service = RoleService()
        
        # 测试角色名称验证
        try:
            service._validate_role_name("A")  # 太短
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        try:
            service._validate_role_name("角色<名称>")  # 包含特殊字符
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        # 测试有效角色名称
        service._validate_role_name("管理员角色")  # 应该通过
        
        # 测试角色代码验证
        try:
            service._validate_role_code("123role")  # 数字开头
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        try:
            service._validate_role_code("a" * 51)  # 太长
            assert False, "应该抛出异常"
        except DataValidationError:
            pass  # 预期的异常
        
        # 测试有效角色代码
        service._validate_role_code("admin_role")  # 应该通过
        
        service.close()
        print("  ✅ 数据验证功能测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 数据验证功能测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def test_async_methods():
    """测试异步方法"""
    print("🔍 测试异步方法...")
    
    try:
        service = RoleService()
        
        # 测试方法存在性和可调用性
        assert hasattr(service, 'create_role'), "create_role方法不存在"
        assert callable(service.create_role), "create_role不可调用"
        
        assert hasattr(service, 'update_role'), "update_role方法不存在"
        assert callable(service.update_role), "update_role不可调用"
        
        assert hasattr(service, 'delete_role'), "delete_role方法不存在"
        assert callable(service.delete_role), "delete_role不可调用"
        
        assert hasattr(service, 'assign_permissions'), "assign_permissions方法不存在"
        assert callable(service.assign_permissions), "assign_permissions不可调用"
        
        assert hasattr(service, 'revoke_permissions'), "revoke_permissions方法不存在"
        assert callable(service.revoke_permissions), "revoke_permissions不可调用"
        
        assert hasattr(service, 'get_role_users'), "get_role_users方法不存在"
        assert callable(service.get_role_users), "get_role_users不可调用"
        
        assert hasattr(service, 'get_role_permissions'), "get_role_permissions方法不存在"
        assert callable(service.get_role_permissions), "get_role_permissions不可调用"
        
        assert hasattr(service, 'assign_users'), "assign_users方法不存在"
        assert callable(service.assign_users), "assign_users不可调用"
        
        assert hasattr(service, 'revoke_users'), "revoke_users方法不存在"
        assert callable(service.revoke_users), "revoke_users不可调用"
        
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
        service = RoleService()
        
        # 测试辅助方法存在性
        assert hasattr(service, 'get_role_by_code'), "get_role_by_code方法不存在"
        assert hasattr(service, 'get_role_by_name'), "get_role_by_name方法不存在"
        assert hasattr(service, 'get_active_roles'), "get_active_roles方法不存在"
        assert hasattr(service, 'search_roles'), "search_roles方法不存在"
        assert hasattr(service, 'get_role_statistics'), "get_role_statistics方法不存在"
        assert hasattr(service, 'batch_create_roles'), "batch_create_roles方法不存在"
        assert hasattr(service, 'batch_assign_permissions'), "batch_assign_permissions方法不存在"
        
        # 测试可调用性
        assert callable(service.get_role_by_code), "get_role_by_code不可调用"
        assert callable(service.get_role_by_name), "get_role_by_name不可调用"
        assert callable(service.get_active_roles), "get_active_roles不可调用"
        assert callable(service.search_roles), "search_roles不可调用"
        assert callable(service.get_role_statistics), "get_role_statistics不可调用"
        assert callable(service.batch_create_roles), "batch_create_roles不可调用"
        assert callable(service.batch_assign_permissions), "batch_assign_permissions不可调用"
        
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
        service = RoleService()
        
        # 测试异常类导入
        from services.exceptions import (
            BusinessLogicError,
            DataValidationError,
            DuplicateResourceError,
            ResourceNotFoundError
        )
        
        # 测试异常类实例化
        business_error = BusinessLogicError("测试业务异常")
        assert business_error.error_code == "BUSINESS_ERROR", "业务异常错误码错误"
        
        validation_error = DataValidationError("测试验证异常")
        assert validation_error.error_code == "VALIDATION_ERROR", "验证异常错误码错误"
        
        duplicate_error = DuplicateResourceError("Role", "role_name", "test")
        assert duplicate_error.error_code == "DUPLICATE_RESOURCE", "重复资源异常错误码错误"
        
        not_found_error = ResourceNotFoundError("Role", "123")
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
        service = RoleService()
        
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
        assert service.get_model_class() == Role, "模型类返回错误"
        
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
        with RoleService() as service:
            assert isinstance(service, RoleService), "上下文管理器返回类型错误"
            assert service.session is not None, "会话未正确初始化"
        
        print("  ✅ 上下文管理器测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 上下文管理器测试失败: {str(e)}")
        traceback.print_exc()
        return False


def test_validation_methods():
    """测试验证方法"""
    print("🔍 测试验证方法...")
    
    try:
        service = RoleService()
        
        # 测试验证方法存在性
        assert hasattr(service, '_validate_role_data'), "_validate_role_data方法不存在"
        assert hasattr(service, '_validate_role_name'), "_validate_role_name方法不存在"
        assert hasattr(service, '_validate_role_code'), "_validate_role_code方法不存在"
        assert hasattr(service, '_check_role_uniqueness'), "_check_role_uniqueness方法不存在"
        assert hasattr(service, '_check_role_dependencies'), "_check_role_dependencies方法不存在"
        assert hasattr(service, '_handle_role_cascade_deletion'), "_handle_role_cascade_deletion方法不存在"
        
        service.close()
        print("  ✅ 验证方法测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 验证方法测试失败: {str(e)}")
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🚀 RoleService角色业务服务验证开始")
    print("=" * 50)
    
    tests = [
        ("服务初始化", test_service_initialization),
        ("数据验证功能", test_data_validation),
        ("异步方法", test_async_methods),
        ("辅助方法", test_helper_methods),
        ("异常处理", test_exception_handling),
        ("BaseService集成", test_base_service_integration),
        ("上下文管理器", test_context_manager),
        ("验证方法", test_validation_methods)
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
        print("🎉 所有验证通过！RoleService角色业务服务开发完成。")
        return 0
    else:
        print("⚠️  部分验证失败，请检查并修复问题。")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
