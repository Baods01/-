#!/usr/bin/env python3
"""
RBAC权限系统 - 环境验证脚本

验证第一轮任务完成情况：
1. 依赖包安装验证
2. 目录结构验证
3. 配置文件验证
4. 现有基础组件验证

作者: RBAC System Development Team
创建时间: 2025-07-21
版本: 1.0.0
"""

import sys
import os
from pathlib import Path


def test_dependencies():
    """测试依赖包安装"""
    print("🔍 验证依赖包安装...")
    
    dependencies = [
        ('fastapi', 'FastAPI Web框架'),
        ('uvicorn', 'ASGI服务器'),
        ('jose', 'JWT处理库'),
        ('pydantic', '数据验证库'),
        ('pydantic_settings', 'Pydantic配置管理'),
        ('bcrypt', '密码加密库'),
        ('pymysql', 'MySQL连接器')
    ]
    
    failed = []
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {description}: {module}")
        except ImportError as e:
            print(f"  ❌ {description}: {module} - {e}")
            failed.append(module)
    
    return len(failed) == 0


def test_directory_structure():
    """测试目录结构"""
    print("\n🔍 验证目录结构...")
    
    required_dirs = [
        'services',
        'services/exceptions',
        'api',
        'api/controllers',
        'api/middleware', 
        'api/schemas'
    ]
    
    required_files = [
        'services/__init__.py',
        'services/exceptions/__init__.py',
        'api/__init__.py',
        'api/controllers/__init__.py',
        'api/middleware/__init__.py',
        'api/schemas/__init__.py'
    ]
    
    failed = []
    
    # 检查目录
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ 目录: {dir_path}")
        else:
            print(f"  ❌ 目录: {dir_path}")
            failed.append(dir_path)
    
    # 检查文件
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ 文件: {file_path}")
        else:
            print(f"  ❌ 文件: {file_path}")
            failed.append(file_path)
    
    return len(failed) == 0


def test_config_files():
    """测试配置文件"""
    print("\n🔍 验证配置文件...")
    
    try:
        from config.api_config import config
        print(f"  ✅ API配置: {config.app_name}")
    except Exception as e:
        print(f"  ❌ API配置加载失败: {e}")
        return False
    
    try:
        from config.jwt_config import jwt_config
        print(f"  ✅ JWT配置: 算法={jwt_config.algorithm}")
    except Exception as e:
        print(f"  ❌ JWT配置加载失败: {e}")
        return False
    
    return True


def test_existing_components():
    """测试现有基础组件"""
    print("\n🔍 验证现有基础组件...")
    
    # 测试DAO层
    try:
        from dao.user_dao import UserDao
        print("  ✅ DAO层: UserDao导入成功")
    except Exception as e:
        print(f"  ❌ DAO层: UserDao导入失败 - {e}")
        return False
    
    # 测试模型层
    try:
        from models.user import User
        print("  ✅ 模型层: User模型导入成功")
    except Exception as e:
        print(f"  ❌ 模型层: User模型导入失败 - {e}")
        return False
    
    # 测试工具层
    try:
        from utils.password_utils import PasswordUtils
        print("  ✅ 工具层: PasswordUtils导入成功")
    except Exception as e:
        print(f"  ❌ 工具层: PasswordUtils导入失败 - {e}")
        return False
    
    # 测试数据库连接
    try:
        from utils.db_utils import DatabaseManager
        print("  ✅ 数据库: DatabaseManager导入成功")
    except Exception as e:
        print(f"  ❌ 数据库: DatabaseManager导入失败 - {e}")
        return False
    
    return True


def test_business_exceptions():
    """测试业务异常类"""
    print("\n🔍 验证业务异常类...")
    
    try:
        from services.exceptions import (
            BusinessLogicError,
            AuthenticationError,
            AuthorizationError,
            ValidationError,
            ResourceNotFoundError,
            DuplicateResourceError
        )
        
        # 测试异常类实例化
        auth_error = AuthenticationError("测试认证异常")
        print(f"  ✅ 认证异常: {auth_error.error_code}")
        
        auth_error = AuthorizationError("测试授权异常")
        print(f"  ✅ 授权异常: {auth_error.error_code}")
        
        validation_error = ValidationError("测试验证异常")
        print(f"  ✅ 验证异常: {validation_error.error_code}")
        
        not_found_error = ResourceNotFoundError("User", "123")
        print(f"  ✅ 资源不存在异常: {not_found_error.error_code}")
        
        duplicate_error = DuplicateResourceError("User", "username", "admin")
        print(f"  ✅ 资源重复异常: {duplicate_error.error_code}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 业务异常类测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 RBAC权限系统 - 环境验证开始")
    print("=" * 50)
    
    tests = [
        ("依赖包安装", test_dependencies),
        ("目录结构", test_directory_structure),
        ("配置文件", test_config_files),
        ("现有基础组件", test_existing_components),
        ("业务异常类", test_business_exceptions)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 验证结果汇总:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有验证通过！环境准备完成，可以开始下一轮开发。")
        return 0
    else:
        print("⚠️  部分验证失败，请检查并修复问题后重新验证。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
