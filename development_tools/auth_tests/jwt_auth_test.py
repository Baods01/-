#!/usr/bin/env python3
"""
JWT认证功能测试

按照第9轮检查提示词要求，全面测试JWT认证功能。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
import asyncio
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.middleware.auth_middleware import (
    get_current_user, get_current_active_user, verify_jwt_token,
    AuthenticationException, AuthorizationException
)
from fastapi.security import HTTPAuthorizationCredentials
from services.auth_service import AuthService
from models.user import User


class JWTAuthTester:
    """JWT认证功能测试器"""
    
    def __init__(self):
        self.test_secret = "test_jwt_secret_key_for_testing"
        self.results = []
    
    def create_test_token(self, payload: dict, expired: bool = False) -> str:
        """创建测试用JWT令牌"""
        if expired:
            payload['exp'] = datetime.utcnow() - timedelta(hours=1)  # 过期令牌
        else:
            payload['exp'] = datetime.utcnow() + timedelta(hours=1)  # 有效令牌
        
        return jwt.encode(payload, self.test_secret, algorithm='HS256')
    
    def create_invalid_token(self) -> str:
        """创建无效的JWT令牌"""
        return "invalid.jwt.token"
    
    def create_tampered_token(self, payload: dict) -> str:
        """创建被篡改的JWT令牌"""
        payload['exp'] = datetime.utcnow() + timedelta(hours=1)
        token = jwt.encode(payload, self.test_secret, algorithm='HS256')
        # 篡改令牌的最后几个字符
        return token[:-5] + "XXXXX"
    
    async def test_valid_token_verification(self) -> bool:
        """测试有效令牌的验证"""
        print("\n1. 测试有效令牌验证:")
        
        try:
            # 创建有效令牌
            payload = {
                'user_id': 1,
                'username': 'testuser',
                'roles': ['ROLE_USER']
            }
            valid_token = self.create_test_token(payload)
            
            # 模拟认证凭据
            credentials = Mock()
            credentials.credentials = valid_token
            
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.verify_token.return_value = payload
            mock_auth_service.get_current_user.return_value = Mock(
                id=1, username='testuser', status=1, is_active=lambda: True
            )
            
            # 测试get_current_user
            with patch('api.middleware.auth_middleware.verify_jwt_token') as mock_verify:
                mock_verify.return_value = payload
                
                user = await get_current_user(credentials, mock_auth_service)
                
                if user and user.username == 'testuser':
                    print("  ✅ 有效令牌验证通过")
                    return True
                else:
                    print("  ❌ 有效令牌验证失败")
                    return False
                    
        except Exception as e:
            print(f"  ❌ 有效令牌验证异常: {str(e)}")
            return False
    
    async def test_invalid_token_handling(self) -> bool:
        """测试无效令牌的处理"""
        print("\n2. 测试无效令牌处理:")
        
        try:
            # 创建无效令牌
            invalid_token = self.create_invalid_token()
            
            # 模拟认证凭据
            credentials = Mock()
            credentials.credentials = invalid_token
            
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.verify_token.side_effect = Exception("Invalid token")
            
            # 测试get_current_user应该抛出异常
            try:
                await get_current_user(credentials, mock_auth_service)
                print("  ❌ 无效令牌未被正确拒绝")
                return False
            except AuthenticationException:
                print("  ✅ 无效令牌正确被拒绝")
                return True
                
        except Exception as e:
            print(f"  ❌ 无效令牌处理异常: {str(e)}")
            return False
    
    async def test_expired_token_handling(self) -> bool:
        """测试过期令牌的处理"""
        print("\n3. 测试过期令牌处理:")
        
        try:
            # 创建过期令牌
            payload = {
                'user_id': 1,
                'username': 'testuser',
                'roles': ['ROLE_USER']
            }
            expired_token = self.create_test_token(payload, expired=True)
            
            # 模拟认证凭据
            credentials = Mock()
            credentials.credentials = expired_token
            
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.verify_token.side_effect = jwt.ExpiredSignatureError("Token expired")
            
            # 测试get_current_user应该抛出异常
            try:
                await get_current_user(credentials, mock_auth_service)
                print("  ❌ 过期令牌未被正确拒绝")
                return False
            except AuthenticationException:
                print("  ✅ 过期令牌正确被拒绝")
                return True
                
        except Exception as e:
            print(f"  ❌ 过期令牌处理异常: {str(e)}")
            return False
    
    async def test_user_status_check(self) -> bool:
        """测试用户状态检查"""
        print("\n4. 测试用户状态检查:")
        
        try:
            # 创建非活跃用户
            inactive_user = Mock()
            inactive_user.is_active.return_value = False
            inactive_user.status = 0  # 禁用状态
            
            # 测试get_current_active_user应该抛出异常
            try:
                await get_current_active_user(inactive_user)
                print("  ❌ 非活跃用户未被正确拒绝")
                return False
            except AuthenticationException:
                print("  ✅ 非活跃用户正确被拒绝")
                
            # 测试活跃用户
            active_user = Mock()
            active_user.is_active.return_value = True
            active_user.status = 1  # 启用状态
            
            result = await get_current_active_user(active_user)
            if result == active_user:
                print("  ✅ 活跃用户正确通过")
                return True
            else:
                print("  ❌ 活跃用户验证失败")
                return False
                
        except Exception as e:
            print(f"  ❌ 用户状态检查异常: {str(e)}")
            return False
    
    async def test_token_parsing(self) -> bool:
        """测试令牌解析功能"""
        print("\n5. 测试令牌解析功能:")
        
        try:
            # 创建有效令牌
            payload = {
                'user_id': 1,
                'username': 'testuser',
                'roles': ['ROLE_USER']
            }
            valid_token = self.create_test_token(payload)
            
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.verify_token.return_value = payload
            
            # 测试verify_jwt_token
            result = await verify_jwt_token(valid_token, mock_auth_service)
            
            if result and result.get('user_id') == 1:
                print("  ✅ 令牌解析功能正常")
                return True
            else:
                print("  ❌ 令牌解析功能异常")
                return False
                
        except Exception as e:
            print(f"  ❌ 令牌解析功能异常: {str(e)}")
            return False
    
    async def test_missing_credentials(self) -> bool:
        """测试缺少认证凭据的处理"""
        print("\n6. 测试缺少认证凭据处理:")
        
        try:
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            
            # 测试None凭据
            try:
                await get_current_user(None, mock_auth_service)
                print("  ❌ 缺少凭据未被正确拒绝")
                return False
            except AuthenticationException:
                print("  ✅ 缺少凭据正确被拒绝")
                return True
                
        except Exception as e:
            print(f"  ❌ 缺少认证凭据处理异常: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有JWT认证功能测试"""
        print("🔍 JWT认证功能测试")
        print("=" * 50)
        
        test_functions = [
            ("有效令牌验证", self.test_valid_token_verification),
            ("无效令牌处理", self.test_invalid_token_handling),
            ("过期令牌处理", self.test_expired_token_handling),
            ("用户状态检查", self.test_user_status_check),
            ("令牌解析功能", self.test_token_parsing),
            ("缺少认证凭据处理", self.test_missing_credentials),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            try:
                if await test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"  ❌ {test_name}测试异常: {str(e)}")
        
        # 输出测试结果汇总
        print("\n" + "=" * 50)
        print("📊 JWT认证功能测试结果汇总:")
        print()
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        
        pass_rate = (passed_tests / total_tests) * 100
        print(f"通过率: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("🎉 JWT认证功能测试优秀！")
        elif pass_rate >= 80:
            print("✅ JWT认证功能测试良好！")
        else:
            print("❌ JWT认证功能需要改进。")
        
        return pass_rate >= 80


async def main():
    """主函数"""
    tester = JWTAuthTester()
    success = await tester.run_all_tests()
    
    if success:
        print("✅ JWT认证功能测试通过！")
        return 0
    else:
        print("❌ JWT认证功能测试未通过，需要修复问题。")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
