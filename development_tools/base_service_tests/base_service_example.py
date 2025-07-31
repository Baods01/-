#!/usr/bin/env python3
"""
RBAC权限系统 - 基础服务类使用示例

本文件展示了如何使用BaseService基础服务类，
包括继承实现、事务管理、异常处理等功能。

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import sys
import os
from typing import Type, Optional, List
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.base_service import BaseService
from services.exceptions import DataValidationError, ResourceNotFoundError
from models.user import User


class UserService(BaseService[User]):
    """
    用户服务示例类
    
    展示如何继承BaseService并实现具体的业务逻辑
    """
    
    def get_model_class(self) -> Type[User]:
        """返回User模型类"""
        return User
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: Optional[str] = None) -> User:
        """
        创建用户
        
        Args:
            username (str): 用户名
            email (str): 邮箱
            password (str): 密码
            full_name (str, optional): 全名
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            ValidationError: 数据验证失败
            DuplicateResourceError: 用户名或邮箱重复
        """
        with self.transaction():
            # 检查用户名是否重复
            existing_user = self.session.query(User).filter(
                User.username == username
            ).first()
            
            if existing_user:
                raise DataValidationError(f"用户名 '{username}' 已存在")
            
            # 检查邮箱是否重复
            existing_email = self.session.query(User).filter(
                User.email == email
            ).first()
            
            if existing_email:
                raise DataValidationError(f"邮箱 '{email}' 已存在")
            
            # 创建用户对象
            user = User(
                username=username,
                email=email,
                password_hash=password,  # 实际应用中需要加密
                full_name=full_name,
                status=1  # 启用状态
            )
            
            # 保存用户
            saved_user = self.save_entity(user)
            
            # 记录操作日志
            self.log_operation("create_user", {
                "user_id": saved_user.id,
                "username": username,
                "email": email
            })
            
            return saved_user
    
    def update_user_info(self, user_id: int, **kwargs) -> User:
        """
        更新用户信息
        
        Args:
            user_id (int): 用户ID
            **kwargs: 要更新的字段
            
        Returns:
            User: 更新后的用户对象
            
        Raises:
            ResourceNotFoundError: 用户不存在
            ValidationError: 数据验证失败
        """
        with self.transaction():
            # 获取用户
            user = self.get_by_id(user_id)
            
            # 更新用户信息
            updated_user = self.update_entity(user, **kwargs)
            
            # 记录操作日志
            self.log_operation("update_user", {
                "user_id": user_id,
                "updated_fields": list(kwargs.keys())
            })
            
            return updated_user
    
    def get_active_users(self, limit: Optional[int] = None, 
                        offset: Optional[int] = None) -> List[User]:
        """
        获取活跃用户列表
        
        Args:
            limit (int, optional): 限制数量
            offset (int, optional): 偏移量
            
        Returns:
            List[User]: 活跃用户列表
        """
        return self.find_all(limit=limit, offset=offset, status=1)
    
    def deactivate_user(self, user_id: int) -> User:
        """
        停用用户
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            User: 更新后的用户对象
        """
        with self.transaction():
            user = self.get_by_id(user_id)
            updated_user = self.update_entity(user, status=0)
            
            self.log_operation("deactivate_user", {"user_id": user_id})
            
            return updated_user


def example_usage():
    """基础服务类使用示例"""
    print("=== BaseService 使用示例 ===")
    
    # 创建用户服务实例
    user_service = UserService()
    
    try:
        # 示例1: 创建用户
        print("\n1. 创建用户示例:")
        with user_service.transaction():
            user = user_service.create_user(
                username="test_user",
                email="test@example.com",
                password="password123",
                full_name="测试用户"
            )
            print(f"创建用户成功: {user.username} (ID: {user.id})")
        
        # 示例2: 查询用户
        print("\n2. 查询用户示例:")
        found_user = user_service.find_by_id(user.id)
        if found_user:
            print(f"找到用户: {found_user.username}")
        
        # 示例3: 更新用户
        print("\n3. 更新用户示例:")
        updated_user = user_service.update_user_info(
            user.id,
            full_name="更新后的测试用户"
        )
        print(f"更新用户成功: {updated_user.full_name}")
        
        # 示例4: 获取活跃用户
        print("\n4. 获取活跃用户示例:")
        active_users = user_service.get_active_users(limit=10)
        print(f"活跃用户数量: {len(active_users)}")
        
        # 示例5: 停用用户
        print("\n5. 停用用户示例:")
        deactivated_user = user_service.deactivate_user(user.id)
        print(f"用户状态: {deactivated_user.status}")
        
        # 示例6: 性能统计
        print("\n6. 性能统计示例:")
        stats = user_service.get_performance_stats()
        print(f"操作次数: {stats['operations_count']}")
        print(f"平均操作时间: {stats['average_operation_time']:.4f}秒")
        print(f"错误率: {stats['error_rate']:.2%}")
        
    except Exception as e:
        print(f"操作失败: {str(e)}")
        print(f"异常类型: {type(e).__name__}")
    
    finally:
        # 清理资源
        user_service.close()
        print("\n=== 示例完成 ===")


def example_context_manager():
    """上下文管理器使用示例"""
    print("\n=== 上下文管理器示例 ===")
    
    try:
        # 使用上下文管理器
        with UserService() as user_service:
            # 在上下文中执行操作
            user = user_service.create_user(
                username="context_user",
                email="context@example.com",
                password="password123"
            )
            print(f"在上下文中创建用户: {user.username}")
            
            # 获取性能统计
            stats = user_service.get_performance_stats()
            print(f"上下文中的操作次数: {stats['operations_count']}")
        
        # 上下文结束后，资源自动清理
        print("上下文管理器自动清理完成")
        
    except Exception as e:
        print(f"上下文管理器示例失败: {str(e)}")


def example_error_handling():
    """异常处理示例"""
    print("\n=== 异常处理示例 ===")
    
    user_service = UserService()
    
    try:
        # 示例1: 查找不存在的用户
        print("1. 查找不存在的用户:")
        try:
            user = user_service.get_by_id(99999)
        except ResourceNotFoundError as e:
            print(f"捕获到资源不存在异常: {e.message}")
            print(f"错误代码: {e.error_code}")
        
        # 示例2: 创建重复用户
        print("\n2. 创建重复用户:")
        try:
            # 先创建一个用户
            user1 = user_service.create_user("duplicate_user", "dup@example.com", "pass123")
            # 再创建同名用户
            user2 = user_service.create_user("duplicate_user", "dup2@example.com", "pass123")
        except DataValidationError as e:
            print(f"捕获到验证异常: {e.message}")
        
        # 示例3: 事务回滚
        print("\n3. 事务回滚示例:")
        try:
            with user_service.transaction():
                user = user_service.create_user("rollback_user", "rollback@example.com", "pass123")
                print(f"创建用户: {user.username}")
                
                # 故意抛出异常触发回滚
                raise Exception("故意触发回滚")
                
        except Exception as e:
            print(f"事务已回滚: {str(e)}")
            
            # 验证用户是否真的被回滚了
            rollback_user = user_service.session.query(User).filter(
                User.username == "rollback_user"
            ).first()
            
            if rollback_user is None:
                print("确认: 用户创建已被回滚")
            else:
                print("警告: 用户创建未被回滚")
    
    finally:
        user_service.close()


if __name__ == "__main__":
    # 运行所有示例
    example_usage()
    example_context_manager()
    example_error_handling()
