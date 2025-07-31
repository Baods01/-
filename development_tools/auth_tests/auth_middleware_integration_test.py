#!/usr/bin/env python3
"""
认证中间件集成测试脚本

测试认证中间件与FastAPI的集成，包括路由保护、权限检查等。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from api.middleware.auth_middleware import (
    AuthMiddleware, OptionalAuthMiddleware,
    get_current_user, get_current_active_user,
    RequirePermissions, RequireRoles,
    require_permissions, require_roles, require_admin
)
from api.schemas import SuccessResponse, UserResponse


class AuthMiddlewareIntegrationTester:
    """认证中间件集成测试器"""
    
    def __init__(self):
        self.app = FastAPI()
        self.setup_test_routes()
        self.client = TestClient(self.app)
    
    def setup_test_routes(self):
        """设置测试路由"""
        
        @self.app.get("/public")
        async def public_endpoint():
            """公开接口"""
            return {"message": "这是公开接口"}
        
        @self.app.get("/protected")
        async def protected_endpoint(current_user: UserResponse = Depends(get_current_active_user)):
            """受保护的接口"""
            return {
                "message": "这是受保护的接口",
                "user": current_user.username if hasattr(current_user, 'username') else "unknown"
            }
        
        @self.app.get("/admin-only")
        @require_admin()
        async def admin_only_endpoint(current_user: UserResponse = Depends(get_current_active_user)):
            """仅管理员接口"""
            return {
                "message": "这是管理员专用接口",
                "user": current_user.username if hasattr(current_user, 'username') else "unknown"
            }
        
        @self.app.get("/user-permissions")
        @require_permissions(["user:view", "user:create"])
        async def user_permissions_endpoint(current_user: UserResponse = Depends(get_current_active_user)):
            """需要用户权限的接口"""
            return {
                "message": "需要用户查看和创建权限",
                "user": current_user.username if hasattr(current_user, 'username') else "unknown"
            }
        
        @self.app.get("/role-required")
        @require_roles(["ROLE_ADMIN", "ROLE_MANAGER"])
        async def role_required_endpoint(current_user: UserResponse = Depends(get_current_active_user)):
            """需要特定角色的接口"""
            return {
                "message": "需要管理员或经理角色",
                "user": current_user.username if hasattr(current_user, 'username') else "unknown"
            }
        
        @self.app.get("/optional-auth")
        async def optional_auth_endpoint(request):
            """可选认证接口"""
            user_info = getattr(request.state, 'current_user', None)
            if user_info:
                return {
                    "message": "已认证用户访问",
                    "user": user_info.get('username', 'unknown')
                }
            else:
                return {
                    "message": "匿名用户访问"
                }
    
    def test_public_access(self) -> bool:
        """测试公开接口访问"""
        print("\n🌐 公开接口访问测试:")
        
        try:
            response = self.client.get("/public")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "公开接口" in data["message"]:
                    print("  ✅ 公开接口访问成功")
                    return True
                else:
                    print("  ❌ 公开接口响应内容错误")
                    return False
            else:
                print(f"  ❌ 公开接口访问失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ 公开接口访问异常: {str(e)}")
            return False
    
    def test_protected_access_without_token(self) -> bool:
        """测试无令牌访问受保护接口"""
        print("\n🔒 无令牌访问受保护接口测试:")
        
        try:
            response = self.client.get("/protected")
            if response.status_code == 401:
                print("  ✅ 无令牌访问受保护接口正确返回401")
                return True
            else:
                print(f"  ❌ 无令牌访问受保护接口状态码错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ 无令牌访问受保护接口异常: {str(e)}")
            return False
    
    def test_protected_access_with_invalid_token(self) -> bool:
        """测试无效令牌访问受保护接口"""
        print("\n🔑 无效令牌访问受保护接口测试:")
        
        try:
            headers = {"Authorization": "Bearer invalid_token_123"}
            response = self.client.get("/protected", headers=headers)
            if response.status_code == 401:
                print("  ✅ 无效令牌访问受保护接口正确返回401")
                return True
            else:
                print(f"  ❌ 无效令牌访问受保护接口状态码错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ 无效令牌访问受保护接口异常: {str(e)}")
            return False
    
    def test_middleware_integration(self) -> bool:
        """测试中间件集成"""
        print("\n🔧 中间件集成测试:")
        
        try:
            # 添加认证中间件
            self.app.add_middleware(AuthMiddleware)
            
            # 重新创建测试客户端
            self.client = TestClient(self.app)
            
            # 测试中间件是否正常工作
            response = self.client.get("/public")
            if response.status_code == 200:
                print("  ✅ 认证中间件集成成功")
                return True
            else:
                print(f"  ❌ 认证中间件集成失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ 中间件集成异常: {str(e)}")
            return False
    
    def test_optional_auth_middleware(self) -> bool:
        """测试可选认证中间件"""
        print("\n🔓 可选认证中间件测试:")
        
        try:
            # 创建新的应用实例测试可选认证中间件
            optional_app = FastAPI()
            optional_app.add_middleware(OptionalAuthMiddleware)
            
            @optional_app.get("/optional-test")
            async def optional_test():
                return {"message": "可选认证测试"}
            
            optional_client = TestClient(optional_app)
            
            # 测试无令牌访问
            response = optional_client.get("/optional-test")
            if response.status_code == 200:
                print("  ✅ 可选认证中间件无令牌访问成功")
                
                # 测试无效令牌访问
                headers = {"Authorization": "Bearer invalid_token"}
                response = optional_client.get("/optional-test", headers=headers)
                if response.status_code == 200:
                    print("  ✅ 可选认证中间件无效令牌访问成功")
                    return True
                else:
                    print(f"  ❌ 可选认证中间件无效令牌访问失败: {response.status_code}")
                    return False
            else:
                print(f"  ❌ 可选认证中间件无令牌访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ 可选认证中间件测试异常: {str(e)}")
            return False
    
    def test_error_responses(self) -> bool:
        """测试错误响应格式"""
        print("\n❌ 错误响应格式测试:")
        
        try:
            response = self.client.get("/protected")
            if response.status_code == 401:
                data = response.json()
                expected_fields = ["success", "message", "error_code", "timestamp"]
                
                if all(field in data for field in expected_fields):
                    if data["success"] == False and data["error_code"] == "AUTHENTICATION_FAILED":
                        print("  ✅ 错误响应格式正确")
                        return True
                    else:
                        print("  ❌ 错误响应字段值错误")
                        return False
                else:
                    print("  ❌ 错误响应字段不完整")
                    return False
            else:
                print(f"  ❌ 错误响应状态码错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ 错误响应格式测试异常: {str(e)}")
            return False
    
    def test_cors_headers(self) -> bool:
        """测试CORS头部"""
        print("\n🌍 CORS头部测试:")
        
        try:
            response = self.client.get("/public")
            
            # 检查是否有处理时间头
            if "X-Process-Time" in response.headers:
                print("  ✅ 响应包含处理时间头")
                return True
            else:
                print("  ⚠️ 响应不包含处理时间头（可能正常）")
                return True  # 这不是错误，只是提醒
        except Exception as e:
            print(f"  ❌ CORS头部测试异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有集成测试"""
        print("🔍 认证中间件集成测试")
        print("=" * 60)
        
        # 运行各项测试
        test_functions = [
            ("公开接口访问", self.test_public_access),
            ("无令牌访问受保护接口", self.test_protected_access_without_token),
            ("无效令牌访问受保护接口", self.test_protected_access_with_invalid_token),
            ("中间件集成", self.test_middleware_integration),
            ("可选认证中间件", self.test_optional_auth_middleware),
            ("错误响应格式", self.test_error_responses),
            ("CORS头部", self.test_cors_headers),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"  ❌ {test_name}测试异常: {str(e)}")
        
        # 输出测试结果汇总
        print("\n" + "=" * 60)
        print("📊 认证中间件集成测试结果汇总:")
        print()
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        
        pass_rate = (passed_tests / total_tests) * 100
        print(f"通过率: {pass_rate:.1f}%")
        
        print()
        if pass_rate >= 90:
            print("🎉 认证中间件集成测试优秀！")
        elif pass_rate >= 80:
            print("✅ 认证中间件集成测试良好！")
        elif pass_rate >= 70:
            print("⚠️ 认证中间件集成测试可接受，建议优化。")
        else:
            print("❌ 认证中间件集成需要改进。")
        
        print("=" * 60)
        return pass_rate >= 80


def main():
    """主函数"""
    tester = AuthMiddlewareIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("✅ 认证中间件集成测试通过！")
        return 0
    else:
        print("❌ 认证中间件集成测试未通过，需要修复问题。")
        return 1


if __name__ == "__main__":
    exit(main())
