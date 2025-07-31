#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限系统性能测试脚本
测试各种场景下的系统性能

作者：RBAC权限系统
创建时间：2025-07-17
"""

import sys
import os
import time
import threading
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tqdm import tqdm
    import pymysql
except ImportError as e:
    print(f"缺少依赖包: {e}")
    print("请运行: pip install tqdm pymysql")
    sys.exit(1)

from utils.password_utils import verify_password
from utils.db_utils import DatabaseManager, DatabaseConfig
from config.test_config import get_config, get_benchmark


class PerformanceTest:
    """性能测试类"""
    
    def __init__(self, config_env: str = None):
        """
        初始化性能测试
        
        Args:
            config_env: 配置环境
        """
        self.config = get_config(config_env)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化数据库连接
        db_config = DatabaseConfig(**self.config.DATABASE)
        try:
            self.db_manager = DatabaseManager(
                db_config,
                min_connections=self.config.CONNECTION_POOL['min_connections'],
                max_connections=self.config.CONNECTION_POOL['max_connections']
            )
            # 测试数据库连接
            self._test_database_connection()
        except Exception as e:
            self.logger.error(f"数据库连接失败: {str(e)}")
            raise Exception(f"无法连接到数据库 {db_config.host}:{db_config.port}/{db_config.database}。请确保MySQL服务已启动。")
        
        # 测试结果存储
        self.results = {
            'authentication': {},
            'permission_query': {},
            'data_operations': {},
            'stress_test': {},
            'start_time': None,
            'end_time': None
        }
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 测试数据缓存
        self.test_users = []
        self.test_roles = []
        self.test_permissions = []
        
        self.logger.info("性能测试初始化完成")

    def _test_database_connection(self):
        """测试数据库连接"""
        try:
            # 执行简单查询测试连接
            result = self.db_manager.execute_query("SELECT 1 as test")
            if not result:
                raise Exception("数据库连接测试失败")
            self.logger.info("数据库连接测试成功")
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {str(e)}")
            raise

    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, self.config.LOGGING['level']),
            format=self.config.LOGGING['format'],
            handlers=[
                logging.FileHandler(self.config.LOGGING['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_test_data(self):
        """加载测试数据"""
        self.logger.info("加载测试数据...")
        
        # 加载用户数据
        users_sql = "SELECT id, username, password_hash FROM users WHERE status = 1 LIMIT 1000"
        self.test_users = self.db_manager.execute_query(users_sql)
        
        # 加载角色数据
        roles_sql = "SELECT id, role_code FROM roles WHERE status = 1 LIMIT 100"
        self.test_roles = self.db_manager.execute_query(roles_sql)
        
        # 加载权限数据
        permissions_sql = "SELECT id, permission_code FROM permissions LIMIT 500"
        self.test_permissions = self.db_manager.execute_query(permissions_sql)
        
        self.logger.info(f"加载测试数据完成: 用户{len(self.test_users)}个, 角色{len(self.test_roles)}个, 权限{len(self.test_permissions)}个")
    
    def _measure_time(self, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
        """
        测量函数执行时间
        
        Args:
            func: 要测量的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Tuple[Any, float]: (函数返回值, 执行时间)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def test_user_authentication(self) -> Dict[str, Any]:
        """测试用户认证性能"""
        self.logger.info("开始用户认证性能测试...")
        
        config = self.config.PERFORMANCE_TEST['authentication']
        results = {
            'single_login': {},
            'concurrent_login': {}
        }
        
        # 单次登录测试
        self.logger.info("执行单次登录测试...")
        single_times = []
        
        for _ in tqdm(range(config['single_login_tests']), desc="单次登录测试"):
            user = random.choice(self.test_users)
            
            def single_login():
                # 模拟登录验证过程
                sql = "SELECT id, username, password_hash FROM users WHERE username = %s AND status = 1"
                result = self.db_manager.execute_query(sql, (user['username'],))
                if result:
                    # 模拟密码验证（实际场景中会验证密码）
                    return len(result) > 0
                return False
            
            _, exec_time = self._measure_time(single_login)
            single_times.append(exec_time)
        
        results['single_login'] = {
            'count': len(single_times),
            'avg_time': statistics.mean(single_times),
            'min_time': min(single_times),
            'max_time': max(single_times),
            'median_time': statistics.median(single_times),
            'p95_time': self._percentile(single_times, 95),
            'p99_time': self._percentile(single_times, 99)
        }
        
        # 并发登录测试
        for concurrent_count in config['concurrent_tests']:
            self.logger.info(f"执行{concurrent_count}并发登录测试...")
            
            concurrent_times = []
            errors = 0
            
            def concurrent_login():
                try:
                    user = random.choice(self.test_users)
                    sql = "SELECT id, username, password_hash FROM users WHERE username = %s AND status = 1"
                    result = self.db_manager.execute_query(sql, (user['username'],))
                    return len(result) > 0 if result else False
                except Exception:
                    return None
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
                futures = [executor.submit(concurrent_login) for _ in range(concurrent_count)]
                
                for future in as_completed(futures, timeout=config['timeout']):
                    try:
                        result = future.result()
                        if result is None:
                            errors += 1
                    except Exception:
                        errors += 1
            
            total_time = time.time() - start_time
            
            results['concurrent_login'][f'{concurrent_count}_concurrent'] = {
                'concurrent_users': concurrent_count,
                'total_time': total_time,
                'avg_time_per_request': total_time / concurrent_count,
                'requests_per_second': concurrent_count / total_time,
                'error_count': errors,
                'success_rate': (concurrent_count - errors) / concurrent_count
            }
        
        self.results['authentication'] = results
        return results
    
    def test_permission_query(self) -> Dict[str, Any]:
        """测试权限查询性能"""
        self.logger.info("开始权限查询性能测试...")
        
        config = self.config.PERFORMANCE_TEST['permission_query']
        results = {
            'single_query': {},
            'batch_query': {},
            'concurrent_query': {}
        }
        
        # 单用户权限查询测试
        self.logger.info("执行单用户权限查询测试...")
        single_times = []
        
        for _ in tqdm(range(config['single_query_tests']), desc="单用户权限查询"):
            user = random.choice(self.test_users)
            
            def single_permission_query():
                sql = """
                SELECT DISTINCT p.permission_code
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id AND ur.status = 1
                JOIN roles r ON ur.role_id = r.id AND r.status = 1
                JOIN role_permissions rp ON r.id = rp.role_id AND rp.status = 1
                JOIN permissions p ON rp.permission_id = p.id
                WHERE u.id = %s AND u.status = 1
                """
                return self.db_manager.execute_query(sql, (user['id'],))
            
            _, exec_time = self._measure_time(single_permission_query)
            single_times.append(exec_time)
        
        results['single_query'] = {
            'count': len(single_times),
            'avg_time': statistics.mean(single_times),
            'min_time': min(single_times),
            'max_time': max(single_times),
            'median_time': statistics.median(single_times),
            'p95_time': self._percentile(single_times, 95),
            'p99_time': self._percentile(single_times, 99)
        }
        
        # 批量权限查询测试
        for batch_size in config['batch_query_sizes']:
            self.logger.info(f"执行批量权限查询测试 (批量大小: {batch_size})...")
            
            batch_times = []
            
            for _ in range(10):  # 执行10次批量测试
                user_ids = [random.choice(self.test_users)['id'] for _ in range(batch_size)]
                
                def batch_permission_query():
                    placeholders = ','.join(['%s'] * len(user_ids))
                    sql = f"""
                    SELECT u.id as user_id, p.permission_code
                    FROM users u
                    JOIN user_roles ur ON u.id = ur.user_id AND ur.status = 1
                    JOIN roles r ON ur.role_id = r.id AND r.status = 1
                    JOIN role_permissions rp ON r.id = rp.role_id AND rp.status = 1
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE u.id IN ({placeholders}) AND u.status = 1
                    """
                    return self.db_manager.execute_query(sql, user_ids)
                
                _, exec_time = self._measure_time(batch_permission_query)
                batch_times.append(exec_time)
            
            results['batch_query'][f'batch_{batch_size}'] = {
                'batch_size': batch_size,
                'count': len(batch_times),
                'avg_time': statistics.mean(batch_times),
                'avg_time_per_user': statistics.mean(batch_times) / batch_size,
                'min_time': min(batch_times),
                'max_time': max(batch_times)
            }
        
        self.results['permission_query'] = results
        return results

    def test_data_operations(self) -> Dict[str, Any]:
        """测试数据操作性能"""
        self.logger.info("开始数据操作性能测试...")

        config = self.config.PERFORMANCE_TEST['data_operations']
        results = {
            'user_crud': {},
            'role_assignment': {},
            'batch_operations': {}
        }

        # 用户CRUD操作测试
        self.logger.info("执行用户CRUD操作测试...")
        crud_times = {
            'create': [],
            'read': [],
            'update': [],
            'delete': []
        }

        for _ in tqdm(range(config['crud_test_count']), desc="用户CRUD测试"):
            # 创建用户
            def create_user():
                sql = """
                INSERT INTO users (username, email, password_hash, status)
                VALUES (%s, %s, %s, %s)
                """
                username = f"test_user_{random.randint(100000, 999999)}"
                email = f"{username}@test.com"
                password_hash = "$2b$12$test_hash_placeholder"
                return self.db_manager.execute_update(sql, (username, email, password_hash, 1))

            _, create_time = self._measure_time(create_user)
            crud_times['create'].append(create_time)

            # 读取用户
            def read_user():
                sql = "SELECT * FROM users WHERE status = 1 ORDER BY RAND() LIMIT 1"
                return self.db_manager.execute_query(sql)

            _, read_time = self._measure_time(read_user)
            crud_times['read'].append(read_time)

            # 更新用户
            def update_user():
                user = random.choice(self.test_users)
                sql = "UPDATE users SET updated_at = NOW() WHERE id = %s"
                return self.db_manager.execute_update(sql, (user['id'],))

            _, update_time = self._measure_time(update_user)
            crud_times['update'].append(update_time)

        for operation, times in crud_times.items():
            if times:
                results['user_crud'][operation] = {
                    'count': len(times),
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'median_time': statistics.median(times)
                }

        # 角色分配性能测试
        self.logger.info("执行角色分配性能测试...")
        assignment_times = []

        for _ in tqdm(range(100), desc="角色分配测试"):
            user = random.choice(self.test_users)
            role = random.choice(self.test_roles)

            def assign_role():
                sql = """
                INSERT IGNORE INTO user_roles (user_id, role_id, assigned_by, status)
                VALUES (%s, %s, %s, %s)
                """
                assigned_by = random.choice(self.test_users)['id']
                return self.db_manager.execute_update(sql, (user['id'], role['id'], assigned_by, 1))

            _, exec_time = self._measure_time(assign_role)
            assignment_times.append(exec_time)

        results['role_assignment'] = {
            'count': len(assignment_times),
            'avg_time': statistics.mean(assignment_times),
            'min_time': min(assignment_times),
            'max_time': max(assignment_times),
            'median_time': statistics.median(assignment_times)
        }

        # 批量操作测试
        for batch_size in config['batch_sizes']:
            self.logger.info(f"执行批量操作测试 (批量大小: {batch_size})...")

            def batch_insert():
                sql = """
                INSERT INTO audit_logs (user_id, action_type, resource_type, resource_id,
                                      action_result, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                batch_data = []
                for _ in range(batch_size):
                    user = random.choice(self.test_users)
                    batch_data.append((
                        user['id'],
                        'test_action',
                        'test_resource',
                        str(random.randint(1, 1000)),
                        1,
                        '127.0.0.1',
                        'Test Agent'
                    ))

                return self.db_manager.execute_batch(sql, batch_data)

            _, batch_time = self._measure_time(batch_insert)

            results['batch_operations'][f'batch_{batch_size}'] = {
                'batch_size': batch_size,
                'total_time': batch_time,
                'time_per_record': batch_time / batch_size,
                'records_per_second': batch_size / batch_time
            }

        self.results['data_operations'] = results
        return results

    def test_stress_test(self) -> Dict[str, Any]:
        """压力测试"""
        self.logger.info("开始压力测试...")

        config = self.config.PERFORMANCE_TEST['stress_test']
        results = {
            'duration_minutes': config['duration_minutes'],
            'concurrent_users': config['concurrent_users'],
            'operations_per_minute': config['operations_per_minute'],
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'avg_response_time': 0,
            'max_response_time': 0,
            'min_response_time': float('inf'),
            'operations_per_second': 0,
            'error_rate': 0
        }

        duration_seconds = config['duration_minutes'] * 60
        total_operations = config['operations_per_minute'] * config['duration_minutes']

        operation_times = []
        successful_ops = 0
        failed_ops = 0

        def stress_operation():
            """压力测试操作"""
            try:
                # 随机选择操作类型
                operation_type = random.choice(['login', 'permission_check', 'user_query'])

                if operation_type == 'login':
                    user = random.choice(self.test_users)
                    sql = "SELECT id FROM users WHERE username = %s AND status = 1"
                    result = self.db_manager.execute_query(sql, (user['username'],))
                    return len(result) > 0 if result else False

                elif operation_type == 'permission_check':
                    user = random.choice(self.test_users)
                    sql = """
                    SELECT COUNT(*) as perm_count
                    FROM users u
                    JOIN user_roles ur ON u.id = ur.user_id AND ur.status = 1
                    JOIN role_permissions rp ON ur.role_id = rp.role_id AND rp.status = 1
                    WHERE u.id = %s
                    """
                    result = self.db_manager.execute_query(sql, (user['id'],))
                    return result[0]['perm_count'] > 0 if result else False

                else:  # user_query
                    sql = "SELECT COUNT(*) as user_count FROM users WHERE status = 1"
                    result = self.db_manager.execute_query(sql)
                    return result[0]['user_count'] > 0 if result else False

            except Exception:
                return False

        self.logger.info(f"开始{config['duration_minutes']}分钟压力测试，{config['concurrent_users']}并发用户...")

        start_time = time.time()
        end_time = start_time + duration_seconds

        with ThreadPoolExecutor(max_workers=config['concurrent_users']) as executor:
            with tqdm(total=total_operations, desc="压力测试") as pbar:

                while time.time() < end_time and len(operation_times) < total_operations:
                    # 提交一批操作
                    batch_size = min(config['concurrent_users'], total_operations - len(operation_times))
                    futures = []

                    for _ in range(batch_size):
                        future = executor.submit(self._measure_time, stress_operation)
                        futures.append(future)

                    # 收集结果
                    for future in as_completed(futures, timeout=30):
                        try:
                            result, exec_time = future.result()
                            operation_times.append(exec_time)

                            if result:
                                successful_ops += 1
                            else:
                                failed_ops += 1

                            pbar.update(1)

                        except Exception:
                            failed_ops += 1
                            pbar.update(1)

        actual_duration = time.time() - start_time

        if operation_times:
            results.update({
                'total_operations': len(operation_times),
                'successful_operations': successful_ops,
                'failed_operations': failed_ops,
                'avg_response_time': statistics.mean(operation_times),
                'max_response_time': max(operation_times),
                'min_response_time': min(operation_times),
                'operations_per_second': len(operation_times) / actual_duration,
                'error_rate': failed_ops / len(operation_times),
                'actual_duration_seconds': actual_duration
            })

        self.results['stress_test'] = results
        return results

    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        self.logger.info("开始运行所有性能测试...")
        self.results['start_time'] = datetime.now()

        # 加载测试数据
        self._load_test_data()

        if not self.test_users:
            self.logger.error("没有找到测试用户数据，请先运行数据生成器")
            return self.results

        # 执行各项测试
        test_functions = [
            ("用户认证测试", self.test_user_authentication),
            ("权限查询测试", self.test_permission_query),
            ("数据操作测试", self.test_data_operations),
            ("压力测试", self.test_stress_test)
        ]

        for test_name, test_func in test_functions:
            self.logger.info(f"执行: {test_name}")
            try:
                test_func()
                self.logger.info(f"{test_name} 完成")
            except Exception as e:
                self.logger.error(f"{test_name} 失败: {str(e)}")

        self.results['end_time'] = datetime.now()

        # 生成测试报告
        self._print_summary()

        return self.results

    def _print_summary(self):
        """打印测试摘要"""
        duration = self.results['end_time'] - self.results['start_time']

        print("\n" + "="*60)
        print("📊 性能测试报告摘要")
        print("="*60)
        print(f"测试时间: {self.results['start_time'].strftime('%Y-%m-%d %H:%M:%S')} - {self.results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration}")
        print()

        # 用户认证测试结果
        if 'authentication' in self.results and self.results['authentication']:
            auth = self.results['authentication']
            if 'single_login' in auth:
                single = auth['single_login']
                print(f"🔐 用户认证测试:")
                print(f"  单次登录平均时间: {single['avg_time']*1000:.2f}ms")
                print(f"  P95响应时间: {single['p95_time']*1000:.2f}ms")

        # 权限查询测试结果
        if 'permission_query' in self.results and self.results['permission_query']:
            perm = self.results['permission_query']
            if 'single_query' in perm:
                single = perm['single_query']
                print(f"🔍 权限查询测试:")
                print(f"  单次查询平均时间: {single['avg_time']*1000:.2f}ms")
                print(f"  P95响应时间: {single['p95_time']*1000:.2f}ms")

        # 压力测试结果
        if 'stress_test' in self.results and self.results['stress_test']:
            stress = self.results['stress_test']
            if 'operations_per_second' in stress:
                print(f"⚡ 压力测试:")
                print(f"  每秒操作数: {stress['operations_per_second']:.2f}")
                print(f"  错误率: {stress['error_rate']*100:.2f}%")
                print(f"  平均响应时间: {stress['avg_response_time']*1000:.2f}ms")

        print("="*60)

    def close(self):
        """关闭数据库连接"""
        if self.db_manager:
            self.db_manager.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='RBAC权限系统性能测试')
    parser.add_argument('--env', default='development', help='配置环境')
    parser.add_argument('--test', choices=['auth', 'permission', 'data', 'stress', 'all'],
                       default='all', help='测试类型')

    args = parser.parse_args()

    tester = PerformanceTest(args.env)

    try:
        if args.test == 'all':
            results = tester.run_all_tests()
        elif args.test == 'auth':
            tester._load_test_data()
            results = tester.test_user_authentication()
        elif args.test == 'permission':
            tester._load_test_data()
            results = tester.test_permission_query()
        elif args.test == 'data':
            tester._load_test_data()
            results = tester.test_data_operations()
        elif args.test == 'stress':
            tester._load_test_data()
            results = tester.test_stress_test()

        # 保存结果到文件
        output_file = f"reports/performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('reports', exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 详细测试结果已保存到: {output_file}")

        return 0

    except KeyboardInterrupt:
        print("\n用户中断测试")
        return 1
    except Exception as e:
        print(f"测试异常: {str(e)}")
        return 1
    finally:
        tester.close()


if __name__ == "__main__":
    sys.exit(main())
