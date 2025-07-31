#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限系统测试配置文件
包含数据生成和性能测试的所有配置参数

作者：RBAC权限系统
创建时间：2025-07-17
"""

import os
from typing import Dict, List, Any


class TestConfig:
    """测试配置类"""
    
    # 系统配置
    SIMULATION_MODE = os.getenv('RBAC_SIMULATION', 'false').lower() == 'true'

    # 数据库配置
    DATABASE = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'rbac_system'),
        'charset': 'utf8mb4'
    }
    
    # 连接池配置
    CONNECTION_POOL = {
        'min_connections': 10,
        'max_connections': 50,
        'connection_timeout': 30,
        'idle_timeout': 3600
    }
    
    # 数据生成配置
    DATA_GENERATION = {
        'users': {
            'count': 100000,
            'batch_size': 1000,
            'default_password': 'password123',
            'status_distribution': {
                'active': 0.9,    # 90% 启用
                'inactive': 0.1   # 10% 禁用
            }
        },
        'roles': {
            'count': 1000,
            'batch_size': 100,
            'categories': [
                'admin', 'manager', 'editor', 'viewer', 'guest',
                'moderator', 'analyst', 'operator', 'supervisor', 'coordinator'
            ]
        },
        'permissions': {
            'count': 5000,
            'batch_size': 200,
            'modules': [
                'user', 'role', 'permission', 'system', 'content',
                'report', 'audit', 'setting', 'notification', 'file'
            ],
            'actions': ['view', 'create', 'edit', 'delete', 'export', 'import', 'approve']
        },
        'user_roles': {
            'avg_roles_per_user': 4,
            'min_roles': 1,
            'max_roles': 8,
            'batch_size': 2000
        },
        'role_permissions': {
            'avg_permissions_per_role': 15,
            'min_permissions': 5,
            'max_permissions': 30,
            'batch_size': 1000
        },
        'audit_logs': {
            'count': 1000000,
            'batch_size': 5000,
            'action_types': [
                'login', 'logout', 'create_user', 'update_user', 'delete_user',
                'assign_role', 'revoke_role', 'grant_permission', 'revoke_permission',
                'view_data', 'export_data', 'system_config'
            ],
            'success_rate': 0.95  # 95% 成功操作
        }
    }
    
    # 性能测试配置
    PERFORMANCE_TEST = {
        'authentication': {
            'single_login_tests': 100,
            'concurrent_tests': [100, 500, 1000],
            'timeout': 30,
            'expected_response_time': 0.5  # 500ms
        },
        'permission_query': {
            'single_query_tests': 1000,
            'batch_query_sizes': [10, 50, 100, 500],
            'concurrent_users': [50, 100, 200],
            'expected_response_time': 0.05,  # 50ms
            'timeout': 10
        },
        'data_operations': {
            'crud_test_count': 500,
            'batch_sizes': [10, 50, 100, 500, 1000],
            'concurrent_operations': [10, 50, 100],
            'timeout': 60
        },
        'stress_test': {
            'duration_minutes': 30,
            'concurrent_users': 200,
            'operations_per_minute': 1000,
            'ramp_up_time': 300,  # 5分钟
            'cool_down_time': 300  # 5分钟
        }
    }
    
    # 报告配置
    REPORT = {
        'output_dir': 'reports',
        'formats': ['html', 'json'],
        'include_charts': True,
        'chart_types': ['line', 'bar', 'histogram'],
        'template_dir': 'templates',
        'static_dir': 'static'
    }
    
    # 日志配置
    LOGGING = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'logs/test.log',
        'max_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'console_output': True,
        'color_output': True
    }
    
    # Faker配置
    FAKER = {
        'locale': 'zh_CN',
        'providers': [
            'faker.providers.person',
            'faker.providers.internet',
            'faker.providers.company',
            'faker.providers.address',
            'faker.providers.phone_number'
        ]
    }
    
    # 系统监控配置
    MONITORING = {
        'enabled': True,
        'interval': 5,  # 秒
        'metrics': [
            'cpu_usage',
            'memory_usage',
            'disk_io',
            'network_io',
            'database_connections'
        ]
    }


class EnvironmentConfig:
    """环境配置类"""
    
    @staticmethod
    def get_config(env: str = None) -> TestConfig:
        """
        根据环境获取配置
        
        Args:
            env: 环境名称 (development, testing, production)
            
        Returns:
            TestConfig: 配置对象
        """
        if env is None:
            env = os.getenv('RBAC_ENV', 'development')
        
        config = TestConfig()
        
        if env == 'testing':
            # 测试环境配置调整
            config.DATA_GENERATION['users']['count'] = 10000
            config.DATA_GENERATION['audit_logs']['count'] = 100000
            config.PERFORMANCE_TEST['stress_test']['duration_minutes'] = 5
            
        elif env == 'production':
            # 生产环境配置调整
            config.CONNECTION_POOL['max_connections'] = 100
            config.PERFORMANCE_TEST['stress_test']['duration_minutes'] = 60
            config.LOGGING['level'] = 'WARNING'
            
        return config


# 预定义的测试场景
TEST_SCENARIOS = {
    'quick_test': {
        'description': '快速测试场景',
        'data_scale': {
            'users': 1000,
            'roles': 50,
            'permissions': 200,
            'audit_logs': 10000
        },
        'performance_tests': ['authentication', 'permission_query']
    },
    'standard_test': {
        'description': '标准测试场景',
        'data_scale': {
            'users': 50000,
            'roles': 500,
            'permissions': 2500,
            'audit_logs': 500000
        },
        'performance_tests': ['authentication', 'permission_query', 'data_operations']
    },
    'full_test': {
        'description': '完整测试场景',
        'data_scale': {
            'users': 100000,
            'roles': 1000,
            'permissions': 5000,
            'audit_logs': 1000000
        },
        'performance_tests': ['authentication', 'permission_query', 'data_operations', 'stress_test']
    }
}

# 性能基准值
PERFORMANCE_BENCHMARKS = {
    'login_response_time': 0.5,      # 500ms
    'permission_query_time': 0.05,   # 50ms
    'user_creation_time': 0.1,       # 100ms
    'role_assignment_time': 0.05,    # 50ms
    'concurrent_users_supported': 1000,
    'queries_per_second': 10000,
    'database_connection_pool_efficiency': 0.8  # 80%
}

# 错误处理配置
ERROR_HANDLING = {
    'max_retries': 3,
    'retry_delay': 1,  # 秒
    'timeout_multiplier': 1.5,
    'critical_errors': [
        'DatabaseConnectionError',
        'OutOfMemoryError',
        'DiskSpaceError'
    ],
    'recoverable_errors': [
        'TimeoutError',
        'TemporaryConnectionError',
        'RateLimitError'
    ]
}


# 导出配置实例
default_config = TestConfig()

# 便捷函数
def get_config(env: str = None) -> TestConfig:
    """获取配置实例"""
    return EnvironmentConfig.get_config(env)

def get_scenario(name: str) -> Dict[str, Any]:
    """获取测试场景配置"""
    return TEST_SCENARIOS.get(name, TEST_SCENARIOS['standard_test'])

def get_benchmark(metric: str) -> float:
    """获取性能基准值"""
    return PERFORMANCE_BENCHMARKS.get(metric, 0.0)
