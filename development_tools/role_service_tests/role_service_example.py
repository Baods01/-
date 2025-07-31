#!/usr/bin/env python3
"""
RBAC权限系统 - 角色服务使用示例

本文件展示了如何使用RoleService角色业务服务类，
包括角色管理、权限分配、用户分配等功能。

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

from services.role_service import RoleService
from services.exceptions import (
    BusinessLogicError,
    DataValidationError,
    DuplicateResourceError,
    ResourceNotFoundError
)


async def example_role_creation():
    """角色创建示例"""
    print("\n=== 角色创建示例 ===")
    
    with RoleService() as service:
        try:
            # 创建管理员角色
            admin_role = await service.create_role(
                role_name="系统管理员",
                role_code="admin",
                description="系统管理员角色，拥有所有权限"
            )
            
            print(f"✅ 管理员角色创建成功:")
            print(f"   角色ID: {admin_role.id}")
            print(f"   角色名称: {admin_role.role_name}")
            print(f"   角色代码: {admin_role.role_code}")
            print(f"   状态: {'启用' if admin_role.status == 1 else '禁用'}")
            
            # 创建普通用户角色
            user_role = await service.create_role(
                role_name="普通用户",
                role_code="user",
                description="普通用户角色，基础权限"
            )
            
            print(f"✅ 普通用户角色创建成功:")
            print(f"   角色ID: {user_role.id}")
            print(f"   角色名称: {user_role.role_name}")
            print(f"   角色代码: {user_role.role_code}")
            
            return admin_role, user_role
            
        except DuplicateResourceError as e:
            print(f"❌ 角色创建失败 - 重复: {e.message}")
        except DataValidationError as e:
            print(f"❌ 角色创建失败 - 验证: {e.message}")
        except Exception as e:
            print(f"❌ 角色创建失败 - 其他: {str(e)}")
        
        return None, None


async def example_role_management():
    """角色管理示例"""
    print("\n=== 角色管理示例 ===")
    
    with RoleService() as service:
        try:
            # 获取角色
            role = await service.get_role_by_code("admin")
            if not role:
                print("❌ 管理员角色不存在，跳过管理测试")
                return
            
            print(f"当前角色: {role.role_name} ({role.role_code})")
            
            # 更新角色信息
            updated_role = await service.update_role(
                role.id,
                description="更新后的系统管理员角色描述"
            )
            
            print(f"✅ 角色信息更新成功")
            
            # 获取活跃角色列表
            active_roles = await service.get_active_roles(limit=10)
            print(f"✅ 获取到 {len(active_roles)} 个活跃角色")
            
            for role in active_roles:
                print(f"   - {role.role_name} ({role.role_code})")
            
        except Exception as e:
            print(f"❌ 角色管理测试失败: {str(e)}")


async def example_permission_assignment():
    """权限分配示例"""
    print("\n=== 权限分配示例 ===")
    
    with RoleService() as service:
        try:
            # 获取角色
            role = await service.get_role_by_code("admin")
            if not role:
                print("❌ 管理员角色不存在，跳过权限分配测试")
                return
            
            # 模拟权限ID列表（实际使用中应该从数据库获取）
            permission_ids = [1, 2, 3, 4, 5]
            
            # 分配权限
            success = await service.assign_permissions(
                role.id,
                permission_ids,
                granted_by=1  # 假设操作者ID为1
            )
            
            if success:
                print(f"✅ 权限分配成功: 角色ID={role.id}, 权限数量={len(permission_ids)}")
                
                # 获取角色权限
                permissions = await service.get_role_permissions(role.id)
                print(f"✅ 角色当前权限数量: {len(permissions)}")
                
                # 撤销部分权限
                revoke_ids = [4, 5]
                revoke_success = await service.revoke_permissions(role.id, revoke_ids)
                
                if revoke_success:
                    print(f"✅ 权限撤销成功: 撤销权限数量={len(revoke_ids)}")
                    
                    # 再次获取角色权限
                    updated_permissions = await service.get_role_permissions(role.id)
                    print(f"✅ 撤销后权限数量: {len(updated_permissions)}")
            
        except Exception as e:
            print(f"❌ 权限分配测试失败: {str(e)}")


async def example_user_assignment():
    """用户分配示例"""
    print("\n=== 用户分配示例 ===")
    
    with RoleService() as service:
        try:
            # 获取角色
            role = await service.get_role_by_code("user")
            if not role:
                print("❌ 普通用户角色不存在，跳过用户分配测试")
                return
            
            # 模拟用户ID列表（实际使用中应该从数据库获取）
            user_ids = [1, 2, 3]
            
            # 分配用户
            success = await service.assign_users(
                role.id,
                user_ids,
                assigned_by=1  # 假设操作者ID为1
            )
            
            if success:
                print(f"✅ 用户分配成功: 角色ID={role.id}, 用户数量={len(user_ids)}")
                
                # 获取角色用户（分页）
                result = await service.get_role_users(role.id, page=1, size=10)
                print(f"✅ 角色用户数量: {result['pagination']['total']}")
                print(f"   当前页用户数: {len(result['users'])}")
                
                # 撤销部分用户
                revoke_user_ids = [3]
                revoke_success = await service.revoke_users(role.id, revoke_user_ids)
                
                if revoke_success:
                    print(f"✅ 用户撤销成功: 撤销用户数量={len(revoke_user_ids)}")
            
        except Exception as e:
            print(f"❌ 用户分配测试失败: {str(e)}")


async def example_role_search():
    """角色搜索示例"""
    print("\n=== 角色搜索示例 ===")
    
    with RoleService() as service:
        try:
            # 搜索角色
            roles = await service.search_roles("管理", limit=10)
            print(f"✅ 搜索到 {len(roles)} 个角色:")
            
            for role in roles:
                print(f"   - {role.role_name} ({role.role_code}) - {'启用' if role.status == 1 else '禁用'}")
            
            # 根据代码获取角色
            admin_role = await service.get_role_by_code("admin")
            if admin_role:
                print(f"✅ 根据代码获取角色: {admin_role.role_name}")
            
            # 根据名称获取角色
            user_role = await service.get_role_by_name("普通用户")
            if user_role:
                print(f"✅ 根据名称获取角色: {user_role.role_code}")
            
        except Exception as e:
            print(f"❌ 角色搜索测试失败: {str(e)}")


async def example_role_statistics():
    """角色统计示例"""
    print("\n=== 角色统计示例 ===")
    
    with RoleService() as service:
        try:
            # 获取统计信息
            stats = await service.get_role_statistics()
            
            print("✅ 角色统计信息:")
            print(f"   总角色数: {stats['total_roles']}")
            print(f"   活跃角色: {stats['active_roles']}")
            print(f"   禁用角色: {stats['inactive_roles']}")
            print(f"   统计时间: {stats['timestamp']}")
            
            print("\n✅ 角色详细信息:")
            for role_detail in stats['role_details'][:5]:  # 只显示前5个
                print(f"   - {role_detail['role_name']}: "
                      f"权限数={role_detail['permission_count']}, "
                      f"用户数={role_detail['user_count']}")
            
        except Exception as e:
            print(f"❌ 角色统计测试失败: {str(e)}")


async def example_batch_operations():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===")
    
    with RoleService() as service:
        try:
            # 批量创建角色
            roles_data = [
                {
                    "role_name": "编辑者",
                    "role_code": "editor",
                    "description": "内容编辑者角色"
                },
                {
                    "role_name": "审核者",
                    "role_code": "reviewer",
                    "description": "内容审核者角色"
                }
            ]
            
            created_roles = await service.batch_create_roles(roles_data)
            print(f"✅ 批量创建角色成功: {len(created_roles)} 个角色")
            
            for role in created_roles:
                print(f"   - {role.role_name} ({role.role_code})")
            
            # 批量分配权限
            assignments = [
                {
                    "role_id": created_roles[0].id,
                    "permission_ids": [1, 2, 3],
                    "granted_by": 1
                },
                {
                    "role_id": created_roles[1].id,
                    "permission_ids": [2, 3, 4],
                    "granted_by": 1
                }
            ]
            
            batch_result = await service.batch_assign_permissions(assignments)
            print(f"✅ 批量分配权限完成:")
            print(f"   总分配数: {batch_result['total_assignments']}")
            print(f"   成功数: {batch_result['success_count']}")
            print(f"   失败数: {batch_result['failed_count']}")
            
        except Exception as e:
            print(f"❌ 批量操作测试失败: {str(e)}")


async def example_data_validation():
    """数据验证示例"""
    print("\n=== 数据验证示例 ===")
    
    with RoleService() as service:
        # 测试各种验证错误
        test_cases = [
            {
                "name": "角色名称太短",
                "data": ("A", "test_role"),
                "expected": "角色名称长度必须在2-100字符之间"
            },
            {
                "name": "角色代码格式错误",
                "data": ("测试角色", "123role"),
                "expected": "角色代码必须以字母开头"
            },
            {
                "name": "角色名称包含特殊字符",
                "data": ("测试<角色>", "test_role2"),
                "expected": "角色名称不能包含特殊字符"
            },
            {
                "name": "角色代码太长",
                "data": ("测试角色", "a" * 51),
                "expected": "角色代码长度必须在2-50字符之间"
            }
        ]
        
        for test_case in test_cases:
            try:
                await service.create_role(*test_case["data"])
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
    print("🚀 RoleService 角色服务使用示例")
    print("=" * 50)
    
    # 运行所有示例
    await example_role_creation()
    await example_role_management()
    await example_permission_assignment()
    await example_user_assignment()
    await example_role_search()
    await example_role_statistics()
    await example_batch_operations()
    await example_data_validation()
    
    print("\n" + "=" * 50)
    print("🎉 所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())
