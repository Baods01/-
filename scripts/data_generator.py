#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限系统测试数据生成器
生成海量测试数据用于性能测试

作者：RBAC权限系统
创建时间：2025-07-17
"""

import sys
import os
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from faker import Faker
    from tqdm import tqdm
    import pymysql
except ImportError as e:
    print(f"缺少依赖包: {e}")
    print("请运行: pip install faker tqdm pymysql")
    sys.exit(1)

from utils.password_utils import hash_password
from utils.db_utils import DatabaseManager, DatabaseConfig
from config.test_config import get_config, get_scenario


class DataGenerator:
    """测试数据生成器"""
    
    def __init__(self, config_env: str = None, scenario: str = 'standard_test'):
        """
        初始化数据生成器
        
        Args:
            config_env: 配置环境
            scenario: 测试场景
        """
        self.config = get_config(config_env)
        self.scenario_config = get_scenario(scenario)
        self.fake = Faker(self.config.FAKER['locale'])
        
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
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'users_generated': 0,
            'roles_generated': 0,
            'permissions_generated': 0,
            'user_roles_generated': 0,
            'role_permissions_generated': 0,
            'audit_logs_generated': 0,
            'start_time': None,
            'end_time': None,
            'errors': []
        }
        
        self.logger.info(f"数据生成器初始化完成，场景: {scenario}")

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
    
    def generate_users(self, count: int = None) -> bool:
        """
        生成用户数据
        
        Args:
            count: 生成数量，默认使用配置
            
        Returns:
            bool: 是否成功
        """
        if count is None:
            count = self.scenario_config['data_scale']['users']
        
        batch_size = self.config.DATA_GENERATION['users']['batch_size']
        default_password = self.config.DATA_GENERATION['users']['default_password']
        
        self.logger.info(f"开始生成 {count} 个用户...")
        
        # 预先生成密码哈希
        password_hash = hash_password(default_password)
        
        try:
            with tqdm(total=count, desc="生成用户") as pbar:
                for i in range(0, count, batch_size):
                    current_batch_size = min(batch_size, count - i)
                    users_batch = []
                    
                    for j in range(current_batch_size):
                        # 生成随机状态
                        status = 1 if random.random() < self.config.DATA_GENERATION['users']['status_distribution']['active'] else 0
                        
                        user = {
                            'username': self.fake.user_name() + f"_{i+j}",
                            'email': self.fake.email(),
                            'password_hash': password_hash,
                            'status': status
                        }
                        users_batch.append(user)
                    
                    # 批量插入
                    self._insert_users_batch(users_batch)
                    
                    with self.lock:
                        self.stats['users_generated'] += current_batch_size
                    
                    pbar.update(current_batch_size)
            
            self.logger.info(f"用户生成完成: {self.stats['users_generated']} 条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"用户生成失败: {str(e)}")
            self.stats['errors'].append(f"用户生成错误: {str(e)}")
            return False
    
    def _insert_users_batch(self, users: List[Dict[str, Any]]):
        """批量插入用户"""
        sql = """
        INSERT INTO users (username, email, password_hash, status)
        VALUES (%(username)s, %(email)s, %(password_hash)s, %(status)s)
        """
        self.db_manager.execute_batch(sql, users)
    
    def generate_roles(self, count: int = None) -> bool:
        """生成角色数据"""
        if count is None:
            count = self.scenario_config['data_scale']['roles']
        
        batch_size = self.config.DATA_GENERATION['roles']['batch_size']
        categories = self.config.DATA_GENERATION['roles']['categories']
        
        self.logger.info(f"开始生成 {count} 个角色...")
        
        try:
            with tqdm(total=count, desc="生成角色") as pbar:
                for i in range(0, count, batch_size):
                    current_batch_size = min(batch_size, count - i)
                    roles_batch = []
                    
                    for j in range(current_batch_size):
                        category = random.choice(categories)
                        level = random.choice(['junior', 'senior', 'lead', 'manager'])
                        department = self.fake.company()[:20]
                        
                        role = {
                            'role_name': f"{department} {level} {category}",
                            'role_code': f"{category}_{level}_{i+j}",
                            'status': 1
                        }
                        roles_batch.append(role)
                    
                    self._insert_roles_batch(roles_batch)
                    
                    with self.lock:
                        self.stats['roles_generated'] += current_batch_size
                    
                    pbar.update(current_batch_size)
            
            self.logger.info(f"角色生成完成: {self.stats['roles_generated']} 条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"角色生成失败: {str(e)}")
            self.stats['errors'].append(f"角色生成错误: {str(e)}")
            return False
    
    def _insert_roles_batch(self, roles: List[Dict[str, Any]]):
        """批量插入角色"""
        sql = """
        INSERT INTO roles (role_name, role_code, status)
        VALUES (%(role_name)s, %(role_code)s, %(status)s)
        """
        self.db_manager.execute_batch(sql, roles)
    
    def generate_permissions(self, count: int = None) -> bool:
        """生成权限数据"""
        if count is None:
            count = self.scenario_config['data_scale']['permissions']
        
        batch_size = self.config.DATA_GENERATION['permissions']['batch_size']
        modules = self.config.DATA_GENERATION['permissions']['modules']
        actions = self.config.DATA_GENERATION['permissions']['actions']
        
        self.logger.info(f"开始生成 {count} 个权限...")
        
        try:
            with tqdm(total=count, desc="生成权限") as pbar:
                for i in range(0, count, batch_size):
                    current_batch_size = min(batch_size, count - i)
                    permissions_batch = []
                    
                    for j in range(current_batch_size):
                        module = random.choice(modules)
                        action = random.choice(actions)
                        resource_detail = self.fake.word()
                        
                        permission = {
                            'permission_name': f"{module} {action} {resource_detail}",
                            'permission_code': f"{module}:{action}:{resource_detail}_{i+j}",
                            'resource_type': module,
                            'action_type': action
                        }
                        permissions_batch.append(permission)
                    
                    self._insert_permissions_batch(permissions_batch)
                    
                    with self.lock:
                        self.stats['permissions_generated'] += current_batch_size
                    
                    pbar.update(current_batch_size)
            
            self.logger.info(f"权限生成完成: {self.stats['permissions_generated']} 条记录")
            return True
            
        except Exception as e:
            self.logger.error(f"权限生成失败: {str(e)}")
            self.stats['errors'].append(f"权限生成错误: {str(e)}")
            return False
    
    def _insert_permissions_batch(self, permissions: List[Dict[str, Any]]):
        """批量插入权限"""
        sql = """
        INSERT INTO permissions (permission_name, permission_code, resource_type, action_type)
        VALUES (%(permission_name)s, %(permission_code)s, %(resource_type)s, %(action_type)s)
        """
        self.db_manager.execute_batch(sql, permissions)

    def generate_user_roles(self) -> bool:
        """生成用户角色关联数据"""
        self.logger.info("开始生成用户角色关联...")

        try:
            # 获取所有用户和角色ID
            users = self.db_manager.execute_query("SELECT id FROM users WHERE status = 1")
            roles = self.db_manager.execute_query("SELECT id FROM roles WHERE status = 1")

            if not users or not roles:
                self.logger.error("没有找到用户或角色数据")
                return False

            user_ids = [user['id'] for user in users]
            role_ids = [role['id'] for role in roles]

            batch_size = self.config.DATA_GENERATION['user_roles']['batch_size']
            min_roles = self.config.DATA_GENERATION['user_roles']['min_roles']
            max_roles = self.config.DATA_GENERATION['user_roles']['max_roles']

            total_relations = 0

            with tqdm(total=len(user_ids), desc="生成用户角色关联") as pbar:
                user_roles_batch = []

                for user_id in user_ids:
                    # 为每个用户随机分配角色
                    num_roles = random.randint(min_roles, max_roles)
                    selected_roles = random.sample(role_ids, min(num_roles, len(role_ids)))

                    for role_id in selected_roles:
                        user_role = {
                            'user_id': user_id,
                            'role_id': role_id,
                            'assigned_by': random.choice(user_ids),
                            'status': 1
                        }
                        user_roles_batch.append(user_role)
                        total_relations += 1

                        # 批量插入
                        if len(user_roles_batch) >= batch_size:
                            self._insert_user_roles_batch(user_roles_batch)
                            with self.lock:
                                self.stats['user_roles_generated'] += len(user_roles_batch)
                            user_roles_batch = []

                    pbar.update(1)

                # 插入剩余数据
                if user_roles_batch:
                    self._insert_user_roles_batch(user_roles_batch)
                    with self.lock:
                        self.stats['user_roles_generated'] += len(user_roles_batch)

            self.logger.info(f"用户角色关联生成完成: {self.stats['user_roles_generated']} 条记录")
            return True

        except Exception as e:
            self.logger.error(f"用户角色关联生成失败: {str(e)}")
            self.stats['errors'].append(f"用户角色关联生成错误: {str(e)}")
            return False

    def _insert_user_roles_batch(self, user_roles: List[Dict[str, Any]]):
        """批量插入用户角色关联"""
        sql = """
        INSERT IGNORE INTO user_roles (user_id, role_id, assigned_by, status)
        VALUES (%(user_id)s, %(role_id)s, %(assigned_by)s, %(status)s)
        """
        self.db_manager.execute_batch(sql, user_roles)

    def generate_role_permissions(self) -> bool:
        """生成角色权限关联数据"""
        self.logger.info("开始生成角色权限关联...")

        try:
            # 获取所有角色和权限ID
            roles = self.db_manager.execute_query("SELECT id FROM roles WHERE status = 1")
            permissions = self.db_manager.execute_query("SELECT id FROM permissions")
            users = self.db_manager.execute_query("SELECT id FROM users WHERE status = 1 LIMIT 100")

            if not roles or not permissions:
                self.logger.error("没有找到角色或权限数据")
                return False

            role_ids = [role['id'] for role in roles]
            permission_ids = [perm['id'] for perm in permissions]
            user_ids = [user['id'] for user in users]

            batch_size = self.config.DATA_GENERATION['role_permissions']['batch_size']
            min_permissions = self.config.DATA_GENERATION['role_permissions']['min_permissions']
            max_permissions = self.config.DATA_GENERATION['role_permissions']['max_permissions']

            with tqdm(total=len(role_ids), desc="生成角色权限关联") as pbar:
                role_permissions_batch = []

                for role_id in role_ids:
                    # 为每个角色随机分配权限
                    num_permissions = random.randint(min_permissions, max_permissions)
                    selected_permissions = random.sample(permission_ids, min(num_permissions, len(permission_ids)))

                    for permission_id in selected_permissions:
                        role_permission = {
                            'role_id': role_id,
                            'permission_id': permission_id,
                            'granted_by': random.choice(user_ids) if user_ids else None,
                            'status': 1
                        }
                        role_permissions_batch.append(role_permission)

                        # 批量插入
                        if len(role_permissions_batch) >= batch_size:
                            self._insert_role_permissions_batch(role_permissions_batch)
                            with self.lock:
                                self.stats['role_permissions_generated'] += len(role_permissions_batch)
                            role_permissions_batch = []

                    pbar.update(1)

                # 插入剩余数据
                if role_permissions_batch:
                    self._insert_role_permissions_batch(role_permissions_batch)
                    with self.lock:
                        self.stats['role_permissions_generated'] += len(role_permissions_batch)

            self.logger.info(f"角色权限关联生成完成: {self.stats['role_permissions_generated']} 条记录")
            return True

        except Exception as e:
            self.logger.error(f"角色权限关联生成失败: {str(e)}")
            self.stats['errors'].append(f"角色权限关联生成错误: {str(e)}")
            return False

    def _insert_role_permissions_batch(self, role_permissions: List[Dict[str, Any]]):
        """批量插入角色权限关联"""
        sql = """
        INSERT IGNORE INTO role_permissions (role_id, permission_id, granted_by, status)
        VALUES (%(role_id)s, %(permission_id)s, %(granted_by)s, %(status)s)
        """
        self.db_manager.execute_batch(sql, role_permissions)

    def generate_audit_logs(self, count: int = None) -> bool:
        """生成操作日志数据"""
        if count is None:
            count = self.scenario_config['data_scale']['audit_logs']

        batch_size = self.config.DATA_GENERATION['audit_logs']['batch_size']
        action_types = self.config.DATA_GENERATION['audit_logs']['action_types']
        success_rate = self.config.DATA_GENERATION['audit_logs']['success_rate']

        self.logger.info(f"开始生成 {count} 条操作日志...")

        try:
            # 获取用户ID列表
            users = self.db_manager.execute_query("SELECT id FROM users LIMIT 1000")
            if not users:
                self.logger.error("没有找到用户数据")
                return False

            user_ids = [user['id'] for user in users]

            with tqdm(total=count, desc="生成操作日志") as pbar:
                for i in range(0, count, batch_size):
                    current_batch_size = min(batch_size, count - i)
                    logs_batch = []

                    for j in range(current_batch_size):
                        # 生成随机时间（过去30天内）
                        days_ago = random.randint(0, 30)
                        hours_ago = random.randint(0, 23)
                        minutes_ago = random.randint(0, 59)

                        created_at = datetime.now() - timedelta(
                            days=days_ago,
                            hours=hours_ago,
                            minutes=minutes_ago
                        )

                        action_type = random.choice(action_types)
                        action_result = 1 if random.random() < success_rate else 0

                        log = {
                            'user_id': random.choice(user_ids),
                            'action_type': action_type,
                            'resource_type': action_type.split('_')[0] if '_' in action_type else 'system',
                            'resource_id': str(random.randint(1, 10000)),
                            'action_result': action_result,
                            'ip_address': self.fake.ipv4(),
                            'user_agent': self.fake.user_agent(),
                            'request_data': f'{{"action": "{action_type}", "timestamp": "{created_at.isoformat()}"}}',
                            'response_data': f'{{"status": "{"success" if action_result else "failed"}", "code": {200 if action_result else 400}}}',
                            'error_message': None if action_result else self.fake.sentence(),
                            'created_at': created_at
                        }
                        logs_batch.append(log)

                    self._insert_audit_logs_batch(logs_batch)

                    with self.lock:
                        self.stats['audit_logs_generated'] += current_batch_size

                    pbar.update(current_batch_size)

            self.logger.info(f"操作日志生成完成: {self.stats['audit_logs_generated']} 条记录")
            return True

        except Exception as e:
            self.logger.error(f"操作日志生成失败: {str(e)}")
            self.stats['errors'].append(f"操作日志生成错误: {str(e)}")
            return False

    def _insert_audit_logs_batch(self, logs: List[Dict[str, Any]]):
        """批量插入操作日志"""
        sql = """
        INSERT INTO audit_logs (
            user_id, action_type, resource_type, resource_id, action_result,
            ip_address, user_agent, request_data, response_data, error_message, created_at
        ) VALUES (
            %(user_id)s, %(action_type)s, %(resource_type)s, %(resource_id)s, %(action_result)s,
            %(ip_address)s, %(user_agent)s, %(request_data)s, %(response_data)s, %(error_message)s, %(created_at)s
        )
        """
        self.db_manager.execute_batch(sql, logs)

    def generate_all_data(self) -> bool:
        """生成所有测试数据"""
        self.logger.info("开始生成所有测试数据...")
        self.stats['start_time'] = datetime.now()

        success = True

        # 按依赖顺序生成数据
        steps = [
            ("用户数据", self.generate_users),
            ("角色数据", self.generate_roles),
            ("权限数据", self.generate_permissions),
            ("用户角色关联", self.generate_user_roles),
            ("角色权限关联", self.generate_role_permissions),
            ("操作日志", self.generate_audit_logs)
        ]

        for step_name, step_func in steps:
            self.logger.info(f"执行步骤: {step_name}")
            if not step_func():
                self.logger.error(f"步骤失败: {step_name}")
                success = False
                break

            # 短暂休息，避免数据库压力过大
            time.sleep(1)

        self.stats['end_time'] = datetime.now()

        # 输出统计信息
        self._print_statistics()

        return success

    def _print_statistics(self):
        """打印统计信息"""
        duration = self.stats['end_time'] - self.stats['start_time']

        print("\n" + "="*60)
        print("📊 数据生成统计报告")
        print("="*60)
        print(f"开始时间: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"结束时间: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration}")
        print()
        print("生成数据统计:")
        print(f"  用户数据: {self.stats['users_generated']:,} 条")
        print(f"  角色数据: {self.stats['roles_generated']:,} 条")
        print(f"  权限数据: {self.stats['permissions_generated']:,} 条")
        print(f"  用户角色关联: {self.stats['user_roles_generated']:,} 条")
        print(f"  角色权限关联: {self.stats['role_permissions_generated']:,} 条")
        print(f"  操作日志: {self.stats['audit_logs_generated']:,} 条")

        total_records = sum([
            self.stats['users_generated'],
            self.stats['roles_generated'],
            self.stats['permissions_generated'],
            self.stats['user_roles_generated'],
            self.stats['role_permissions_generated'],
            self.stats['audit_logs_generated']
        ])

        print(f"\n总记录数: {total_records:,} 条")

        if duration.total_seconds() > 0:
            rate = total_records / duration.total_seconds()
            print(f"生成速率: {rate:.2f} 条/秒")

        if self.stats['errors']:
            print(f"\n❌ 错误数量: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"  - {error}")
        else:
            print("\n✅ 数据生成完成，无错误")

        print("="*60)

    def cleanup_data(self):
        """清理测试数据"""
        self.logger.info("开始清理测试数据...")

        tables = [
            'audit_logs',
            'role_permissions',
            'user_roles',
            'permissions',
            'roles',
            'users'
        ]

        try:
            for table in tables:
                sql = f"DELETE FROM {table} WHERE id > 0"
                affected = self.db_manager.execute_update(sql)
                self.logger.info(f"清理表 {table}: {affected} 条记录")

            # 重置自增ID
            for table in tables:
                sql = f"ALTER TABLE {table} AUTO_INCREMENT = 1"
                self.db_manager.execute_update(sql)

            self.logger.info("数据清理完成")

        except Exception as e:
            self.logger.error(f"数据清理失败: {str(e)}")

    def close(self):
        """关闭数据库连接"""
        if self.db_manager:
            self.db_manager.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='RBAC权限系统测试数据生成器')
    parser.add_argument('--env', default='development', help='配置环境')
    parser.add_argument('--scenario', default='standard_test', help='测试场景')
    parser.add_argument('--cleanup', action='store_true', help='清理现有数据')
    parser.add_argument('--users-only', action='store_true', help='只生成用户数据')

    args = parser.parse_args()

    generator = DataGenerator(args.env, args.scenario)

    try:
        if args.cleanup:
            generator.cleanup_data()

        if args.users_only:
            success = generator.generate_users()
        else:
            success = generator.generate_all_data()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n用户中断操作")
        return 1
    except Exception as e:
        print(f"程序异常: {str(e)}")
        return 1
    finally:
        generator.close()


if __name__ == "__main__":
    sys.exit(main())
