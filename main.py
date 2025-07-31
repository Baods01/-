#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBAC权限系统测试主程序
整合数据生成、性能测试和报告生成功能

作者：RBAC权限系统
创建时间：2025-07-17
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any
import logging
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import click
    from tqdm import tqdm
except ImportError as e:
    print(f"缺少依赖包: {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)

from scripts.data_generator import DataGenerator
from scripts.performance_test import PerformanceTest
from scripts.report_generator import ReportGenerator
from config.test_config import get_config, get_scenario, TEST_SCENARIOS


class RBACTestSuite:
    """RBAC权限系统测试套件"""
    
    def __init__(self, config_env: str = 'development', scenario: str = 'standard_test'):
        """
        初始化测试套件
        
        Args:
            config_env: 配置环境
            scenario: 测试场景
        """
        self.config_env = config_env
        self.scenario = scenario
        self.config = get_config(config_env)
        self.scenario_config = get_scenario(scenario)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化组件
        self.data_generator = None
        self.performance_tester = None
        self.report_generator = None
        
        # 测试结果
        self.results = {
            'data_generation': {},
            'performance_test': {},
            'start_time': None,
            'end_time': None,
            'scenario': scenario,
            'config_env': config_env
        }
        
        self.logger.info(f"RBAC测试套件初始化完成 - 环境: {config_env}, 场景: {scenario}")
    
    def _setup_logging(self):
        """设置日志"""
        log_config = self.config.LOGGING
        
        # 创建日志目录
        log_dir = os.path.dirname(log_config['file'])
        os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format=log_config['format'],
            handlers=[
                logging.FileHandler(log_config['file']),
                logging.StreamHandler() if log_config['console_output'] else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_data_generation(self, cleanup_first: bool = False) -> bool:
        """
        运行数据生成

        Args:
            cleanup_first: 是否先清理现有数据

        Returns:
            bool: 是否成功
        """
        self.logger.info("开始数据生成阶段...")

        try:
            self.data_generator = DataGenerator(self.config_env, self.scenario)

            if cleanup_first:
                self.logger.info("清理现有测试数据...")
                self.data_generator.cleanup_data()

            # 生成数据
            success = self.data_generator.generate_all_data()

            # 保存统计信息
            self.results['data_generation'] = self.data_generator.stats.copy()

            if success:
                self.logger.info("数据生成完成")
            else:
                self.logger.error("数据生成失败")

            return success

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"数据生成异常: {error_msg}")

            # 检查是否是数据库连接问题
            if "无法连接到数据库" in error_msg or "Can't connect to MySQL" in error_msg:
                print("❌ 数据库连接失败")
                print("💡 请检查以下事项：")
                print("   1. MySQL服务是否已启动")
                print("   2. 数据库连接配置是否正确")
                print("   3. 数据库用户权限是否足够")
                print(f"   4. 当前配置: {self.config.DATABASE['host']}:{self.config.DATABASE['port']}/{self.config.DATABASE['database']}")
            else:
                print(f"❌ 数据生成失败: {error_msg}")

            return False
        finally:
            if self.data_generator:
                self.data_generator.close()
    
    def run_performance_test(self) -> bool:
        """
        运行性能测试

        Returns:
            bool: 是否成功
        """
        self.logger.info("开始性能测试阶段...")

        try:
            self.performance_tester = PerformanceTest(self.config_env)

            # 运行性能测试
            test_results = self.performance_tester.run_all_tests()

            # 保存测试结果
            self.results['performance_test'] = test_results

            self.logger.info("性能测试完成")
            return True

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"性能测试异常: {error_msg}")

            # 检查是否是数据库连接问题
            if "无法连接到数据库" in error_msg or "Can't connect to MySQL" in error_msg:
                print("❌ 数据库连接失败")
                print("💡 请检查MySQL服务是否已启动")
            elif "没有找到测试用户数据" in error_msg:
                print("❌ 没有找到测试数据")
                print("💡 请先运行数据生成: python main.py --data-only")
            else:
                print(f"❌ 性能测试失败: {error_msg}")

            return False
        finally:
            if self.performance_tester:
                self.performance_tester.close()
    
    def generate_report(self) -> Dict[str, str]:
        """
        生成测试报告
        
        Returns:
            Dict[str, str]: 生成的报告文件路径
        """
        self.logger.info("开始生成测试报告...")
        
        try:
            self.report_generator = ReportGenerator(self.config_env)
            
            # 生成完整报告
            report_files = self.report_generator.generate_complete_report(
                self.results['performance_test'],
                self.results['data_generation']
            )
            
            self.logger.info("测试报告生成完成")
            return report_files
            
        except Exception as e:
            self.logger.error(f"报告生成异常: {str(e)}")
            return {}
    
    def run_full_test_suite(self, cleanup_first: bool = False) -> bool:
        """
        运行完整的测试套件
        
        Args:
            cleanup_first: 是否先清理现有数据
            
        Returns:
            bool: 是否成功
        """
        self.logger.info("开始运行完整测试套件...")
        self.results['start_time'] = datetime.now()
        
        success = True
        
        try:
            # 阶段1: 数据生成
            print("🗄️  阶段1: 生成测试数据")
            if not self.run_data_generation(cleanup_first):
                print("❌ 数据生成失败")
                success = False
                return success
            print("✅ 数据生成完成")
            
            # 短暂休息
            time.sleep(2)
            
            # 阶段2: 性能测试
            print("\n⚡ 阶段2: 执行性能测试")
            if not self.run_performance_test():
                print("❌ 性能测试失败")
                success = False
                return success
            print("✅ 性能测试完成")
            
            # 短暂休息
            time.sleep(1)
            
            # 阶段3: 生成报告
            print("\n📊 阶段3: 生成测试报告")
            report_files = self.generate_report()
            if not report_files:
                print("❌ 报告生成失败")
                success = False
                return success
            
            print("✅ 报告生成完成")
            print(f"📄 HTML报告: {report_files.get('html', '未生成')}")
            print(f"📄 JSON报告: {report_files.get('json', '未生成')}")
            
            return success
            
        except KeyboardInterrupt:
            print("\n⚠️  用户中断测试")
            success = False
            return success
        except Exception as e:
            self.logger.error(f"测试套件执行异常: {str(e)}")
            print(f"❌ 测试异常: {str(e)}")
            success = False
            return success
        finally:
            self.results['end_time'] = datetime.now()
            self._print_final_summary(success)
    
    def _print_final_summary(self, success: bool):
        """打印最终摘要"""
        duration = self.results['end_time'] - self.results['start_time']
        
        print("\n" + "="*60)
        print("📋 RBAC权限系统测试套件执行摘要")
        print("="*60)
        print(f"测试场景: {self.scenario}")
        print(f"配置环境: {self.config_env}")
        print(f"开始时间: {self.results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"结束时间: {self.results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration}")
        print(f"执行状态: {'✅ 成功' if success else '❌ 失败'}")
        
        # 数据生成摘要
        if self.results['data_generation']:
            data_stats = self.results['data_generation']
            print(f"\n📊 数据生成统计:")
            print(f"  用户: {data_stats.get('users_generated', 0):,} 条")
            print(f"  角色: {data_stats.get('roles_generated', 0):,} 条")
            print(f"  权限: {data_stats.get('permissions_generated', 0):,} 条")
            print(f"  关联关系: {data_stats.get('user_roles_generated', 0) + data_stats.get('role_permissions_generated', 0):,} 条")
            print(f"  操作日志: {data_stats.get('audit_logs_generated', 0):,} 条")
        
        # 性能测试摘要
        if self.results['performance_test']:
            perf_stats = self.results['performance_test']
            print(f"\n⚡ 性能测试结果:")
            
            # 认证性能
            if 'authentication' in perf_stats and perf_stats['authentication'].get('single_login'):
                auth = perf_stats['authentication']['single_login']
                print(f"  登录响应时间: {auth['avg_time']*1000:.2f}ms (平均)")
            
            # 权限查询性能
            if 'permission_query' in perf_stats and perf_stats['permission_query'].get('single_query'):
                perm = perf_stats['permission_query']['single_query']
                print(f"  权限查询时间: {perm['avg_time']*1000:.2f}ms (平均)")
            
            # 压力测试
            if 'stress_test' in perf_stats and perf_stats['stress_test']:
                stress = perf_stats['stress_test']
                print(f"  系统吞吐量: {stress.get('operations_per_second', 0):.2f} ops/s")
                print(f"  错误率: {stress.get('error_rate', 0)*100:.2f}%")
        
        print("="*60)


@click.command()
@click.option('--env', default='development', help='配置环境 (development/testing/production)')
@click.option('--scenario', default='standard_test', 
              type=click.Choice(list(TEST_SCENARIOS.keys())), 
              help='测试场景')
@click.option('--cleanup', is_flag=True, help='清理现有测试数据')
@click.option('--data-only', is_flag=True, help='只执行数据生成')
@click.option('--test-only', is_flag=True, help='只执行性能测试')
@click.option('--report-only', is_flag=True, help='只生成报告')
@click.option('--test-results', help='测试结果JSON文件路径 (用于report-only)')
@click.option('--data-stats', help='数据生成统计JSON文件路径 (用于report-only)')
@click.option('--check-db', is_flag=True, help='检查数据库连接和表结构')
@click.option('--simulation', is_flag=True, help='模拟模式（无需数据库）')
def main(env, scenario, cleanup, data_only, test_only, report_only, test_results, data_stats, check_db, simulation):
    """RBAC权限系统测试主程序"""
    
    print("🚀 RBAC权限系统测试套件")
    print("="*50)
    print(f"环境: {env}")
    print(f"场景: {scenario}")
    print(f"场景描述: {TEST_SCENARIOS[scenario]['description']}")
    print("="*50)

    if simulation:
        # 模拟模式
        print("🎭 启动模拟模式（无需数据库）")
        print("="*50)

        from scripts.simulation_mode import SimulationDataGenerator, SimulationPerformanceTest, create_simulation_report

        try:
            if data_only:
                # 只模拟数据生成
                generator = SimulationDataGenerator(env, scenario)
                if cleanup:
                    generator.cleanup_data()
                success = generator.generate_all_data()
                return 0 if success else 1

            elif test_only:
                # 只模拟性能测试
                tester = SimulationPerformanceTest(env)
                results = tester.run_all_tests()

                # 保存结果
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"reports/simulation_performance_{timestamp}.json"
                os.makedirs('reports', exist_ok=True)

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

                print(f"📄 模拟测试结果已保存到: {output_file}")
                return 0

            else:
                # 完整模拟测试
                print("🎭 运行完整模拟测试套件...")

                # 数据生成
                print("\n📊 阶段1: 模拟数据生成")
                generator = SimulationDataGenerator(env, scenario)
                if cleanup:
                    generator.cleanup_data()
                data_success = generator.generate_all_data()

                if not data_success:
                    print("❌ 模拟数据生成失败")
                    return 1

                # 性能测试
                print("\n⚡ 阶段2: 模拟性能测试")
                tester = SimulationPerformanceTest(env)
                test_results = tester.run_all_tests()

                # 生成报告
                print("\n📄 阶段3: 生成模拟报告")
                report_file = create_simulation_report(test_results, generator.stats)

                print(f"\n🎉 模拟测试完成！")
                print(f"📄 报告文件: {report_file}")
                return 0

        except Exception as e:
            print(f"❌ 模拟模式异常: {str(e)}")
            return 1

    if check_db:
        # 数据库检查
        from check_database import check_database_connection, check_table_structure, check_test_data

        success = True
        success &= check_database_connection(env)
        if success:
            success &= check_table_structure(env)
        if success:
            success &= check_test_data(env)

        if success:
            print("\n🎉 数据库检查通过！")
        else:
            print("\n❌ 数据库检查失败！")

        return 0 if success else 1

    if report_only:
        # 只生成报告
        if not test_results:
            print("❌ 生成报告需要指定 --test-results 参数")
            return 1
        
        try:
            with open(test_results, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except Exception as e:
            print(f"❌ 加载测试结果失败: {e}")
            return 1
        
        data_generation_stats = None
        if data_stats:
            try:
                with open(data_stats, 'r', encoding='utf-8') as f:
                    data_generation_stats = json.load(f)
            except Exception as e:
                print(f"⚠️  加载数据生成统计失败: {e}")
        
        generator = ReportGenerator(env)
        report_files = generator.generate_complete_report(results, data_generation_stats)
        
        if report_files:
            print(f"✅ 报告生成完成")
            print(f"📄 HTML报告: {report_files.get('html', '未生成')}")
            print(f"📄 JSON报告: {report_files.get('json', '未生成')}")
            return 0
        else:
            print("❌ 报告生成失败")
            return 1
    
    # 创建测试套件
    test_suite = RBACTestSuite(env, scenario)
    
    try:
        if data_only:
            # 只执行数据生成
            success = test_suite.run_data_generation(cleanup)
        elif test_only:
            # 只执行性能测试
            success = test_suite.run_performance_test()
        else:
            # 执行完整测试套件
            success = test_suite.run_full_test_suite(cleanup)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        return 1
    except Exception as e:
        print(f"❌ 程序异常: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
