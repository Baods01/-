"""
RBAC系统用户DAO模块

本模块定义了用户数据访问对象，提供用户相关的数据库操作接口。

Classes:
    UserDao: 用户DAO类

Author: AI Assistant
Created: 2025-07-19
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from models.user import User
from models.user_role import UserRole
from models.role import Role
from models.role_permission import RolePermission
from models.permission import Permission
from .base_dao import BaseDao, DatabaseError, NotFoundError


class UserDao(BaseDao[User]):
    """
    用户数据访问对象
    
    提供用户相关的数据库操作接口，包括基础CRUD操作和用户特有的查询方法。
    
    Methods:
        基础CRUD操作（继承自BaseDao）:
            create, find_by_id, find_all, update, delete_by_id
            batch_create, batch_update, batch_delete
        
        用户特有查询方法:
            find_by_username: 根据用户名查询
            find_by_email: 根据邮箱查询
            find_active_users: 查询所有启用用户
            find_by_status: 根据状态查询
            search_users: 用户搜索
        
        用户角色相关方法:
            get_user_roles: 获取用户的所有角色
            get_user_permissions: 获取用户的所有权限
            has_role: 检查用户是否具有特定角色
            has_permission: 检查用户是否具有特定权限
        
        用户管理方法:
            activate_user: 启用用户
            deactivate_user: 禁用用户
            update_password: 更新密码
    """
    
    def _get_model_class(self) -> type:
        """获取模型类"""
        return User
    
    def find_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名查询用户
        
        Args:
            username (str): 用户名
            
        Returns:
            Optional[User]: 找到的用户对象，如果不存在则返回None
            
        Raises:
            ValueError: 用户名参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not username or not isinstance(username, str):
                raise ValueError("用户名不能为空")
            
            user = self.session.query(User).filter(
                User.username == username.strip()
            ).first()
            
            return user
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据用户名查询用户失败: username={username}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱查询用户
        
        Args:
            email (str): 邮箱地址
            
        Returns:
            Optional[User]: 找到的用户对象，如果不存在则返回None
            
        Raises:
            ValueError: 邮箱参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not email or not isinstance(email, str):
                raise ValueError("邮箱地址不能为空")
            
            user = self.session.query(User).filter(
                User.email == email.strip().lower()
            ).first()
            
            return user
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据邮箱查询用户失败: email={email}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_active_users(self) -> List[User]:
        """
        查询所有启用用户
        
        Returns:
            List[User]: 启用的用户列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            users = self.session.query(User).filter(
                User.status == 1
            ).order_by(User.created_at.desc()).all()
            
            return users
            
        except SQLAlchemyError as e:
            self.logger.error(f"查询启用用户失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_status(self, status: int) -> List[User]:
        """
        根据状态查询用户
        
        Args:
            status (int): 用户状态，1=启用，0=禁用
            
        Returns:
            List[User]: 指定状态的用户列表
            
        Raises:
            ValueError: 状态参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if status not in [0, 1]:
                raise ValueError("用户状态只能是0（禁用）或1（启用）")
            
            users = self.session.query(User).filter(
                User.status == status
            ).order_by(User.created_at.desc()).all()
            
            return users
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据状态查询用户失败: status={status}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def search_users(self, keyword: str, limit: Optional[int] = None) -> List[User]:
        """
        用户搜索（用户名或邮箱）
        
        Args:
            keyword (str): 搜索关键词
            limit (int, optional): 限制返回记录数
            
        Returns:
            List[User]: 匹配的用户列表
            
        Raises:
            ValueError: 关键词参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not keyword or not isinstance(keyword, str):
                raise ValueError("搜索关键词不能为空")
            
            keyword = f"%{keyword.strip()}%"
            query = self.session.query(User).filter(
                or_(
                    User.username.like(keyword),
                    User.email.like(keyword)
                )
            ).order_by(User.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"搜索用户失败: keyword={keyword}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_user_roles(self, user_id: int) -> List[Role]:
        """
        获取用户的所有角色
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[Role]: 用户拥有的角色列表
            
        Raises:
            ValueError: 用户ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            
            roles = self.session.query(Role).join(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.status == 1,
                    Role.status == 1
                )
            ).order_by(Role.role_name).all()
            
            return roles
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取用户角色失败: user_id={user_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """
        获取用户的所有权限
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[Permission]: 用户拥有的权限列表
            
        Raises:
            ValueError: 用户ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            
            permissions = self.session.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.status == 1,
                    Role.status == 1,
                    RolePermission.status == 1
                )
            ).distinct().order_by(Permission.resource_type, Permission.action_type).all()
            
            return permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取用户权限失败: user_id={user_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def has_role(self, user_id: int, role_code: str) -> bool:
        """
        检查用户是否具有特定角色
        
        Args:
            user_id (int): 用户ID
            role_code (str): 角色代码
            
        Returns:
            bool: 如果用户具有该角色返回True，否则返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_code:
                raise ValueError("角色代码不能为空")
            
            count = self.session.query(UserRole).join(Role).filter(
                and_(
                    UserRole.user_id == user_id,
                    Role.role_code == role_code,
                    UserRole.status == 1,
                    Role.status == 1
                )
            ).count()
            
            return count > 0
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"检查用户角色失败: user_id={user_id}, role_code={role_code}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def has_permission(self, user_id: int, permission_code: str) -> bool:
        """
        检查用户是否具有特定权限
        
        Args:
            user_id (int): 用户ID
            permission_code (str): 权限代码
            
        Returns:
            bool: 如果用户具有该权限返回True，否则返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not permission_code:
                raise ValueError("权限代码不能为空")
            
            count = self.session.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    Permission.permission_code == permission_code,
                    UserRole.status == 1,
                    Role.status == 1,
                    RolePermission.status == 1
                )
            ).count()
            
            return count > 0
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"检查用户权限失败: user_id={user_id}, permission_code={permission_code}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def activate_user(self, user_id: int) -> bool:
        """
        启用用户
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 操作成功返回True，用户不存在返回False
            
        Raises:
            ValueError: 用户ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            
            user = self.find_by_id(user_id)
            if not user:
                return False
            
            user.activate()
            self.session.flush()
            
            self.logger.info(f"启用用户成功: user_id={user_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"启用用户失败: user_id={user_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        禁用用户
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 操作成功返回True，用户不存在返回False
            
        Raises:
            ValueError: 用户ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            
            user = self.find_by_id(user_id)
            if not user:
                return False
            
            user.deactivate()
            self.session.flush()
            
            self.logger.info(f"禁用用户成功: user_id={user_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"禁用用户失败: user_id={user_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def update_password(self, user_id: int, password_hash: str) -> bool:
        """
        更新用户密码
        
        Args:
            user_id (int): 用户ID
            password_hash (str): 新的密码哈希值
            
        Returns:
            bool: 操作成功返回True，用户不存在返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not password_hash:
                raise ValueError("密码哈希值不能为空")
            
            user = self.find_by_id(user_id)
            if not user:
                return False
            
            user.set_password_hash(password_hash)
            self.session.flush()
            
            self.logger.info(f"更新用户密码成功: user_id={user_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"更新用户密码失败: user_id={user_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
