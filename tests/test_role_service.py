#!/usr/bin/env python3
"""
RBAC权限系统 - 角色服务测试

本文件包含RoleService角色业务服务类的单元测试，
验证角色管理、权限分配、用户分配等功能。

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import sys
import os
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock

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
from models.permission import Permission
from models.user import User


class TestRoleService(unittest.TestCase):
    """RoleService测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟会话
        self.mock_session = Mock()
        
        # 创建测试服务实例
        with patch('services.role_service.RoleDao'), \
             patch('services.role_service.RolePermissionDao'), \
             patch('services.role_service.UserRoleDao'), \
             patch('services.role_service.PermissionDao'), \
             patch('services.role_service.UserDao'):
            self.service = RoleService(session=self.mock_session)
            
            # 设置模拟对象
            self.service.role_dao = Mock()
            self.service.role_permission_dao = Mock()
            self.service.user_role_dao = Mock()
            self.service.permission_dao = Mock()
            self.service.user_dao = Mock()
    
    def tearDown(self):
        """测试后清理"""
        self.service.close()
    
    def test_create_role_success(self):
        """测试成功创建角色"""
        async def test():
            # 设置模拟返回值
            self.service.role_dao.find_by_name = Mock(return_value=None)
            self.service.role_dao.find_by_role_code = Mock(return_value=None)
            
            # 模拟角色对象
            with patch('services.role_service.Role') as mock_role_class, \
                 patch.object(self.service, 'save_entity') as mock_save:
                
                mock_role = Mock(spec=Role)
                mock_role.id = 1
                mock_role.role_name = "管理员"
                mock_role.role_code = "admin"
                mock_role.validate = Mock(return_value=True)
                mock_role_class.return_value = mock_role
                mock_save.return_value = mock_role
                
                # 执行测试
                result = await self.service.create_role("管理员", "admin", "管理员角色")
                
                # 验证结果
                self.assertEqual(result, mock_role)
                mock_role.validate.assert_called_once()
        
        asyncio.run(test())
    
    def test_create_role_duplicate_name(self):
        """测试角色名称重复"""
        async def test():
            # 设置模拟返回值 - 角色名称已存在
            existing_role = Mock(spec=Role)
            existing_role.id = 1
            self.service.role_dao.find_by_name = Mock(return_value=existing_role)
            
            # 执行测试并验证异常
            with self.assertRaises(DuplicateResourceError) as context:
                await self.service.create_role("管理员", "admin", "管理员角色")
            
            self.assertIn("角色名称", str(context.exception))
        
        asyncio.run(test())
    
    def test_create_role_duplicate_code(self):
        """测试角色代码重复"""
        async def test():
            # 设置模拟返回值 - 角色代码已存在
            self.service.role_dao.find_by_name = Mock(return_value=None)
            existing_role = Mock(spec=Role)
            existing_role.id = 1
            self.service.role_dao.find_by_role_code = Mock(return_value=existing_role)
            
            # 执行测试并验证异常
            with self.assertRaises(DuplicateResourceError) as context:
                await self.service.create_role("管理员", "admin", "管理员角色")
            
            self.assertIn("角色代码", str(context.exception))
        
        asyncio.run(test())
    
    def test_update_role_success(self):
        """测试成功更新角色"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            mock_role.role_name = "管理员"
            mock_role.role_code = "admin"
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role), \
                 patch.object(self.service, 'update_entity', return_value=mock_role):
                
                updated_role = await self.service.update_role(1, description="更新描述")
                self.assertEqual(updated_role, mock_role)
                
                # 验证过滤禁止字段
                self.service.update_entity.assert_called_once()
                args = self.service.update_entity.call_args[1]
                self.assertNotIn('id', args)
                self.assertNotIn('created_at', args)
        
        asyncio.run(test())
    
    def test_delete_role_success(self):
        """测试成功删除角色"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            mock_role.role_name = "管理员"
            mock_role.role_code = "admin"
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role), \
                 patch.object(self.service, 'delete_by_id', return_value=True), \
                 patch.object(self.service, '_check_role_dependencies'), \
                 patch.object(self.service, '_handle_role_cascade_deletion'):
                
                result = await self.service.delete_role(1)
                self.assertTrue(result)
        
        asyncio.run(test())
    
    def test_delete_role_with_dependencies(self):
        """测试删除有依赖的角色"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role):
                # 模拟依赖检查失败
                with patch.object(self.service, '_check_role_dependencies', 
                                side_effect=BusinessLogicError("角色有依赖")):
                    
                    with self.assertRaises(BusinessLogicError):
                        await self.service.delete_role(1, force=False)
        
        asyncio.run(test())
    
    def test_assign_permissions_success(self):
        """测试成功分配权限"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            
            mock_permissions = [Mock(id=1), Mock(id=2), Mock(id=3)]
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role), \
                 patch.object(self.service, '_validate_permission_ids', return_value=[1, 2, 3]), \
                 patch.object(self.service, '_check_permission_assignment_validity'):
                
                # 模拟权限分配
                self.service.role_permission_dao.find_by_role_permission = Mock(return_value=None)
                self.service.role_permission_dao.grant_permission = Mock(return_value=True)
                
                result = await self.service.assign_permissions(1, [1, 2, 3])
                self.assertTrue(result)
        
        asyncio.run(test())
    
    def test_revoke_permissions_success(self):
        """测试成功撤销权限"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            
            mock_existing = Mock()
            mock_existing.status = 1
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role), \
                 patch.object(self.service, '_validate_permission_ids', return_value=[1, 2]):
                
                # 模拟权限撤销
                self.service.role_permission_dao.find_by_role_permission = Mock(return_value=mock_existing)
                self.service.role_permission_dao.revoke_permission = Mock(return_value=True)
                
                result = await self.service.revoke_permissions(1, [1, 2])
                self.assertTrue(result)
        
        asyncio.run(test())
    
    def test_get_role_users_success(self):
        """测试获取角色用户"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            mock_role.role_name = "管理员"
            mock_role.role_code = "admin"
            
            mock_users = [Mock(to_dict=lambda: {"id": 1, "username": "user1"}),
                         Mock(to_dict=lambda: {"id": 2, "username": "user2"})]
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role):
                self.service.role_dao.get_role_users = Mock(return_value=mock_users)
                
                result = await self.service.get_role_users(1, page=1, size=10)
                
                self.assertEqual(len(result['users']), 2)
                self.assertEqual(result['pagination']['total'], 2)
                self.assertEqual(result['role_info']['id'], 1)
        
        asyncio.run(test())
    
    def test_get_role_permissions_success(self):
        """测试获取角色权限"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            
            mock_permissions = [Mock(spec=Permission), Mock(spec=Permission)]
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role):
                self.service.role_dao.get_role_permissions = Mock(return_value=mock_permissions)
                
                result = await self.service.get_role_permissions(1)
                self.assertEqual(len(result), 2)
        
        asyncio.run(test())
    
    def test_assign_users_success(self):
        """测试成功分配用户"""
        async def test():
            mock_role = Mock(spec=Role)
            mock_role.id = 1
            
            with patch.object(self.service, 'get_by_id', return_value=mock_role), \
                 patch.object(self.service, '_validate_user_ids', return_value=[1, 2]):
                
                # 模拟用户分配
                self.service.user_role_dao.find_by_user_role = Mock(return_value=None)
                self.service.user_role_dao.assign_role = Mock(return_value=True)
                
                result = await self.service.assign_users(1, [1, 2])
                self.assertTrue(result)
        
        asyncio.run(test())
    
    def test_data_validation(self):
        """测试数据验证"""
        # 测试角色名称验证
        with self.assertRaises(DataValidationError):
            self.service._validate_role_name("A")  # 太短
        
        with self.assertRaises(DataValidationError):
            self.service._validate_role_name("角色<名称>")  # 包含特殊字符
        
        # 测试角色代码验证
        with self.assertRaises(DataValidationError):
            self.service._validate_role_code("123role")  # 数字开头
        
        with self.assertRaises(DataValidationError):
            self.service._validate_role_code("a" * 51)  # 太长
    
    def test_search_roles(self):
        """测试搜索角色"""
        async def test():
            mock_roles = [Mock(spec=Role), Mock(spec=Role)]
            
            self.service.role_dao.search_roles = Mock(return_value=mock_roles)
            
            result = await self.service.search_roles("管理", limit=10)
            self.assertEqual(len(result), 2)
            
            self.service.role_dao.search_roles.assert_called_once_with("管理", 10, 0)
        
        asyncio.run(test())
    
    def test_get_role_statistics(self):
        """测试获取角色统计"""
        async def test():
            mock_roles = [Mock(id=1, role_name="管理员", role_code="admin")]
            
            with patch.object(self.service, 'count_all', return_value=5), \
                 patch.object(self.service, 'find_all', return_value=mock_roles):
                
                self.service.role_dao.get_role_permissions = Mock(return_value=[])
                self.service.role_dao.get_role_users = Mock(return_value=[])
                
                result = await self.service.get_role_statistics()
                
                self.assertEqual(result['total_roles'], 5)
                self.assertIn('role_details', result)
        
        asyncio.run(test())


if __name__ == '__main__':
    unittest.main()
