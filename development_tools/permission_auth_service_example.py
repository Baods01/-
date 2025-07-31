#!/usr/bin/env python3
"""
RBAC权限系统 - 权限与认证业务服务使用示例

本文件展示了如何使用PermissionService权限业务服务和AuthService认证业务服务，
包括权限管理、用户认证、JWT令牌管理等功能。

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import sys
import os
import asyncio
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.permission_service import PermissionService
from services.auth_service import AuthService
from services.exceptions import (
    BusinessLogicError,
    DataValidationError,
    DuplicateResourceError,
    ResourceNotFoundError,
    AuthenticationError
)


async def example_permission_management():
    """权限管理示例"""
    print("\n=== 权限管理示例 ===")
    
    with PermissionService() as service:
        try:
            # 创建权限
            user_view_permission = await service.create_permission(
                name="查看用户",
                code="user:view",
                resource_type="user",
                action_type="view",
                description="查看用户信息的权限"
            )
            
            print(f"✅ 权限创建成功:")
            print(f"   权限ID: {user_view_permission.id}")
            print(f"   权限名称: {user_view_permission.permission_name}")
            print(f"   权限代码: {user_view_permission.permission_code}")
            
            # 创建更多权限
            permissions_data = [
                {
                    "name": "创建用户",
                    "code": "user:create",
                    "resource_type": "user",
                    "action_type": "create",
                    "description": "创建新用户的权限"
                },
                {
                    "name": "编辑用户",
                    "code": "user:edit",
                    "resource_type": "user",
                    "action_type": "edit",
                    "description": "编辑用户信息的权限"
                },
                {
                    "name": "删除用户",
                    "code": "user:delete",
                    "resource_type": "user",
                    "action_type": "delete",
                    "description": "删除用户的权限"
                }
            ]
            
            # 批量创建权限
            created_permissions = await service.batch_create_permissions(permissions_data)
            print(f"✅ 批量创建权限成功: {len(created_permissions)} 个权限")
            
            for perm in created_permissions:
                print(f"   - {perm.permission_name} ({perm.permission_code})")
            
            # 获取权限树
            permission_tree = await service.get_permission_tree("user")
            print(f"✅ 用户权限树:")
            
            if "user" in permission_tree:
                user_perms = permission_tree["user"]
                print(f"   资源: {user_perms['resource_name']}")
                print(f"   权限数量: {len(user_perms['permissions'])}")
                
                for perm in user_perms['permissions']:
                    print(f"     - {perm['name']} ({perm['code']})")
            
            # 搜索权限
            search_results = await service.search_permissions("用户", limit=5)
            print(f"✅ 搜索结果: 找到 {len(search_results)} 个相关权限")
            
            # 获取权限统计
            stats = await service.get_permission_statistics()
            print(f"✅ 权限统计:")
            print(f"   总权限数: {stats['total_permissions']}")
            print(f"   资源类型数: {stats['resource_count']}")
            print(f"   操作类型数: {stats['action_count']}")
            
        except Exception as e:
            print(f"❌ 权限管理测试失败: {str(e)}")


async def example_authentication():
    """认证功能示例"""
    print("\n=== 认证功能示例 ===")
    
    with AuthService() as service:
        try:
            # 模拟用户登录（注意：这需要数据库中有实际用户数据）
            print("ℹ️  注意：以下登录示例需要数据库中有实际用户数据")
            
            # 示例：尝试登录（会失败，因为没有实际用户数据）
            try:
                login_result = await service.login(
                    username="admin",
                    password="password123",
                    remember_me=True,
                    ip_address="127.0.0.1",
                    user_agent="Test Client"
                )
                
                print(f"✅ 登录成功:")
                print(f"   访问令牌: {login_result['access_token'][:50]}...")
                print(f"   刷新令牌: {login_result['refresh_token'][:50]}...")
                print(f"   令牌类型: {login_result['token_type']}")
                print(f"   过期时间: {login_result['expires_in']} 秒")
                
                # 验证令牌
                access_token = login_result['access_token']
                payload = await service.verify_token(access_token)
                
                if payload:
                    print(f"✅ 令牌验证成功:")
                    print(f"   用户ID: {payload.get('user_id')}")
                    print(f"   用户名: {payload.get('username')}")
                    print(f"   角色: {payload.get('roles')}")
                else:
                    print("❌ 令牌验证失败")
                
                # 刷新令牌
                refresh_token = login_result['refresh_token']
                new_tokens = await service.refresh_token(refresh_token)
                
                print(f"✅ 令牌刷新成功:")
                print(f"   新访问令牌: {new_tokens['access_token'][:50]}...")
                
                # 登出
                logout_success = await service.logout(access_token, payload.get('user_id'))
                print(f"✅ 登出成功: {logout_success}")
                
            except AuthenticationError as e:
                print(f"ℹ️  预期的认证失败: {e.message}")
            except Exception as e:
                print(f"ℹ️  登录测试异常（预期）: {str(e)}")
            
            # 测试令牌验证功能
            print("\n--- 令牌验证功能测试 ---")
            
            # 测试无效令牌
            invalid_payload = await service.verify_token("invalid.token.here")
            print(f"✅ 无效令牌验证: {invalid_payload is None}")
            
            # 测试令牌有效性检查
            is_valid = await service.is_token_valid("invalid.token.here")
            print(f"✅ 令牌有效性检查: {not is_valid}")
            
        except Exception as e:
            print(f"❌ 认证功能测试失败: {str(e)}")


async def example_permission_check():
    """权限检查示例"""
    print("\n=== 权限检查示例 ===")
    
    with PermissionService() as perm_service, AuthService() as auth_service:
        try:
            # 测试权限检查（注意：这需要数据库中有实际用户和权限数据）
            print("ℹ️  注意：以下权限检查示例需要数据库中有实际用户和权限数据")
            
            try:
                # 使用PermissionService检查权限
                has_permission = await perm_service.check_permission(1, "user:view")
                print(f"✅ 用户1是否有user:view权限: {has_permission}")
                
                # 使用AuthService检查权限
                has_permission2 = await auth_service.check_permission(1, "user:create")
                print(f"✅ 用户1是否有user:create权限: {has_permission2}")
                
            except ResourceNotFoundError as e:
                print(f"ℹ️  预期的资源不存在: {e.message}")
            except Exception as e:
                print(f"ℹ️  权限检查异常（预期）: {str(e)}")
            
            # 测试权限代码格式验证
            print("\n--- 权限代码格式验证 ---")
            
            valid_codes = ["user:view", "role:create", "system:admin"]
            invalid_codes = ["invalid", "user:", ":view", "user-view"]
            
            for code in valid_codes:
                is_valid = perm_service._is_valid_permission_code(code)
                print(f"✅ {code} 格式验证: {is_valid}")
            
            for code in invalid_codes:
                is_valid = perm_service._is_valid_permission_code(code)
                print(f"✅ {code} 格式验证: {not is_valid}")
            
        except Exception as e:
            print(f"❌ 权限检查测试失败: {str(e)}")


async def example_data_validation():
    """数据验证示例"""
    print("\n=== 数据验证示例 ===")
    
    with PermissionService() as service:
        # 测试各种验证错误
        test_cases = [
            {
                "name": "权限名称太短",
                "data": ("A", "test:view", "test", "view"),
                "expected": "权限名称长度必须在2-64字符之间"
            },
            {
                "name": "权限代码格式错误",
                "data": ("测试权限", "invalid-code", "test", "view"),
                "expected": "权限代码格式错误"
            },
            {
                "name": "权限代码不匹配",
                "data": ("测试权限", "wrong:code", "test", "view"),
                "expected": "权限代码格式错误，期望: test:view"
            }
        ]
        
        for test_case in test_cases:
            try:
                await service.create_permission(*test_case["data"])
                print(f"❌ {test_case['name']}: 应该失败但成功了")
            except DataValidationError as e:
                if test_case["expected"] in str(e):
                    print(f"✅ {test_case['name']}: 验证正确")
                else:
                    print(f"⚠️  {test_case['name']}: 验证消息不匹配 - {e.message}")
            except Exception as e:
                print(f"❌ {test_case['name']}: 意外错误 - {str(e)}")


async def example_service_integration():
    """服务集成示例"""
    print("\n=== 服务集成示例 ===")
    
    try:
        # 展示两个服务的集成使用
        with PermissionService() as perm_service, AuthService() as auth_service:
            print("✅ 权限服务和认证服务同时初始化成功")
            
            # 获取资源类型
            resource_types = await perm_service.get_all_resource_types()
            print(f"✅ 系统中的资源类型: {resource_types}")
            
            # 获取操作类型
            action_types = await perm_service.get_all_action_types()
            print(f"✅ 系统中的操作类型: {action_types}")
            
            # 展示权限树结构
            full_tree = await perm_service.get_permission_tree()
            print(f"✅ 完整权限树包含 {len(full_tree)} 个资源类型")
            
            for resource_type, resource_data in full_tree.items():
                print(f"   - {resource_data['resource_name']}: {len(resource_data['permissions'])} 个权限")
            
            # 展示认证服务的辅助功能
            print("\n--- 认证服务辅助功能 ---")
            
            # 获取当前用户（使用无效令牌）
            current_user = await auth_service.get_current_user("invalid.token")
            print(f"✅ 无效令牌获取用户: {current_user is None}")
            
            # 获取用户会话
            sessions = await auth_service.get_user_sessions(1)
            print(f"✅ 用户会话数量: {len(sessions)}")
            
    except Exception as e:
        print(f"❌ 服务集成测试失败: {str(e)}")


async def main():
    """主函数"""
    print("🚀 权限与认证业务服务使用示例")
    print("=" * 60)
    
    # 运行所有示例
    await example_permission_management()
    await example_authentication()
    await example_permission_check()
    await example_data_validation()
    await example_service_integration()
    
    print("\n" + "=" * 60)
    print("🎉 所有示例运行完成！")
    print("\n📝 注意事项:")
    print("1. 部分功能需要数据库中有实际的用户、角色、权限数据")
    print("2. 认证功能的完整测试需要配置JWT密钥和数据库连接")
    print("3. 权限检查功能需要完整的RBAC数据结构")
    print("4. 生产环境中请修改JWT密钥和其他安全配置")


if __name__ == "__main__":
    asyncio.run(main())
