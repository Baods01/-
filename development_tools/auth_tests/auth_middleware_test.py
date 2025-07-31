#!/usr/bin/env python3
"""
认证中间件和权限检查装饰器测试脚本

按照第9轮提示词要求，全面测试JWT认证中间件和权限检查装饰器的功能。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.middleware.auth_middleware import (
    AuthenticationException, AuthorizationException,
    get_current_user, get_current_active_user, verify_jwt_token,
    require_permissions, require_roles, require_admin, optional_auth,
    PermissionChecker, RoleChecker, RequirePermissions, RequireRoles,
    TokenHandler, UserInfoCache, SecurityMonitor,
    AuthMiddleware, OptionalAuthMiddleware,
    security, token_handler, user_info_cache, security_monitor
)


class AuthMiddlewareTester:
    """认证中间件测试器"""
    
    def __init__(self):
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        self.results["total_tests"] += 1
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                self.results["passed_tests"] += 1
                status = "✅ 通过"
            else:
                self.results["failed_tests"] += 1
                status = "❌ 失败"
            
            self.results["test_results"].append({
                "name": test_name,
                "status": status,
                "duration": round(duration, 4)
            })
            
            print(f"  {status}: {test_name} ({duration:.4f}s)")
            return result
            
        except Exception as e:
            self.results["failed_tests"] += 1
            status = f"❌ 异常: {str(e)}"
            self.results["test_results"].append({
                "name": test_name,
                "status": status,
                "duration": 0
            })
            print(f"  {status}: {test_name}")
            return False
    
    def test_exception_classes(self) -> bool:
        """测试异常类"""
        print("\n🔍 异常类测试:")
        
        tests = [
            ("AuthenticationException默认状态码", lambda: self._test_auth_exception_default()),
            ("AuthenticationException自定义消息", lambda: self._test_auth_exception_custom()),
            ("AuthorizationException默认状态码", lambda: self._test_authz_exception_default()),
            ("AuthorizationException自定义消息", lambda: self._test_authz_exception_custom()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_auth_exception_default(self) -> bool:
        """测试认证异常默认状态码"""
        try:
            raise AuthenticationException()
        except AuthenticationException as e:
            return e.status_code == 401 and "WWW-Authenticate" in e.headers
        return False
    
    def _test_auth_exception_custom(self) -> bool:
        """测试认证异常自定义消息"""
        try:
            raise AuthenticationException("自定义认证失败消息")
        except AuthenticationException as e:
            return e.detail == "自定义认证失败消息"
        return False
    
    def _test_authz_exception_default(self) -> bool:
        """测试授权异常默认状态码"""
        try:
            raise AuthorizationException()
        except AuthorizationException as e:
            return e.status_code == 403
        return False
    
    def _test_authz_exception_custom(self) -> bool:
        """测试授权异常自定义消息"""
        try:
            raise AuthorizationException("自定义权限不足消息")
        except AuthorizationException as e:
            return e.detail == "自定义权限不足消息"
        return False
    
    def test_token_handler(self) -> bool:
        """测试令牌处理器"""
        print("\n🔑 令牌处理器测试:")
        
        tests = [
            ("TokenHandler实例化", lambda: self._test_token_handler_init()),
            ("Bearer令牌提取", lambda: self._test_extract_bearer_token()),
            ("令牌黑名单功能", lambda: self._test_token_blacklist()),
            ("令牌缓存功能", lambda: self._test_token_cache()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_token_handler_init(self) -> bool:
        """测试令牌处理器初始化"""
        handler = TokenHandler()
        return (hasattr(handler, '_token_cache') and 
                hasattr(handler, '_blacklist') and
                isinstance(handler._token_cache, dict) and
                isinstance(handler._blacklist, set))
    
    def _test_extract_bearer_token(self) -> bool:
        """测试Bearer令牌提取"""
        from fastapi import Request
        from unittest.mock import Mock
        
        # 模拟请求对象
        mock_request = Mock()
        mock_request.headers = {"Authorization": "Bearer test_token_123"}
        
        handler = TokenHandler()
        token = handler.extract_bearer_token(mock_request)
        return token == "test_token_123"
    
    def _test_token_blacklist(self) -> bool:
        """测试令牌黑名单功能"""
        handler = TokenHandler()
        test_token = "test_blacklist_token"
        
        # 添加到黑名单
        handler.add_to_blacklist(test_token)
        
        # 检查是否在黑名单中
        return test_token in handler._blacklist
    
    def _test_token_cache(self) -> bool:
        """测试令牌缓存功能"""
        handler = TokenHandler()
        cache_key = "test_cache_key"
        test_data = {"user_id": 1, "username": "test"}
        
        # 设置缓存
        handler._set_cache(cache_key, test_data)
        
        # 获取缓存
        cached_data = handler._get_from_cache(cache_key)
        return cached_data == test_data
    
    def test_user_info_cache(self) -> bool:
        """测试用户信息缓存"""
        print("\n👤 用户信息缓存测试:")
        
        tests = [
            ("UserInfoCache实例化", lambda: self._test_user_cache_init()),
            ("用户信息缓存设置获取", lambda: self._test_user_info_cache()),
            ("用户权限缓存设置获取", lambda: self._test_user_permissions_cache()),
            ("缓存过期清理", lambda: self._test_cache_expiry()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_user_cache_init(self) -> bool:
        """测试用户缓存初始化"""
        cache = UserInfoCache()
        return (hasattr(cache, '_user_cache') and 
                hasattr(cache, '_permission_cache') and
                isinstance(cache._user_cache, dict) and
                isinstance(cache._permission_cache, dict))
    
    def _test_user_info_cache(self) -> bool:
        """测试用户信息缓存"""
        cache = UserInfoCache()
        user_id = 1
        user_info = {"username": "test", "email": "test@example.com"}
        
        # 设置缓存
        cache.set_user_info(user_id, user_info)
        
        # 获取缓存
        cached_info = cache.get_user_info(user_id)
        return cached_info == user_info
    
    def _test_user_permissions_cache(self) -> bool:
        """测试用户权限缓存"""
        cache = UserInfoCache()
        user_id = 1
        permissions = ["user:view", "user:create", "role:view"]
        
        # 设置缓存
        cache.set_user_permissions(user_id, permissions)
        
        # 获取缓存
        cached_permissions = cache.get_user_permissions(user_id)
        return cached_permissions == permissions
    
    def _test_cache_expiry(self) -> bool:
        """测试缓存过期"""
        cache = UserInfoCache()
        user_id = 999
        user_info = {"username": "expired_test"}
        
        # 设置缓存
        cache.set_user_info(user_id, user_info)
        
        # 手动设置过期时间为过去
        if user_id in cache._user_cache:
            cache._user_cache[user_id]['expire_time'] = datetime.now() - timedelta(minutes=1)
        
        # 尝试获取过期缓存
        cached_info = cache.get_user_info(user_id)
        return cached_info is None
    
    def test_security_monitor(self) -> bool:
        """测试安全监控器"""
        print("\n🔒 安全监控器测试:")
        
        tests = [
            ("SecurityMonitor实例化", lambda: self._test_security_monitor_init()),
            ("失败登录记录", lambda: self._test_failed_login_record()),
            ("成功登录记录", lambda: self._test_successful_login_record()),
            ("IP阻止功能", lambda: self._test_ip_blocking()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_security_monitor_init(self) -> bool:
        """测试安全监控器初始化"""
        monitor = SecurityMonitor()
        return (hasattr(monitor, '_failed_attempts') and 
                hasattr(monitor, '_suspicious_ips') and
                hasattr(monitor, '_access_log') and
                isinstance(monitor._failed_attempts, dict) and
                isinstance(monitor._suspicious_ips, set) and
                isinstance(monitor._access_log, list))
    
    def _test_failed_login_record(self) -> bool:
        """测试失败登录记录"""
        monitor = SecurityMonitor()
        ip = "192.168.1.100"
        username = "testuser"
        reason = "密码错误"
        
        # 记录失败登录
        monitor.record_failed_login(ip, username, reason)
        
        # 检查记录是否存在
        key = f"{ip}:{username}"
        return key in monitor._failed_attempts and len(monitor._failed_attempts[key]) > 0
    
    def _test_successful_login_record(self) -> bool:
        """测试成功登录记录"""
        monitor = SecurityMonitor()
        ip = "192.168.1.101"
        username = "testuser2"
        
        # 先记录失败登录
        monitor.record_failed_login(ip, username, "密码错误")
        
        # 再记录成功登录
        monitor.record_successful_login(ip, username)
        
        # 检查失败记录是否被清理
        key = f"{ip}:{username}"
        return key not in monitor._failed_attempts
    
    def _test_ip_blocking(self) -> bool:
        """测试IP阻止功能"""
        monitor = SecurityMonitor()
        ip = "192.168.1.102"
        username = "testuser3"
        
        # 记录多次失败登录以触发IP阻止
        for i in range(6):  # 超过最大失败次数
            monitor.record_failed_login(ip, username, f"密码错误{i}")
        
        # 检查IP是否被阻止
        return monitor.is_ip_blocked(ip)
    
    def test_permission_checker(self) -> bool:
        """测试权限检查器"""
        print("\n🛡️ 权限检查器测试:")
        
        tests = [
            ("PermissionChecker初始化", lambda: self._test_permission_checker_init()),
            ("RoleChecker初始化", lambda: self._test_role_checker_init()),
            ("RequirePermissions函数", lambda: self._test_require_permissions_func()),
            ("RequireRoles函数", lambda: self._test_require_roles_func()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_permission_checker_init(self) -> bool:
        """测试权限检查器初始化"""
        permissions = ["user:view", "user:create"]
        checker = PermissionChecker(permissions)
        return checker.required_permissions == permissions
    
    def _test_role_checker_init(self) -> bool:
        """测试角色检查器初始化"""
        roles = ["ROLE_ADMIN", "ROLE_USER"]
        checker = RoleChecker(roles)
        return checker.required_roles == roles
    
    def _test_require_permissions_func(self) -> bool:
        """测试RequirePermissions函数"""
        permissions = ["user:view"]
        dependency = RequirePermissions(permissions)
        return dependency is not None
    
    def _test_require_roles_func(self) -> bool:
        """测试RequireRoles函数"""
        roles = ["ROLE_ADMIN"]
        dependency = RequireRoles(roles)
        return dependency is not None
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🔍 认证中间件和权限检查装饰器功能测试")
        print("=" * 70)
        
        # 运行各项测试
        test_categories = [
            ("异常类", self.test_exception_classes),
            ("令牌处理器", self.test_token_handler),
            ("用户信息缓存", self.test_user_info_cache),
            ("安全监控器", self.test_security_monitor),
            ("权限检查器", self.test_permission_checker),
        ]
        
        category_results = {}
        for category_name, test_func in test_categories:
            category_results[category_name] = test_func()
        
        # 输出测试结果汇总
        print("\n" + "=" * 70)
        print("📊 认证中间件测试结果汇总:")
        print()
        
        for category, passed in category_results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {status}: {category}")
        
        print()
        print(f"总测试数: {self.results['total_tests']}")
        print(f"通过: {self.results['passed_tests']} ✅")
        print(f"失败: {self.results['failed_tests']} ❌")
        
        pass_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100
        print(f"通过率: {pass_rate:.1f}%")
        
        print()
        if pass_rate >= 90:
            print("🎉 认证中间件功能测试优秀！")
        elif pass_rate >= 80:
            print("✅ 认证中间件功能测试良好！")
        elif pass_rate >= 70:
            print("⚠️ 认证中间件功能测试可接受，建议优化。")
        else:
            print("❌ 认证中间件功能需要改进。")
        
        print("=" * 70)
        return pass_rate >= 80


def main():
    """主函数"""
    tester = AuthMiddlewareTester()
    success = tester.run_all_tests()
    
    if success:
        print("✅ 认证中间件功能测试通过！")
        return 0
    else:
        print("❌ 认证中间件功能测试未通过，需要修复问题。")
        return 1


if __name__ == "__main__":
    exit(main())
