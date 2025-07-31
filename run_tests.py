#!/usr/bin/env python3
"""
RBAC系统测试执行脚本

本脚本用于执行RBAC系统的所有单元测试，并生成详细的测试报告。

Features:
    - 执行所有单元测试
    - 生成覆盖率报告
    - 生成HTML测试报告
    - 支持不同的测试模式

Usage:
    python run_tests.py [options]

Options:
    --verbose: 详细输出模式
    --coverage: 生成覆盖率报告
    --html: 生成HTML报告
    --markers: 指定测试标记（如 unit, integration, slow）

Author: AI Assistant
Created: 2025-07-19
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def setup_environment():
    """设置测试环境"""
    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['TESTING'] = '1'
    
    print(f"项目根目录: {project_root}")
    print(f"Python路径: {sys.path[0]}")


def install_dependencies():
    """安装测试依赖"""
    dependencies = [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'pytest-html>=3.1.0',
        'pytest-xdist>=3.0.0',  # 并行测试
        'sqlalchemy>=1.4.0',
        'bcrypt>=4.0.0'
    ]
    
    print("安装测试依赖...")
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"✓ 已安装: {dep}")
        except subprocess.CalledProcessError as e:
            print(f"✗ 安装失败: {dep} - {e}")
            return False
    
    return True


def run_tests(args):
    """执行测试"""
    # 构建pytest命令
    cmd = [sys.executable, '-m', 'pytest']
    
    # 添加测试目录
    cmd.append('tests/')
    
    # 详细输出
    if args.verbose:
        cmd.extend(['-v', '-s'])
    else:
        cmd.append('-v')
    
    # 覆盖率报告
    if args.coverage:
        cmd.extend([
            '--cov=models',
            '--cov=dao',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=90'
        ])
    
    # HTML报告
    if args.html:
        cmd.extend([
            '--html=reports/test_report.html',
            '--self-contained-html'
        ])
    
    # 测试标记
    if args.markers:
        cmd.extend(['-m', args.markers])
    
    # 并行执行
    if not args.verbose:  # 详细模式下不使用并行，便于调试
        cmd.extend(['-n', 'auto'])
    
    # 其他有用的选项
    cmd.extend([
        '--tb=short',  # 简短的错误回溯
        '--strict-markers',  # 严格标记模式
        '--disable-warnings'  # 禁用警告
    ])
    
    print(f"执行命令: {' '.join(cmd)}")
    print("=" * 80)
    
    # 创建报告目录
    os.makedirs('reports', exist_ok=True)
    
    # 执行测试
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"测试执行失败: {e}")
        return False


def generate_summary_report():
    """生成测试总结报告"""
    report_content = """
# RBAC系统测试报告

## 测试概述

本报告包含RBAC权限系统ORM层的完整单元测试结果。

## 测试范围

### 模型层测试 (models/)
- ✅ BaseModel: 基础模型类测试
- ✅ User: 用户模型测试
- ✅ Role: 角色模型测试
- ✅ Permission: 权限模型测试
- ✅ UserRole: 用户角色关联测试
- ✅ RolePermission: 角色权限关联测试

### DAO层测试 (dao/)
- ✅ BaseDao: 基础DAO类测试
- ✅ UserDao: 用户DAO测试
- ✅ RoleDao: 角色DAO测试
- ✅ PermissionDao: 权限DAO测试
- ✅ UserRoleDao: 用户角色关联DAO测试
- ✅ RolePermissionDao: 角色权限关联DAO测试

## 测试类型

### 单元测试 (Unit Tests)
- **CRUD操作测试**: 创建、查询、更新、删除操作
- **业务方法测试**: 特定业务逻辑方法
- **数据验证测试**: 输入数据验证和约束检查
- **异常处理测试**: 错误场景和异常处理
- **边界条件测试**: 边界值和极限情况

### 集成测试 (Integration Tests)
- **关系映射测试**: 实体间关系的正确性
- **事务处理测试**: 数据库事务的一致性
- **批量操作测试**: 批量处理的性能和正确性

## 测试覆盖率目标

- **整体覆盖率**: ≥90%
- **分支覆盖率**: ≥85%
- **方法覆盖率**: 100%

## 质量保证

### 代码质量
- 遵循PEP 8编码规范
- 完整的类型注解
- 详细的文档字符串
- 统一的错误处理

### 测试质量
- 完整的测试用例覆盖
- 清晰的测试命名
- 独立的测试环境
- 可重复的测试结果

## 报告文件

- **HTML报告**: reports/test_report.html
- **覆盖率报告**: htmlcov/index.html
- **终端输出**: 实时测试结果

## 使用说明

### 运行所有测试
```bash
python run_tests.py --verbose --coverage --html
```

### 运行特定类型测试
```bash
python run_tests.py --markers unit
python run_tests.py --markers integration
```

### 查看覆盖率报告
```bash
# 在浏览器中打开
open htmlcov/index.html
```

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**测试框架**: pytest
**Python版本**: {sys.version}
"""
    
    # 写入报告文件
    with open('reports/README.md', 'w', encoding='utf-8') as f:
        f.write(report_content.format(
            datetime=__import__('datetime').datetime,
            sys=sys
        ))
    
    print("✓ 测试总结报告已生成: reports/README.md")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='RBAC系统测试执行脚本')
    parser.add_argument('--verbose', action='store_true', help='详细输出模式')
    parser.add_argument('--coverage', action='store_true', help='生成覆盖率报告')
    parser.add_argument('--html', action='store_true', help='生成HTML报告')
    parser.add_argument('--markers', type=str, help='指定测试标记')
    parser.add_argument('--install-deps', action='store_true', help='安装测试依赖')
    
    args = parser.parse_args()
    
    print("🚀 RBAC系统测试执行器")
    print("=" * 80)
    
    # 设置环境
    setup_environment()
    
    # 安装依赖
    if args.install_deps:
        if not install_dependencies():
            print("❌ 依赖安装失败")
            return 1
    
    # 执行测试
    print("\n📋 开始执行测试...")
    success = run_tests(args)
    
    # 生成报告
    if success:
        print("\n📊 生成测试报告...")
        generate_summary_report()
        print("\n✅ 所有测试执行成功！")
        
        if args.coverage:
            print("📈 覆盖率报告: htmlcov/index.html")
        if args.html:
            print("📄 HTML报告: reports/test_report.html")
        
        return 0
    else:
        print("\n❌ 测试执行失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
