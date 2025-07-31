#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限系统测试报告生成器
生成HTML和JSON格式的详细测试报告

作者：RBAC权限系统
创建时间：2025-07-17
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from jinja2 import Template, Environment, FileSystemLoader
except ImportError:
    print("缺少依赖包: jinja2")
    print("请运行: pip install jinja2")
    sys.exit(1)

from config.test_config import get_config


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, config_env: str = None):
        """
        初始化报告生成器
        
        Args:
            config_env: 配置环境
        """
        self.config = get_config(config_env)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 创建输出目录
        self.output_dir = self.config.REPORT['output_dir']
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger.info("报告生成器初始化完成")
    
    def generate_html_report(self, test_results: Dict[str, Any], 
                           data_generation_stats: Dict[str, Any] = None) -> str:
        """
        生成HTML格式的测试报告
        
        Args:
            test_results: 性能测试结果
            data_generation_stats: 数据生成统计
            
        Returns:
            str: 生成的HTML文件路径
        """
        self.logger.info("生成HTML测试报告...")
        
        # HTML模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RBAC权限系统测试报告</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
        }
        .header .subtitle {
            color: #666;
            margin-top: 10px;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #333;
            border-left: 4px solid #007bff;
            padding-left: 15px;
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #28a745;
        }
        .metric-card.warning {
            border-left-color: #ffc107;
        }
        .metric-card.danger {
            border-left-color: #dc3545;
        }
        .metric-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        .metric-unit {
            font-size: 14px;
            color: #666;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .table th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }
        .table tr:hover {
            background-color: #f5f5f5;
        }
        .status-success {
            color: #28a745;
            font-weight: bold;
        }
        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        .status-danger {
            color: #dc3545;
            font-weight: bold;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }
        .chart-placeholder {
            height: 300px;
            background: #f8f9fa;
            border: 2px dashed #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RBAC权限系统测试报告</h1>
            <div class="subtitle">
                生成时间: {{ report_time }}<br>
                测试环境: {{ test_env }}
            </div>
        </div>

        <!-- 测试概览 -->
        <div class="section">
            <h2>📊 测试概览</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">测试开始时间</div>
                    <div class="metric-value">{{ test_results.start_time or '未知' }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">测试结束时间</div>
                    <div class="metric-value">{{ test_results.end_time or '未知' }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">总测试时长</div>
                    <div class="metric-value">{{ test_duration }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">测试状态</div>
                    <div class="metric-value status-success">完成</div>
                </div>
            </div>
        </div>

        {% if data_generation_stats %}
        <!-- 数据生成统计 -->
        <div class="section">
            <h2>🗄️ 测试数据生成统计</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">用户数据</div>
                    <div class="metric-value">{{ "{:,}".format(data_generation_stats.users_generated or 0) }}</div>
                    <div class="metric-unit">条记录</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">角色数据</div>
                    <div class="metric-value">{{ "{:,}".format(data_generation_stats.roles_generated or 0) }}</div>
                    <div class="metric-unit">条记录</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">权限数据</div>
                    <div class="metric-value">{{ "{:,}".format(data_generation_stats.permissions_generated or 0) }}</div>
                    <div class="metric-unit">条记录</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">关联关系</div>
                    <div class="metric-value">{{ "{:,}".format((data_generation_stats.user_roles_generated or 0) + (data_generation_stats.role_permissions_generated or 0)) }}</div>
                    <div class="metric-unit">条记录</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">操作日志</div>
                    <div class="metric-value">{{ "{:,}".format(data_generation_stats.audit_logs_generated or 0) }}</div>
                    <div class="metric-unit">条记录</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">生成耗时</div>
                    <div class="metric-value">{{ data_generation_duration }}</div>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- 用户认证测试 -->
        {% if test_results.authentication %}
        <div class="section">
            <h2>🔐 用户认证性能测试</h2>
            {% set auth = test_results.authentication %}
            
            {% if auth.single_login %}
            <h3>单次登录测试</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">平均响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(auth.single_login.avg_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">P95响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(auth.single_login.p95_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">最快响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(auth.single_login.min_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">最慢响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(auth.single_login.max_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
            </div>
            {% endif %}

            {% if auth.concurrent_login %}
            <h3>并发登录测试</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>并发用户数</th>
                        <th>总耗时(秒)</th>
                        <th>平均响应时间(毫秒)</th>
                        <th>每秒请求数</th>
                        <th>成功率</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, result in auth.concurrent_login.items() %}
                    <tr>
                        <td>{{ result.concurrent_users }}</td>
                        <td>{{ "%.2f"|format(result.total_time) }}</td>
                        <td>{{ "%.2f"|format(result.avg_time_per_request * 1000) }}</td>
                        <td>{{ "%.2f"|format(result.requests_per_second) }}</td>
                        <td class="{% if result.success_rate >= 0.95 %}status-success{% elif result.success_rate >= 0.9 %}status-warning{% else %}status-danger{% endif %}">
                            {{ "%.1f"|format(result.success_rate * 100) }}%
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
        {% endif %}

        <!-- 权限查询测试 -->
        {% if test_results.permission_query %}
        <div class="section">
            <h2>🔍 权限查询性能测试</h2>
            {% set perm = test_results.permission_query %}
            
            {% if perm.single_query %}
            <h3>单用户权限查询</h3>
            <div class="metrics-grid">
                <div class="metric-card {% if perm.single_query.avg_time <= 0.05 %}{% elif perm.single_query.avg_time <= 0.1 %}warning{% else %}danger{% endif %}">
                    <div class="metric-title">平均响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(perm.single_query.avg_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">P95响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(perm.single_query.p95_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">测试次数</div>
                    <div class="metric-value">{{ "{:,}".format(perm.single_query.count) }}</div>
                    <div class="metric-unit">次</div>
                </div>
            </div>
            {% endif %}

            {% if perm.batch_query %}
            <h3>批量权限查询</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>批量大小</th>
                        <th>平均总时间(毫秒)</th>
                        <th>平均单用户时间(毫秒)</th>
                        <th>最快时间(毫秒)</th>
                        <th>最慢时间(毫秒)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, result in perm.batch_query.items() %}
                    <tr>
                        <td>{{ result.batch_size }}</td>
                        <td>{{ "%.2f"|format(result.avg_time * 1000) }}</td>
                        <td>{{ "%.2f"|format(result.avg_time_per_user * 1000) }}</td>
                        <td>{{ "%.2f"|format(result.min_time * 1000) }}</td>
                        <td>{{ "%.2f"|format(result.max_time * 1000) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
        {% endif %}

        <!-- 数据操作测试 -->
        {% if test_results.data_operations %}
        <div class="section">
            <h2>💾 数据操作性能测试</h2>
            {% set data_ops = test_results.data_operations %}
            
            {% if data_ops.user_crud %}
            <h3>用户CRUD操作</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>操作类型</th>
                        <th>测试次数</th>
                        <th>平均时间(毫秒)</th>
                        <th>最快时间(毫秒)</th>
                        <th>最慢时间(毫秒)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for operation, result in data_ops.user_crud.items() %}
                    <tr>
                        <td>{{ operation.upper() }}</td>
                        <td>{{ result.count }}</td>
                        <td>{{ "%.2f"|format(result.avg_time * 1000) }}</td>
                        <td>{{ "%.2f"|format(result.min_time * 1000) }}</td>
                        <td>{{ "%.2f"|format(result.max_time * 1000) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}

            {% if data_ops.batch_operations %}
            <h3>批量操作性能</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>批量大小</th>
                        <th>总时间(秒)</th>
                        <th>单条记录时间(毫秒)</th>
                        <th>每秒处理记录数</th>
                    </tr>
                </thead>
                <tbody>
                    {% for key, result in data_ops.batch_operations.items() %}
                    <tr>
                        <td>{{ result.batch_size }}</td>
                        <td>{{ "%.3f"|format(result.total_time) }}</td>
                        <td>{{ "%.2f"|format(result.time_per_record * 1000) }}</td>
                        <td>{{ "%.0f"|format(result.records_per_second) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
        {% endif %}

        <!-- 压力测试 -->
        {% if test_results.stress_test %}
        <div class="section">
            <h2>⚡ 系统压力测试</h2>
            {% set stress = test_results.stress_test %}
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">测试时长</div>
                    <div class="metric-value">{{ stress.duration_minutes }}</div>
                    <div class="metric-unit">分钟</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">并发用户数</div>
                    <div class="metric-value">{{ stress.concurrent_users }}</div>
                    <div class="metric-unit">用户</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">总操作数</div>
                    <div class="metric-value">{{ "{:,}".format(stress.total_operations) }}</div>
                    <div class="metric-unit">次</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">成功操作数</div>
                    <div class="metric-value">{{ "{:,}".format(stress.successful_operations) }}</div>
                    <div class="metric-unit">次</div>
                </div>
                <div class="metric-card {% if stress.error_rate <= 0.01 %}{% elif stress.error_rate <= 0.05 %}warning{% else %}danger{% endif %}">
                    <div class="metric-title">错误率</div>
                    <div class="metric-value">{{ "%.2f"|format(stress.error_rate * 100) }}</div>
                    <div class="metric-unit">%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">每秒操作数</div>
                    <div class="metric-value">{{ "%.2f"|format(stress.operations_per_second) }}</div>
                    <div class="metric-unit">ops/s</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">平均响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(stress.avg_response_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">最大响应时间</div>
                    <div class="metric-value">{{ "%.2f"|format(stress.max_response_time * 1000) }}</div>
                    <div class="metric-unit">毫秒</div>
                </div>
            </div>
        </div>
        {% endif %}

        <div class="footer">
            <p>RBAC权限系统测试报告 - 生成于 {{ report_time }}</p>
            <p>测试工具版本: v1.0.0</p>
        </div>
    </div>
</body>
</html>
        """
        
        # 准备模板数据
        template_data = {
            'test_results': test_results,
            'data_generation_stats': data_generation_stats,
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_env': 'Development',
            'test_duration': self._calculate_duration(test_results.get('start_time'), test_results.get('end_time')),
            'data_generation_duration': self._calculate_duration(
                data_generation_stats.get('start_time') if data_generation_stats else None,
                data_generation_stats.get('end_time') if data_generation_stats else None
            )
        }
        
        # 渲染模板
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        # 保存HTML文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = os.path.join(self.output_dir, f'test_report_{timestamp}.html')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML报告生成完成: {html_file}")
        return html_file

    def generate_json_report(self, test_results: Dict[str, Any],
                           data_generation_stats: Dict[str, Any] = None) -> str:
        """
        生成JSON格式的测试报告

        Args:
            test_results: 性能测试结果
            data_generation_stats: 数据生成统计

        Returns:
            str: 生成的JSON文件路径
        """
        self.logger.info("生成JSON测试报告...")

        # 准备报告数据
        report_data = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'generator_version': '1.0.0',
                'test_environment': 'development'
            },
            'test_results': test_results,
            'data_generation_stats': data_generation_stats,
            'summary': self._generate_summary(test_results, data_generation_stats)
        }

        # 保存JSON文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = os.path.join(self.output_dir, f'test_report_{timestamp}.json')

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"JSON报告生成完成: {json_file}")
        return json_file

    def _generate_summary(self, test_results: Dict[str, Any],
                         data_generation_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """生成测试摘要"""
        summary = {
            'test_status': 'completed',
            'total_test_time': self._calculate_duration(
                test_results.get('start_time'),
                test_results.get('end_time')
            ),
            'performance_metrics': {},
            'data_generation_metrics': {}
        }

        # 性能指标摘要
        if 'authentication' in test_results and test_results['authentication']:
            auth = test_results['authentication']
            if 'single_login' in auth:
                summary['performance_metrics']['avg_login_time_ms'] = auth['single_login']['avg_time'] * 1000
                summary['performance_metrics']['p95_login_time_ms'] = auth['single_login']['p95_time'] * 1000

        if 'permission_query' in test_results and test_results['permission_query']:
            perm = test_results['permission_query']
            if 'single_query' in perm:
                summary['performance_metrics']['avg_permission_query_time_ms'] = perm['single_query']['avg_time'] * 1000
                summary['performance_metrics']['p95_permission_query_time_ms'] = perm['single_query']['p95_time'] * 1000

        if 'stress_test' in test_results and test_results['stress_test']:
            stress = test_results['stress_test']
            summary['performance_metrics']['operations_per_second'] = stress.get('operations_per_second', 0)
            summary['performance_metrics']['error_rate'] = stress.get('error_rate', 0)
            summary['performance_metrics']['avg_response_time_ms'] = stress.get('avg_response_time', 0) * 1000

        # 数据生成指标摘要
        if data_generation_stats:
            summary['data_generation_metrics'] = {
                'total_users': data_generation_stats.get('users_generated', 0),
                'total_roles': data_generation_stats.get('roles_generated', 0),
                'total_permissions': data_generation_stats.get('permissions_generated', 0),
                'total_user_roles': data_generation_stats.get('user_roles_generated', 0),
                'total_role_permissions': data_generation_stats.get('role_permissions_generated', 0),
                'total_audit_logs': data_generation_stats.get('audit_logs_generated', 0),
                'generation_duration': self._calculate_duration(
                    data_generation_stats.get('start_time'),
                    data_generation_stats.get('end_time')
                )
            }

        return summary

    def _calculate_duration(self, start_time: Any, end_time: Any) -> str:
        """计算时间间隔"""
        if not start_time or not end_time:
            return "未知"

        try:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

            duration = end_time - start_time

            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                return f"{int(hours)}小时{int(minutes)}分钟{int(seconds)}秒"
            elif minutes > 0:
                return f"{int(minutes)}分钟{int(seconds)}秒"
            else:
                return f"{duration.total_seconds():.2f}秒"

        except Exception:
            return "计算失败"

    def generate_performance_analysis(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成性能分析报告

        Args:
            test_results: 测试结果

        Returns:
            Dict[str, Any]: 性能分析结果
        """
        analysis = {
            'overall_rating': 'unknown',
            'bottlenecks': [],
            'recommendations': [],
            'benchmark_comparison': {}
        }

        # 基准值比较
        benchmarks = {
            'login_response_time': 0.5,      # 500ms
            'permission_query_time': 0.05,   # 50ms
            'operations_per_second': 1000,
            'error_rate_threshold': 0.01     # 1%
        }

        issues = []
        good_metrics = []

        # 分析登录性能
        if 'authentication' in test_results and test_results['authentication']:
            auth = test_results['authentication']
            if 'single_login' in auth:
                avg_time = auth['single_login']['avg_time']
                if avg_time > benchmarks['login_response_time']:
                    issues.append(f"登录响应时间过长: {avg_time*1000:.2f}ms (基准: {benchmarks['login_response_time']*1000}ms)")
                    analysis['bottlenecks'].append('用户认证性能')
                else:
                    good_metrics.append('登录响应时间')

                analysis['benchmark_comparison']['login_time'] = {
                    'actual': avg_time * 1000,
                    'benchmark': benchmarks['login_response_time'] * 1000,
                    'status': 'pass' if avg_time <= benchmarks['login_response_time'] else 'fail'
                }

        # 分析权限查询性能
        if 'permission_query' in test_results and test_results['permission_query']:
            perm = test_results['permission_query']
            if 'single_query' in perm:
                avg_time = perm['single_query']['avg_time']
                if avg_time > benchmarks['permission_query_time']:
                    issues.append(f"权限查询时间过长: {avg_time*1000:.2f}ms (基准: {benchmarks['permission_query_time']*1000}ms)")
                    analysis['bottlenecks'].append('权限查询性能')
                else:
                    good_metrics.append('权限查询时间')

                analysis['benchmark_comparison']['permission_query_time'] = {
                    'actual': avg_time * 1000,
                    'benchmark': benchmarks['permission_query_time'] * 1000,
                    'status': 'pass' if avg_time <= benchmarks['permission_query_time'] else 'fail'
                }

        # 分析压力测试结果
        if 'stress_test' in test_results and test_results['stress_test']:
            stress = test_results['stress_test']

            ops_per_sec = stress.get('operations_per_second', 0)
            if ops_per_sec < benchmarks['operations_per_second']:
                issues.append(f"系统吞吐量不足: {ops_per_sec:.2f} ops/s (基准: {benchmarks['operations_per_second']} ops/s)")
                analysis['bottlenecks'].append('系统吞吐量')
            else:
                good_metrics.append('系统吞吐量')

            error_rate = stress.get('error_rate', 0)
            if error_rate > benchmarks['error_rate_threshold']:
                issues.append(f"错误率过高: {error_rate*100:.2f}% (基准: {benchmarks['error_rate_threshold']*100}%)")
                analysis['bottlenecks'].append('系统稳定性')
            else:
                good_metrics.append('系统稳定性')

            analysis['benchmark_comparison']['operations_per_second'] = {
                'actual': ops_per_sec,
                'benchmark': benchmarks['operations_per_second'],
                'status': 'pass' if ops_per_sec >= benchmarks['operations_per_second'] else 'fail'
            }

            analysis['benchmark_comparison']['error_rate'] = {
                'actual': error_rate * 100,
                'benchmark': benchmarks['error_rate_threshold'] * 100,
                'status': 'pass' if error_rate <= benchmarks['error_rate_threshold'] else 'fail'
            }

        # 生成总体评级
        if not issues:
            analysis['overall_rating'] = 'excellent'
        elif len(issues) <= 2:
            analysis['overall_rating'] = 'good'
        elif len(issues) <= 4:
            analysis['overall_rating'] = 'fair'
        else:
            analysis['overall_rating'] = 'poor'

        # 生成优化建议
        if '用户认证性能' in analysis['bottlenecks']:
            analysis['recommendations'].append('优化用户认证查询，考虑添加用户名索引或使用缓存')

        if '权限查询性能' in analysis['bottlenecks']:
            analysis['recommendations'].append('优化权限查询SQL，考虑创建复合索引或使用权限缓存')

        if '系统吞吐量' in analysis['bottlenecks']:
            analysis['recommendations'].append('增加数据库连接池大小，考虑读写分离或分库分表')

        if '系统稳定性' in analysis['bottlenecks']:
            analysis['recommendations'].append('检查错误日志，优化异常处理和重试机制')

        if not analysis['recommendations']:
            analysis['recommendations'].append('系统性能表现良好，建议定期监控和维护')

        return analysis

    def generate_complete_report(self, test_results: Dict[str, Any],
                               data_generation_stats: Dict[str, Any] = None) -> Dict[str, str]:
        """
        生成完整的测试报告（HTML + JSON）

        Args:
            test_results: 性能测试结果
            data_generation_stats: 数据生成统计

        Returns:
            Dict[str, str]: 生成的文件路径
        """
        self.logger.info("生成完整测试报告...")

        # 添加性能分析
        test_results['performance_analysis'] = self.generate_performance_analysis(test_results)

        # 生成HTML和JSON报告
        html_file = self.generate_html_report(test_results, data_generation_stats)
        json_file = self.generate_json_report(test_results, data_generation_stats)

        return {
            'html': html_file,
            'json': json_file
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='RBAC权限系统测试报告生成器')
    parser.add_argument('--test-results', required=True, help='测试结果JSON文件路径')
    parser.add_argument('--data-stats', help='数据生成统计JSON文件路径')
    parser.add_argument('--format', choices=['html', 'json', 'both'], default='both', help='报告格式')
    parser.add_argument('--env', default='development', help='配置环境')

    args = parser.parse_args()

    # 加载测试结果
    try:
        with open(args.test_results, 'r', encoding='utf-8') as f:
            test_results = json.load(f)
    except Exception as e:
        print(f"加载测试结果失败: {e}")
        return 1

    # 加载数据生成统计（可选）
    data_stats = None
    if args.data_stats:
        try:
            with open(args.data_stats, 'r', encoding='utf-8') as f:
                data_stats = json.load(f)
        except Exception as e:
            print(f"加载数据生成统计失败: {e}")

    # 生成报告
    generator = ReportGenerator(args.env)

    try:
        if args.format == 'html':
            html_file = generator.generate_html_report(test_results, data_stats)
            print(f"HTML报告生成完成: {html_file}")
        elif args.format == 'json':
            json_file = generator.generate_json_report(test_results, data_stats)
            print(f"JSON报告生成完成: {json_file}")
        else:  # both
            files = generator.generate_complete_report(test_results, data_stats)
            print(f"HTML报告: {files['html']}")
            print(f"JSON报告: {files['json']}")

        return 0

    except Exception as e:
        print(f"报告生成失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
