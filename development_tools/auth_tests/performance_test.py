#!/usr/bin/env python3
"""
性能测试

按照第9轮检查提示词要求，全面测试认证中间件的性能。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
import asyncio
import time
import concurrent.futures
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.middleware.auth_middleware import (
    TokenHandler, UserInfoCache, SecurityMonitor,
    verify_jwt_token, PermissionChecker
)


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.results = {}
    
    async def test_token_verification_performance(self) -> bool:
        """测试令牌验证性能"""
        print("\n1. 测试令牌验证性能:")
        
        try:
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.verify_token.return_value = {
                'user_id': 1,
                'username': 'testuser'
            }
            
            # 测试单次令牌验证性能
            token = "test_token_123"
            
            start_time = time.time()
            for _ in range(1000):
                await verify_jwt_token(token, mock_auth_service)
            single_time = time.time() - start_time
            
            avg_time = single_time / 1000
            print(f"  ✅ 单次令牌验证平均时间: {avg_time:.6f}s")
            
            if avg_time < 0.001:  # 1ms以内
                print("  ✅ 令牌验证性能优秀")
                self.results['token_verification'] = avg_time
                return True
            elif avg_time < 0.01:  # 10ms以内
                print("  ✅ 令牌验证性能良好")
                self.results['token_verification'] = avg_time
                return True
            else:
                print("  ⚠️ 令牌验证性能需要优化")
                self.results['token_verification'] = avg_time
                return False
                
        except Exception as e:
            print(f"  ❌ 令牌验证性能测试异常: {str(e)}")
            return False
    
    async def test_permission_check_performance(self) -> bool:
        """测试权限检查性能"""
        print("\n2. 测试权限检查性能:")
        
        try:
            # 创建权限检查器
            checker = PermissionChecker(["user:view", "user:create"])
            
            # 创建用户
            user = Mock()
            user.id = 1
            user.username = "testuser"
            
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.check_permission.return_value = True
            
            # 测试权限检查性能
            start_time = time.time()
            for _ in range(100):
                await checker(user, mock_auth_service)
            check_time = time.time() - start_time
            
            avg_time = check_time / 100
            print(f"  ✅ 单次权限检查平均时间: {avg_time:.6f}s")
            
            if avg_time < 0.001:  # 1ms以内
                print("  ✅ 权限检查性能优秀")
                self.results['permission_check'] = avg_time
                return True
            elif avg_time < 0.01:  # 10ms以内
                print("  ✅ 权限检查性能良好")
                self.results['permission_check'] = avg_time
                return True
            else:
                print("  ⚠️ 权限检查性能需要优化")
                self.results['permission_check'] = avg_time
                return False
                
        except Exception as e:
            print(f"  ❌ 权限检查性能测试异常: {str(e)}")
            return False
    
    async def test_cache_performance(self) -> bool:
        """测试缓存机制效果"""
        print("\n3. 测试缓存机制效果:")
        
        try:
            token_handler = TokenHandler()
            user_cache = UserInfoCache()
            
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.verify_token.return_value = {
                'user_id': 1,
                'username': 'testuser'
            }
            
            token = "test_cache_token"
            
            # 测试无缓存的性能
            start_time = time.time()
            for _ in range(100):
                await verify_jwt_token(token, mock_auth_service)
            no_cache_time = time.time() - start_time
            
            # 测试有缓存的性能
            start_time = time.time()
            for _ in range(100):
                await token_handler.verify_token_with_cache(token, mock_auth_service)
            cache_time = time.time() - start_time
            
            # 计算缓存效果
            if cache_time < no_cache_time:
                improvement = ((no_cache_time - cache_time) / no_cache_time) * 100
                print(f"  ✅ 缓存提升性能: {improvement:.1f}%")
                self.results['cache_improvement'] = improvement
                return True
            else:
                print("  ⚠️ 缓存未显著提升性能")
                self.results['cache_improvement'] = 0
                return False
                
        except Exception as e:
            print(f"  ❌ 缓存性能测试异常: {str(e)}")
            return False
    
    async def test_concurrent_access_performance(self) -> bool:
        """测试并发访问性能"""
        print("\n4. 测试并发访问性能:")
        
        try:
            # 模拟AuthService
            mock_auth_service = AsyncMock()
            mock_auth_service.verify_token.return_value = {
                'user_id': 1,
                'username': 'testuser'
            }
            
            token = "test_concurrent_token"
            
            async def verify_token_task():
                """单个令牌验证任务"""
                return await verify_jwt_token(token, mock_auth_service)
            
            # 测试并发性能
            concurrent_count = 50
            start_time = time.time()
            
            tasks = [verify_token_task() for _ in range(concurrent_count)]
            results = await asyncio.gather(*tasks)
            
            concurrent_time = time.time() - start_time
            avg_time = concurrent_time / concurrent_count
            
            print(f"  ✅ 并发{concurrent_count}次验证总时间: {concurrent_time:.4f}s")
            print(f"  ✅ 并发验证平均时间: {avg_time:.6f}s")
            
            # 检查所有任务是否成功
            success_count = sum(1 for result in results if result is not None)
            success_rate = (success_count / concurrent_count) * 100
            
            print(f"  ✅ 并发验证成功率: {success_rate:.1f}%")
            
            if success_rate >= 95 and avg_time < 0.01:
                print("  ✅ 并发访问性能优秀")
                self.results['concurrent_performance'] = avg_time
                return True
            elif success_rate >= 90 and avg_time < 0.1:
                print("  ✅ 并发访问性能良好")
                self.results['concurrent_performance'] = avg_time
                return True
            else:
                print("  ⚠️ 并发访问性能需要优化")
                self.results['concurrent_performance'] = avg_time
                return False
                
        except Exception as e:
            print(f"  ❌ 并发访问性能测试异常: {str(e)}")
            return False
    
    async def test_memory_usage(self) -> bool:
        """测试内存使用情况"""
        print("\n5. 测试内存使用情况:")
        
        try:
            import psutil
            import os
            
            # 获取当前进程
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 创建大量缓存数据
            user_cache = UserInfoCache()
            token_handler = TokenHandler()
            
            # 添加大量缓存数据
            for i in range(1000):
                user_cache.set_user_info(i, {
                    'username': f'user{i}',
                    'email': f'user{i}@example.com'
                })
                
                token_handler._set_cache(f'token{i}', {
                    'user_id': i,
                    'username': f'user{i}'
                })
            
            # 检查内存使用
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"  ✅ 初始内存使用: {initial_memory:.2f}MB")
            print(f"  ✅ 最终内存使用: {final_memory:.2f}MB")
            print(f"  ✅ 内存增长: {memory_increase:.2f}MB")
            
            if memory_increase < 50:  # 50MB以内
                print("  ✅ 内存使用合理")
                self.results['memory_usage'] = memory_increase
                return True
            elif memory_increase < 100:  # 100MB以内
                print("  ✅ 内存使用可接受")
                self.results['memory_usage'] = memory_increase
                return True
            else:
                print("  ⚠️ 内存使用较高")
                self.results['memory_usage'] = memory_increase
                return False
                
        except ImportError:
            print("  ⚠️ psutil未安装，跳过内存测试")
            return True
        except Exception as e:
            print(f"  ❌ 内存使用测试异常: {str(e)}")
            return False
    
    async def test_cache_expiry_performance(self) -> bool:
        """测试缓存过期清理性能"""
        print("\n6. 测试缓存过期清理性能:")
        
        try:
            user_cache = UserInfoCache()
            token_handler = TokenHandler()
            
            # 添加大量缓存数据
            for i in range(1000):
                user_cache.set_user_info(i, {'username': f'user{i}'})
                token_handler._set_cache(f'token{i}', {'user_id': i})
            
            # 手动设置一些缓存为过期
            for i in range(0, 500):
                if i in user_cache._user_cache:
                    user_cache._user_cache[i]['expire_time'] = datetime.now() - timedelta(minutes=1)
                
                cache_key = f'token{i}'
                if cache_key in token_handler._token_cache:
                    token_handler._token_cache[cache_key]['expire_time'] = datetime.now() - timedelta(minutes=1)
            
            # 测试清理性能
            start_time = time.time()
            user_cache.clear_expired_cache()
            token_handler.clear_expired_cache()
            cleanup_time = time.time() - start_time
            
            print(f"  ✅ 缓存清理时间: {cleanup_time:.4f}s")
            
            if cleanup_time < 0.1:  # 100ms以内
                print("  ✅ 缓存清理性能优秀")
                self.results['cache_cleanup'] = cleanup_time
                return True
            elif cleanup_time < 1.0:  # 1s以内
                print("  ✅ 缓存清理性能良好")
                self.results['cache_cleanup'] = cleanup_time
                return True
            else:
                print("  ⚠️ 缓存清理性能需要优化")
                self.results['cache_cleanup'] = cleanup_time
                return False
                
        except Exception as e:
            print(f"  ❌ 缓存过期清理性能测试异常: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有性能测试"""
        print("🔍 性能测试")
        print("=" * 50)
        
        test_functions = [
            ("令牌验证性能", self.test_token_verification_performance),
            ("权限检查性能", self.test_permission_check_performance),
            ("缓存机制效果", self.test_cache_performance),
            ("并发访问性能", self.test_concurrent_access_performance),
            ("内存使用情况", self.test_memory_usage),
            ("缓存清理性能", self.test_cache_expiry_performance),
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
        print("📊 性能测试结果汇总:")
        print()
        
        if 'token_verification' in self.results:
            print(f"令牌验证性能: {self.results['token_verification']:.6f}s/次")
        
        if 'permission_check' in self.results:
            print(f"权限检查性能: {self.results['permission_check']:.6f}s/次")
        
        if 'cache_improvement' in self.results:
            print(f"缓存性能提升: {self.results['cache_improvement']:.1f}%")
        
        if 'concurrent_performance' in self.results:
            print(f"并发访问性能: {self.results['concurrent_performance']:.6f}s/次")
        
        if 'memory_usage' in self.results:
            print(f"内存使用增长: {self.results['memory_usage']:.2f}MB")
        
        if 'cache_cleanup' in self.results:
            print(f"缓存清理时间: {self.results['cache_cleanup']:.4f}s")
        
        print()
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        
        pass_rate = (passed_tests / total_tests) * 100
        print(f"通过率: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("🎉 性能测试优秀！")
        elif pass_rate >= 80:
            print("✅ 性能测试良好！")
        else:
            print("❌ 性能需要改进。")
        
        return pass_rate >= 80


async def main():
    """主函数"""
    tester = PerformanceTester()
    success = await tester.run_all_tests()
    
    if success:
        print("✅ 性能测试通过！")
        return 0
    else:
        print("❌ 性能测试未通过，需要优化性能。")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
