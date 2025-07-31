#!/usr/bin/env python3
"""
数据模式性能测试脚本

测试数据模式的序列化、反序列化性能。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import List

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    UserCreateRequest, UserResponse, UserDetailResponse, UserListResponse,
    RoleResponse, PermissionResponse, LoginRequest, LoginResponse
)


class SchemaPerformanceTester:
    """数据模式性能测试器"""
    
    def __init__(self):
        self.results = {}
    
    def test_serialization_performance(self):
        """测试序列化性能"""
        print("🚀 6. 性能测试")
        print("=" * 50)
        print("\n📊 序列化性能测试:")
        
        # 测试单个对象序列化
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
        
        # 单个用户序列化性能
        start_time = time.time()
        for _ in range(1000):
            user_response = UserResponse(**user_data)
            json_str = user_response.model_dump_json()
        single_time = time.time() - start_time
        
        print(f"  ✅ 单个用户序列化 (1000次): {single_time:.4f}s")
        print(f"     平均每次: {single_time/1000:.6f}s")
        
        # 批量用户序列化性能
        users_data = []
        for i in range(100):
            user = {
                'id': i + 1,
                'username': f'user{i+1}',
                'email': f'user{i+1}@example.com',
                'nickname': f'用户{i+1}',
                'phone': f'1380013800{i%10}',
                'status': 1,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'last_login_at': datetime.now()
            }
            users_data.append(user)
        
        start_time = time.time()
        user_responses = [UserResponse(**data) for data in users_data]
        batch_time = time.time() - start_time
        
        print(f"  ✅ 批量用户序列化 (100个): {batch_time:.4f}s")
        print(f"     平均每个: {batch_time/100:.6f}s")
        
        # 复杂嵌套对象序列化性能
        user_detail_data = {
            **user_data,
            'roles': ['admin', 'user', 'manager'],
            'permissions': [f'resource{i}:action{j}' for i in range(10) for j in range(5)],
            'login_count': 100
        }
        
        start_time = time.time()
        for _ in range(100):
            user_detail_response = UserDetailResponse(**user_detail_data)
            json_str = user_detail_response.model_dump_json()
        nested_time = time.time() - start_time
        
        print(f"  ✅ 复杂嵌套对象序列化 (100次): {nested_time:.4f}s")
        print(f"     平均每次: {nested_time/100:.6f}s")
        
        self.results['serialization'] = {
            'single_time': single_time,
            'batch_time': batch_time,
            'nested_time': nested_time
        }
    
    def test_validation_performance(self):
        """测试验证性能"""
        print("\n🔍 验证规则执行性能测试:")
        
        # 用户创建请求验证性能
        user_requests_data = []
        for i in range(100):
            user_data = {
                'username': f'testuser{i}',
                'email': f'test{i}@example.com',
                'password': f'TestPass{i}123!',
                'nickname': f'测试用户{i}',
                'phone': f'1380013800{i%10}'
            }
            user_requests_data.append(user_data)
        
        start_time = time.time()
        for data in user_requests_data:
            user_request = UserCreateRequest(**data)
        validation_time = time.time() - start_time
        
        print(f"  ✅ 用户创建验证 (100次): {validation_time:.4f}s")
        print(f"     平均每次: {validation_time/100:.6f}s")
        
        # 登录请求验证性能
        login_requests_data = []
        for i in range(1000):
            login_data = {
                'username': f'user{i}',
                'password': f'password{i}',
                'remember_me': i % 2 == 0,
                'device_info': f'Device {i}'
            }
            login_requests_data.append(login_data)
        
        start_time = time.time()
        for data in login_requests_data:
            login_request = LoginRequest(**data)
        login_validation_time = time.time() - start_time
        
        print(f"  ✅ 登录请求验证 (1000次): {login_validation_time:.4f}s")
        print(f"     平均每次: {login_validation_time/1000:.6f}s")
        
        self.results['validation'] = {
            'user_validation_time': validation_time,
            'login_validation_time': login_validation_time
        }
    
    def test_json_conversion_performance(self):
        """测试JSON转换性能"""
        print("\n🔄 JSON转换性能测试:")
        
        # 准备测试数据
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
        
        # 测试model_dump_json性能
        start_time = time.time()
        for _ in range(1000):
            json_str = user_response.model_dump_json()
        dump_time = time.time() - start_time
        
        print(f"  ✅ model_dump_json (1000次): {dump_time:.4f}s")
        print(f"     平均每次: {dump_time/1000:.6f}s")
        
        # 测试model_dump + json.dumps性能
        start_time = time.time()
        for _ in range(1000):
            data_dict = user_response.model_dump()
            json_str = json.dumps(data_dict, default=str)
        manual_dump_time = time.time() - start_time
        
        print(f"  ✅ model_dump + json.dumps (1000次): {manual_dump_time:.4f}s")
        print(f"     平均每次: {manual_dump_time/1000:.6f}s")
        
        # 比较性能
        if dump_time < manual_dump_time:
            print(f"  📈 model_dump_json 比手动转换快 {((manual_dump_time - dump_time) / manual_dump_time * 100):.1f}%")
        else:
            print(f"  📉 手动转换比 model_dump_json 快 {((dump_time - manual_dump_time) / dump_time * 100):.1f}%")
        
        self.results['json_conversion'] = {
            'dump_time': dump_time,
            'manual_dump_time': manual_dump_time
        }
    
    def run_all_tests(self):
        """运行所有性能测试"""
        print("🔍 数据模式性能测试")
        print("=" * 60)
        
        self.test_serialization_performance()
        self.test_validation_performance()
        self.test_json_conversion_performance()
        
        # 输出性能总结
        print("\n" + "=" * 60)
        print("📊 性能测试结果总结:")
        print()
        
        if 'serialization' in self.results:
            ser = self.results['serialization']
            print(f"序列化性能:")
            print(f"  - 单个对象: {ser['single_time']/1000:.6f}s/次")
            print(f"  - 批量对象: {ser['batch_time']/100:.6f}s/个")
            print(f"  - 复杂嵌套: {ser['nested_time']/100:.6f}s/次")
        
        if 'validation' in self.results:
            val = self.results['validation']
            print(f"验证性能:")
            print(f"  - 用户创建验证: {val['user_validation_time']/100:.6f}s/次")
            print(f"  - 登录请求验证: {val['login_validation_time']/1000:.6f}s/次")
        
        if 'json_conversion' in self.results:
            json_conv = self.results['json_conversion']
            print(f"JSON转换性能:")
            print(f"  - model_dump_json: {json_conv['dump_time']/1000:.6f}s/次")
            print(f"  - 手动转换: {json_conv['manual_dump_time']/1000:.6f}s/次")
        
        # 性能评估
        print()
        avg_serialization = self.results.get('serialization', {}).get('single_time', 0) / 1000
        avg_validation = self.results.get('validation', {}).get('user_validation_time', 0) / 100
        
        if avg_serialization < 0.001 and avg_validation < 0.001:
            print("🎉 性能表现优秀！所有操作都在1ms以内完成。")
        elif avg_serialization < 0.01 and avg_validation < 0.01:
            print("✅ 性能表现良好！所有操作都在10ms以内完成。")
        else:
            print("⚠️ 性能表现一般，建议进行优化。")
        
        print("=" * 60)


def main():
    """主函数"""
    tester = SchemaPerformanceTester()
    tester.run_all_tests()
    return 0


if __name__ == "__main__":
    exit(main())
