#!/usr/bin/env python3
"""
RBAC权限系统 - 用户服务使用示例

本文件展示了如何使用UserService用户业务服务类，
包括用户注册、认证、权限管理等功能。

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import sys
import os
import asyncio
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.user_service import UserService
from services.exceptions import (
    AuthenticationError,
    DataValidationError,
    DuplicateResourceError,
    ResourceNotFoundError
)


async def example_user_registration():
    """用户注册示例"""
    print("\n=== 用户注册示例 ===")
    
    async with UserService() as service:
        try:
            # 创建用户
            user = await service.create_user(
                username="testuser",
                email="test@example.com",
                password="TestPassword123!",
                full_name="测试用户"
            )
            
            print(f"✅ 用户注册成功:")
            print(f"   用户ID: {user.id}")
            print(f"   用户名: {user.username}")
            print(f"   邮箱: {user.email}")
            print(f"   状态: {'启用' if user.is_active() else '禁用'}")
            
            return user
            
        except DuplicateResourceError as e:
            print(f"❌ 用户注册失败 - 重复: {e.message}")
        except DataValidationError as e:
            print(f"❌ 用户注册失败 - 验证: {e.message}")
        except Exception as e:
            print(f"❌ 用户注册失败 - 其他: {str(e)}")
        
        return None


async def example_user_authentication():
    """用户认证示例"""
    print("\n=== 用户认证示例 ===")
    
    async with UserService() as service:
        try:
            # 用户名登录
            user = await service.authenticate_user("testuser", "TestPassword123!")
            if user:
                print(f"✅ 用户名登录成功: {user.username}")
            
            # 邮箱登录
            user = await service.authenticate_user("test@example.com", "TestPassword123!")
            if user:
                print(f"✅ 邮箱登录成功: {user.email}")
            
            # 错误密码测试
            try:
                await service.authenticate_user("testuser", "WrongPassword")
            except AuthenticationError as e:
                print(f"✅ 错误密码被正确拒绝: {e.message}")
            
        except Exception as e:
            print(f"❌ 认证测试失败: {str(e)}")


async def example_password_management():
    """密码管理示例"""
    print("\n=== 密码管理示例 ===")
    
    async with UserService() as service:
        try:
            # 获取用户
            user = await service.get_user_by_username("testuser")
            if not user:
                print("❌ 用户不存在，跳过密码管理测试")
                return
            
            # 修改密码
            success = await service.change_password(
                user.id,
                "TestPassword123!",
                "NewPassword456@"
            )
            
            if success:
                print("✅ 密码修改成功")
                
                # 验证新密码
                auth_user = await service.authenticate_user("testuser", "NewPassword456@")
                if auth_user:
                    print("✅ 新密码验证成功")
                
                # 恢复原密码
                await service.change_password(
                    user.id,
                    "NewPassword456@",
                    "TestPassword123!"
                )
                print("✅ 密码已恢复")
            
        except Exception as e:
            print(f"❌ 密码管理测试失败: {str(e)}")


async def example_user_management():
    """用户管理示例"""
    print("\n=== 用户管理示例 ===")
    
    async with UserService() as service:
        try:
            # 获取用户
            user = await service.get_user_by_username("testuser")
            if not user:
                print("❌ 用户不存在，跳过用户管理测试")
                return
            
            print(f"当前用户状态: {'启用' if user.is_active() else '禁用'}")
            
            # 禁用用户
            success = await service.disable_user(user.id)
            if success:
                print("✅ 用户禁用成功")
                
                # 验证禁用状态
                try:
                    await service.authenticate_user("testuser", "TestPassword123!")
                except AuthenticationError as e:
                    print(f"✅ 禁用用户登录被正确拒绝: {e.message}")
            
            # 启用用户
            success = await service.enable_user(user.id)
            if success:
                print("✅ 用户启用成功")
                
                # 验证启用状态
                auth_user = await service.authenticate_user("testuser", "TestPassword123!")
                if auth_user:
                    print("✅ 启用用户登录成功")
            
        except Exception as e:
            print(f"❌ 用户管理测试失败: {str(e)}")


async def example_user_update():
    """用户信息更新示例"""
    print("\n=== 用户信息更新示例 ===")
    
    async with UserService() as service:
        try:
            # 获取用户
            user = await service.get_user_by_username("testuser")
            if not user:
                print("❌ 用户不存在，跳过更新测试")
                return
            
            print(f"更新前: {user.username} - {user.email}")
            
            # 更新用户信息
            updated_user = await service.update_user(
                user.id,
                full_name="更新后的测试用户",
                email="updated@example.com"
            )
            
            print(f"✅ 用户信息更新成功:")
            print(f"   全名: {updated_user.full_name}")
            print(f"   邮箱: {updated_user.email}")
            
            # 恢复原邮箱
            await service.update_user(user.id, email="test@example.com")
            print("✅ 邮箱已恢复")
            
        except Exception as e:
            print(f"❌ 用户更新测试失败: {str(e)}")


async def example_user_search():
    """用户搜索示例"""
    print("\n=== 用户搜索示例 ===")
    
    async with UserService() as service:
        try:
            # 搜索用户
            users = await service.search_users("test", limit=10)
            print(f"✅ 搜索到 {len(users)} 个用户:")
            
            for user in users:
                print(f"   - {user.username} ({user.email}) - {'启用' if user.is_active() else '禁用'}")
            
            # 获取活跃用户
            active_users = await service.get_active_users(limit=5)
            print(f"✅ 活跃用户数量: {len(active_users)}")
            
        except Exception as e:
            print(f"❌ 用户搜索测试失败: {str(e)}")


async def example_user_statistics():
    """用户统计示例"""
    print("\n=== 用户统计示例 ===")
    
    async with UserService() as service:
        try:
            # 获取统计信息
            stats = await service.get_user_statistics()
            
            print("✅ 用户统计信息:")
            print(f"   总用户数: {stats['total_users']}")
            print(f"   活跃用户: {stats['active_users']}")
            print(f"   禁用用户: {stats['inactive_users']}")
            print(f"   统计时间: {stats['timestamp']}")
            
        except Exception as e:
            print(f"❌ 用户统计测试失败: {str(e)}")


async def example_batch_operations():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")
    
    async with UserService() as service:
        try:
            # 批量创建用户
            users_data = [
                {
                    "username": "batchuser1",
                    "email": "batch1@example.com",
                    "password": "BatchPass123!",
                    "full_name": "批量用户1"
                },
                {
                    "username": "batchuser2",
                    "email": "batch2@example.com",
                    "password": "BatchPass123!",
                    "full_name": "批量用户2"
                }
            ]
            
            created_users = await service.batch_create_users(users_data)
            print(f"✅ 批量创建用户成功: {len(created_users)} 个用户")
            
            for user in created_users:
                print(f"   - {user.username} ({user.email})")
            
        except Exception as e:
            print(f"❌ 批量操作测试失败: {str(e)}")


async def example_data_validation():
    """数据验证示例"""
    print("\n=== 数据验证示例 ===")
    
    async with UserService() as service:
        # 测试各种验证错误
        test_cases = [
            {
                "name": "用户名太短",
                "data": ("ab", "test@example.com", "TestPass123!"),
                "expected": "用户名长度必须在3-50字符之间"
            },
            {
                "name": "用户名格式错误",
                "data": ("123user", "test@example.com", "TestPass123!"),
                "expected": "用户名必须以字母开头"
            },
            {
                "name": "邮箱格式错误",
                "data": ("testuser2", "invalid-email", "TestPass123!"),
                "expected": "邮箱地址格式不正确"
            },
            {
                "name": "密码强度不足",
                "data": ("testuser3", "test3@example.com", "weak"),
                "expected": "密码强度不足"
            }
        ]
        
        for test_case in test_cases:
            try:
                await service.create_user(*test_case["data"])
                print(f"❌ {test_case['name']}: 应该失败但成功了")
            except DataValidationError as e:
                if test_case["expected"] in str(e):
                    print(f"✅ {test_case['name']}: 验证正确")
                else:
                    print(f"⚠️  {test_case['name']}: 验证消息不匹配 - {e.message}")
            except Exception as e:
                print(f"❌ {test_case['name']}: 意外错误 - {str(e)}")


async def main():
    """主函数"""
    print("🚀 UserService 用户服务使用示例")
    print("=" * 50)
    
    # 运行所有示例
    await example_user_registration()
    await example_user_authentication()
    await example_password_management()
    await example_user_management()
    await example_user_update()
    await example_user_search()
    await example_user_statistics()
    await example_batch_operations()
    await example_data_validation()
    
    print("\n" + "=" * 50)
    print("🎉 所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())
