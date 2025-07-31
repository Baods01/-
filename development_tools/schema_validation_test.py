#!/usr/bin/env python3
"""
数据模式定义完整性和正确性检查脚本

按照第8轮检查提示词要求，全面检查数据模式定义。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserDetailResponse,
    RoleCreateRequest, RoleResponse, PermissionCreateRequest, PermissionResponse,
    LoginRequest, LoginResponse, SuccessResponse, ErrorResponse
)
from pydantic import ValidationError


class SchemaValidationTester:
    """数据模式验证测试器"""
    
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
    
    def test_string_length_validation(self) -> bool:
        """测试字符串长度验证"""
        print("\n📏 字符串长度验证测试:")
        
        tests = [
            ("用户名最小长度验证", lambda: self._test_username_min_length()),
            ("用户名最大长度验证", lambda: self._test_username_max_length()),
            ("密码最小长度验证", lambda: self._test_password_min_length()),
            ("角色名称长度验证", lambda: self._test_role_name_length()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_username_min_length(self) -> bool:
        """测试用户名最小长度"""
        try:
            UserCreateRequest(username='ab', email='test@example.com', password='Test123!')
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def _test_username_max_length(self) -> bool:
        """测试用户名最大长度"""
        try:
            UserCreateRequest(username='a' * 51, email='test@example.com', password='Test123!')
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def _test_password_min_length(self) -> bool:
        """测试密码最小长度"""
        try:
            UserCreateRequest(username='testuser', email='test@example.com', password='123')
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def _test_role_name_length(self) -> bool:
        """测试角色名称长度"""
        try:
            RoleCreateRequest(name='a', code='ROLE_TEST')  # 名称太短
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def test_regex_validation(self) -> bool:
        """测试正则表达式验证"""
        print("\n🔤 正则表达式验证测试:")
        
        tests = [
            ("用户名格式验证", lambda: self._test_username_format()),
            ("角色代码格式验证", lambda: self._test_role_code_format()),
            ("权限代码格式验证", lambda: self._test_permission_code_format()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_username_format(self) -> bool:
        """测试用户名格式"""
        try:
            UserCreateRequest(username='test@user', email='test@example.com', password='Test123!')
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def _test_role_code_format(self) -> bool:
        """测试角色代码格式"""
        try:
            RoleCreateRequest(name='测试角色', code='invalid_code')
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def _test_permission_code_format(self) -> bool:
        """测试权限代码格式"""
        try:
            PermissionCreateRequest(
                name='测试权限', 
                code='invalid_format',
                resource_type='user',
                action_type='view'
            )
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def test_serialization(self) -> bool:
        """测试序列化功能"""
        print("\n🔄 序列化测试:")
        
        tests = [
            ("用户模型序列化", lambda: self._test_user_serialization()),
            ("角色模型序列化", lambda: self._test_role_serialization()),
            ("日期时间格式化", lambda: self._test_datetime_serialization()),
            ("嵌套对象序列化", lambda: self._test_nested_serialization()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_user_serialization(self) -> bool:
        """测试用户模型序列化"""
        try:
            user_data = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'nickname': '测试用户',
                'phone': '13800138000',
                'status': 1,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_login_at': datetime.now()
            }
            
            user_response = UserResponse(**user_data)
            json_str = user_response.model_dump_json()
            return len(json_str) > 0
        except Exception:
            return False
    
    def _test_role_serialization(self) -> bool:
        """测试角色模型序列化"""
        try:
            role_data = {
                'id': 1,
                'name': '系统管理员',
                'code': 'ROLE_ADMIN',
                'description': '系统管理员角色',
                'status': 1,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            role_response = RoleResponse(**role_data)
            json_str = role_response.model_dump_json()
            return len(json_str) > 0
        except Exception:
            return False
    
    def _test_datetime_serialization(self) -> bool:
        """测试日期时间序列化"""
        try:
            user_data = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'nickname': '测试用户',
                'phone': None,
                'status': 1,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_login_at': None
            }
            
            user_response = UserResponse(**user_data)
            json_str = user_response.model_dump_json()
            data = json.loads(json_str)
            
            # 检查日期时间是否为字符串格式
            return isinstance(data['created_at'], str)
        except Exception:
            return False
    
    def _test_nested_serialization(self) -> bool:
        """测试嵌套对象序列化"""
        try:
            user_detail_data = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'nickname': '测试用户',
                'phone': '13800138000',
                'status': 1,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_login_at': datetime.now(),
                'roles': ['admin', 'user'],
                'permissions': ['user:view', 'user:create'],
                'login_count': 10
            }
            
            user_detail_response = UserDetailResponse(**user_detail_data)
            json_str = user_detail_response.model_dump_json()
            data = json.loads(json_str)
            
            return isinstance(data['roles'], list) and len(data['roles']) > 0
        except Exception:
            return False
    
    def test_edge_cases(self) -> bool:
        """测试边界条件"""
        print("\n⚠️ 边界条件测试:")
        
        tests = [
            ("空值处理", lambda: self._test_null_values()),
            ("超长字符串处理", lambda: self._test_long_strings()),
            ("特殊字符处理", lambda: self._test_special_characters()),
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False
        
        return all_passed
    
    def _test_null_values(self) -> bool:
        """测试空值处理"""
        try:
            # 测试可选字段的空值
            user_data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'Test123!',
                'nickname': None,  # 可选字段为空
                'phone': None      # 可选字段为空
            }
            
            user_request = UserCreateRequest(**user_data)
            return user_request.nickname is None and user_request.phone is None
        except Exception:
            return False
    
    def _test_long_strings(self) -> bool:
        """测试超长字符串处理"""
        try:
            # 测试描述字段的最大长度
            RoleCreateRequest(
                name='测试角色',
                code='ROLE_TEST',
                description='a' * 501  # 超过最大长度500
            )
            return False  # 应该抛出异常
        except ValidationError:
            return True  # 正确抛出异常
    
    def _test_special_characters(self) -> bool:
        """测试特殊字符处理"""
        try:
            # 测试包含特殊字符的昵称
            user_data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'Test123!',
                'nickname': '测试用户@#$%^&*()',  # 包含特殊字符
            }
            
            user_request = UserCreateRequest(**user_data)
            return user_request.nickname == '测试用户@#$%^&*()'
        except Exception:
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🔍 数据模式定义完整性和正确性检查")
        print("=" * 60)
        
        # 运行各项测试
        test_categories = [
            ("字符串长度验证", self.test_string_length_validation),
            ("正则表达式验证", self.test_regex_validation),
            ("序列化功能", self.test_serialization),
            ("边界条件", self.test_edge_cases),
        ]
        
        category_results = {}
        for category_name, test_func in test_categories:
            category_results[category_name] = test_func()
        
        # 输出测试结果汇总
        print("\n" + "=" * 60)
        print("📊 数据模式检查结果汇总:")
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
            print("🎉 数据模式定义质量优秀！")
        elif pass_rate >= 80:
            print("✅ 数据模式定义质量良好！")
        elif pass_rate >= 70:
            print("⚠️ 数据模式定义质量可接受，建议优化。")
        else:
            print("❌ 数据模式定义质量需要改进。")
        
        print("=" * 60)
        return pass_rate >= 80


def main():
    """主函数"""
    tester = SchemaValidationTester()
    success = tester.run_all_tests()
    
    if success:
        print("✅ 数据模式定义检查通过！")
        return 0
    else:
        print("❌ 数据模式定义检查未通过，需要修复问题。")
        return 1


if __name__ == "__main__":
    exit(main())
