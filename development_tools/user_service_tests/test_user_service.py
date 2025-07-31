#!/usr/bin/env python3
"""
RBAC权限系统 - 用户服务测试

本文件包含UserService用户业务服务类的单元测试，
验证用户注册、认证、权限管理等功能。

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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.user_service import UserService
from services.exceptions import (
    AuthenticationError,
    DataValidationError,
    DuplicateResourceError,
    ResourceNotFoundError
)
from models.user import User


class TestUserService(unittest.TestCase):
    """UserService测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟会话
        self.mock_session = Mock()
        
        # 创建测试服务实例
        with patch('services.user_service.UserDao'), \
             patch('services.user_service.PasswordUtils'):
            self.service = UserService(session=self.mock_session)
            
            # 设置模拟对象
            self.service.user_dao = Mock()
            self.service.password_utils = Mock()
    
    def tearDown(self):
        """测试后清理"""
        self.service.close()
    
    def test_create_user_success(self):
        """测试成功创建用户"""
        async def test():
            # 设置模拟返回值
            self.service.user_dao.find_by_username.return_value = None
            self.service.user_dao.find_by_email.return_value = None
            self.service.password_utils.check_password_strength.return_value = (True, "强密码")
            self.service.password_utils.hash_password.return_value = "hashed_password"
            
            # 模拟用户对象
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.validate.return_value = True
            
            with patch.object(self.service, 'save_entity', return_value=mock_user):
                # 执行测试
                result = await self.service.create_user(
                    "testuser", 
                    "test@example.com", 
                    "TestPass123!"
                )
                
                # 验证结果
                self.assertEqual(result, mock_user)
                self.service.password_utils.hash_password.assert_called_once_with("TestPass123!")
        
        asyncio.run(test())
    
    def test_create_user_duplicate_username(self):
        """测试用户名重复"""
        async def test():
            # 设置模拟返回值 - 用户名已存在
            existing_user = Mock(spec=User)
            existing_user.id = 1
            self.service.user_dao.find_by_username.return_value = existing_user
            
            # 执行测试并验证异常
            with self.assertRaises(DuplicateResourceError) as context:
                await self.service.create_user(
                    "existinguser", 
                    "test@example.com", 
                    "TestPass123!"
                )
            
            self.assertIn("用户名", str(context.exception))
        
        asyncio.run(test())
    
    def test_create_user_duplicate_email(self):
        """测试邮箱重复"""
        async def test():
            # 设置模拟返回值 - 邮箱已存在
            self.service.user_dao.find_by_username.return_value = None
            existing_user = Mock(spec=User)
            existing_user.id = 1
            self.service.user_dao.find_by_email.return_value = existing_user
            
            # 执行测试并验证异常
            with self.assertRaises(DuplicateResourceError) as context:
                await self.service.create_user(
                    "testuser", 
                    "existing@example.com", 
                    "TestPass123!"
                )
            
            self.assertIn("邮箱", str(context.exception))
        
        asyncio.run(test())
    
    def test_create_user_weak_password(self):
        """测试弱密码"""
        async def test():
            # 设置模拟返回值
            self.service.user_dao.find_by_username.return_value = None
            self.service.user_dao.find_by_email.return_value = None
            self.service.password_utils.check_password_strength.return_value = (False, "密码太弱")
            
            # 执行测试并验证异常
            with self.assertRaises(DataValidationError) as context:
                await self.service.create_user(
                    "testuser", 
                    "test@example.com", 
                    "weak"
                )
            
            self.assertIn("密码强度不足", str(context.exception))
        
        asyncio.run(test())
    
    def test_authenticate_user_success(self):
        """测试成功认证"""
        async def test():
            # 设置模拟用户
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.is_active.return_value = True
            mock_user.password_hash = "hashed_password"
            
            self.service.user_dao.find_by_username.return_value = mock_user
            self.service.password_utils.verify_password.return_value = True
            
            # 执行测试
            result = await self.service.authenticate_user("testuser", "password")
            
            # 验证结果
            self.assertEqual(result, mock_user)
            self.service.password_utils.verify_password.assert_called_once_with(
                "password", "hashed_password"
            )
        
        asyncio.run(test())
    
    def test_authenticate_user_not_found(self):
        """测试用户不存在"""
        async def test():
            # 设置模拟返回值
            self.service.user_dao.find_by_username.return_value = None
            
            # 执行测试并验证异常
            with self.assertRaises(AuthenticationError) as context:
                await self.service.authenticate_user("nonexistent", "password")
            
            self.assertIn("用户名或密码错误", str(context.exception))
        
        asyncio.run(test())
    
    def test_authenticate_user_inactive(self):
        """测试用户已禁用"""
        async def test():
            # 设置模拟用户 - 已禁用
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.is_active.return_value = False
            
            self.service.user_dao.find_by_username.return_value = mock_user
            
            # 执行测试并验证异常
            with self.assertRaises(AuthenticationError) as context:
                await self.service.authenticate_user("testuser", "password")
            
            self.assertIn("已被禁用", str(context.exception))
        
        asyncio.run(test())
    
    def test_authenticate_user_wrong_password(self):
        """测试密码错误"""
        async def test():
            # 设置模拟用户
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.is_active.return_value = True
            mock_user.password_hash = "hashed_password"
            
            self.service.user_dao.find_by_username.return_value = mock_user
            self.service.password_utils.verify_password.return_value = False
            
            # 执行测试并验证异常
            with self.assertRaises(AuthenticationError) as context:
                await self.service.authenticate_user("testuser", "wrongpassword")
            
            self.assertIn("用户名或密码错误", str(context.exception))
        
        asyncio.run(test())
    
    def test_change_password_success(self):
        """测试成功修改密码"""
        async def test():
            # 设置模拟用户
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.password_hash = "old_hashed_password"
            
            with patch.object(self.service, 'get_by_id', return_value=mock_user):
                self.service.password_utils.verify_password.side_effect = [True, False]  # 旧密码正确，新密码不同
                self.service.password_utils.check_password_strength.return_value = (True, "强密码")
                self.service.password_utils.hash_password.return_value = "new_hashed_password"
                
                # 执行测试
                result = await self.service.change_password(1, "oldpass", "newpass")
                
                # 验证结果
                self.assertTrue(result)
                mock_user.set_password_hash.assert_called_once_with("new_hashed_password")
        
        asyncio.run(test())
    
    def test_change_password_wrong_old_password(self):
        """测试旧密码错误"""
        async def test():
            # 设置模拟用户
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.password_hash = "hashed_password"
            
            with patch.object(self.service, 'get_by_id', return_value=mock_user):
                self.service.password_utils.verify_password.return_value = False
                
                # 执行测试并验证异常
                with self.assertRaises(AuthenticationError) as context:
                    await self.service.change_password(1, "wrongoldpass", "newpass")
                
                self.assertIn("旧密码验证失败", str(context.exception))
        
        asyncio.run(test())
    
    def test_enable_user_success(self):
        """测试成功启用用户"""
        async def test():
            # 设置模拟用户
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.is_active.return_value = False
            
            with patch.object(self.service, 'get_by_id', return_value=mock_user):
                self.service.user_dao.activate_user.return_value = True
                
                # 执行测试
                result = await self.service.enable_user(1)
                
                # 验证结果
                self.assertTrue(result)
                self.service.user_dao.activate_user.assert_called_once_with(1)
        
        asyncio.run(test())
    
    def test_disable_user_success(self):
        """测试成功禁用用户"""
        async def test():
            # 设置模拟用户
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.is_active.return_value = True
            
            with patch.object(self.service, 'get_by_id', return_value=mock_user):
                self.service.user_dao.deactivate_user.return_value = True
                
                # 执行测试
                result = await self.service.disable_user(1)
                
                # 验证结果
                self.assertTrue(result)
                self.service.user_dao.deactivate_user.assert_called_once_with(1)
        
        asyncio.run(test())
    
    def test_get_user_permissions(self):
        """测试获取用户权限"""
        async def test():
            # 设置模拟用户和权限
            mock_user = Mock(spec=User)
            mock_user.id = 1
            
            mock_permissions = [
                Mock(permission_code="read_user"),
                Mock(permission_code="write_user")
            ]
            
            with patch.object(self.service, 'get_by_id', return_value=mock_user):
                self.service.user_dao.get_user_permissions.return_value = mock_permissions
                
                # 执行测试
                result = await self.service.get_user_permissions(1)
                
                # 验证结果
                self.assertEqual(result, ["read_user", "write_user"])
        
        asyncio.run(test())
    
    def test_data_validation(self):
        """测试数据验证"""
        # 测试用户名验证
        with self.assertRaises(DataValidationError):
            self.service._validate_username("ab")  # 太短
        
        with self.assertRaises(DataValidationError):
            self.service._validate_username("123user")  # 数字开头
        
        # 测试邮箱验证
        with self.assertRaises(DataValidationError):
            self.service._validate_email("invalid-email")  # 格式错误
        
        with self.assertRaises(DataValidationError):
            self.service._validate_email("a" * 60 + "@example.com")  # 太长


if __name__ == '__main__':
    unittest.main()
