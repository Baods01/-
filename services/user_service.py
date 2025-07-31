"""
RBAC权限系统 - 用户业务服务类

本模块定义了用户相关的业务逻辑服务，封装用户注册、认证、权限管理等核心功能。

Classes:
    UserService: 用户业务服务类

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import re
import asyncio
from typing import Optional, List, Dict, Any, Type
from datetime import datetime, timezone

from sqlalchemy.orm import Session

# 导入基础服务类
from services.base_service import BaseService

# 导入业务异常类
from services.exceptions import (
    BusinessLogicError,
    AuthenticationError,
    AuthorizationError,
    DataValidationError,
    ResourceNotFoundError,
    DuplicateResourceError
)

# 导入现有组件
from models.user import User
from dao.user_dao import UserDao
from utils.password_utils import PasswordUtils


class UserService(BaseService[User]):
    """
    用户业务服务类
    
    封装用户相关的所有业务逻辑，包括用户注册、认证、权限管理、状态管理等。
    基于BaseService提供统一的事务管理、异常处理和日志记录。
    
    Features:
        - 用户注册和认证
        - 密码管理和强度验证
        - 用户状态管理（启用/禁用）
        - 权限检查和授权验证
        - 完整的数据验证和审计日志
    
    Attributes:
        user_dao (UserDao): 用户数据访问对象
        password_utils (PasswordUtils): 密码处理工具
    
    Example:
        >>> with UserService() as service:
        ...     user = await service.create_user("admin", "admin@example.com", "Password123!")
        ...     authenticated = await service.authenticate_user("admin", "Password123!")
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化用户服务
        
        Args:
            session (Session, optional): 数据库会话，如果不提供则创建新会话
        """
        super().__init__(session)
        
        # 初始化组件
        self.user_dao = UserDao(self.session)
        self.password_utils = PasswordUtils()
        
        self.logger.info("UserService 初始化完成")
    
    def get_model_class(self) -> Type[User]:
        """获取服务对应的模型类"""
        return User
    
    async def create_user(self, username: str, email: str, password: str, **kwargs) -> User:
        """
        创建用户
        
        实现用户注册逻辑，包括数据验证、唯一性检查、密码加密等。
        
        Args:
            username (str): 用户名
            email (str): 邮箱地址
            password (str): 明文密码
            **kwargs: 其他用户属性（如full_name等）
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            DataValidationError: 数据验证失败
            DuplicateResourceError: 用户名或邮箱重复
            BusinessLogicError: 其他业务逻辑错误
        """
        with self.transaction():
            try:
                # 1. 数据验证
                self._validate_user_data(username, email, password)
                
                # 2. 唯一性检查
                await self._check_user_uniqueness(username, email)
                
                # 3. 密码强度验证和加密
                self._validate_password_strength(password)
                password_hash = self.password_utils.hash_password(password)
                
                # 4. 创建用户对象
                user_data = {
                    'username': username.strip(),
                    'email': email.strip().lower(),
                    'password_hash': password_hash,
                    'status': 1,  # 默认启用
                    **kwargs
                }
                
                user = User(**user_data)
                
                # 5. 数据验证
                user.validate()
                
                # 6. 保存用户
                created_user = self.save_entity(user)
                
                # 7. 记录操作日志
                self.log_operation("create_user", {
                    "user_id": created_user.id,
                    "username": username,
                    "email": email,
                    "status": "success"
                })
                
                self.logger.info(f"用户创建成功: username={username}, email={email}, user_id={created_user.id}")
                return created_user
                
            except Exception as e:
                self.log_operation("create_user", {
                    "username": username,
                    "email": email,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        支持用户名或邮箱登录，验证密码并检查用户状态。
        
        Args:
            username (str): 用户名或邮箱地址
            password (str): 明文密码
            
        Returns:
            Optional[User]: 认证成功返回用户对象，失败返回None
            
        Raises:
            AuthenticationError: 认证失败
            DataValidationError: 输入数据无效
        """
        try:
            # 1. 输入验证
            if not username or not password:
                raise DataValidationError("用户名和密码不能为空")
            
            username = username.strip()
            
            # 2. 查找用户（支持用户名或邮箱登录）
            user = None
            if '@' in username:
                # 邮箱登录
                user = self.user_dao.find_by_email(username)
            else:
                # 用户名登录
                user = self.user_dao.find_by_username(username)
            
            if not user:
                # 记录认证失败日志
                self.log_operation("authenticate_user", {
                    "username": username,
                    "status": "failed",
                    "reason": "user_not_found"
                })
                raise AuthenticationError("用户名或密码错误")
            
            # 3. 检查用户状态
            if not user.is_active():
                self.log_operation("authenticate_user", {
                    "user_id": user.id,
                    "username": username,
                    "status": "failed",
                    "reason": "user_inactive"
                })
                raise AuthenticationError("用户账户已被禁用")
            
            # 4. 验证密码
            if not self.password_utils.verify_password(password, user.password_hash):
                self.log_operation("authenticate_user", {
                    "user_id": user.id,
                    "username": username,
                    "status": "failed",
                    "reason": "invalid_password"
                })
                raise AuthenticationError("用户名或密码错误")
            
            # 5. 认证成功
            self.log_operation("authenticate_user", {
                "user_id": user.id,
                "username": username,
                "status": "success"
            })
            
            self.logger.info(f"用户认证成功: user_id={user.id}, username={username}")
            return user
            
        except (AuthenticationError, DataValidationError):
            raise
        except Exception as e:
            self.log_operation("authenticate_user", {
                "username": username,
                "status": "error",
                "error": str(e)
            })
            raise self._convert_exception(e)
    
    async def update_user(self, user_id: int, **update_data) -> User:
        """
        更新用户信息
        
        Args:
            user_id (int): 用户ID
            **update_data: 要更新的字段
            
        Returns:
            User: 更新后的用户对象
            
        Raises:
            ResourceNotFoundError: 用户不存在
            DataValidationError: 数据验证失败
            DuplicateResourceError: 用户名或邮箱重复
        """
        with self.transaction():
            try:
                # 1. 获取用户
                user = self.get_by_id(user_id)
                
                # 2. 验证更新数据
                if 'username' in update_data:
                    new_username = update_data['username'].strip()
                    if new_username != user.username:
                        self._validate_username(new_username)
                        await self._check_username_uniqueness(new_username, exclude_user_id=user_id)
                
                if 'email' in update_data:
                    new_email = update_data['email'].strip().lower()
                    if new_email != user.email:
                        self._validate_email(new_email)
                        await self._check_email_uniqueness(new_email, exclude_user_id=user_id)
                
                # 3. 过滤不允许直接更新的字段
                forbidden_fields = {'id', 'password_hash', 'created_at'}
                filtered_data = {k: v for k, v in update_data.items() if k not in forbidden_fields}
                
                # 4. 更新用户
                updated_user = self.update_entity(user, **filtered_data)
                
                # 5. 记录操作日志
                self.log_operation("update_user", {
                    "user_id": user_id,
                    "updated_fields": list(filtered_data.keys()),
                    "status": "success"
                })
                
                self.logger.info(f"用户信息更新成功: user_id={user_id}, fields={list(filtered_data.keys())}")
                return updated_user
                
            except Exception as e:
                self.log_operation("update_user", {
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        修改密码

        Args:
            user_id (int): 用户ID
            old_password (str): 旧密码
            new_password (str): 新密码

        Returns:
            bool: 修改成功返回True

        Raises:
            ResourceNotFoundError: 用户不存在
            AuthenticationError: 旧密码验证失败
            DataValidationError: 新密码强度不足
        """
        with self.transaction():
            try:
                # 1. 获取用户
                user = self.get_by_id(user_id)

                # 2. 验证旧密码
                if not self.password_utils.verify_password(old_password, user.password_hash):
                    self.log_operation("change_password", {
                        "user_id": user_id,
                        "status": "failed",
                        "reason": "invalid_old_password"
                    })
                    raise AuthenticationError("旧密码验证失败")

                # 3. 验证新密码强度
                self._validate_password_strength(new_password)

                # 4. 检查新密码是否与旧密码相同
                if self.password_utils.verify_password(new_password, user.password_hash):
                    raise DataValidationError("新密码不能与旧密码相同")

                # 5. 加密新密码
                new_password_hash = self.password_utils.hash_password(new_password)

                # 6. 更新密码
                user.set_password_hash(new_password_hash)
                self.session.flush()

                # 7. 记录操作日志
                self.log_operation("change_password", {
                    "user_id": user_id,
                    "status": "success"
                })

                self.logger.info(f"用户密码修改成功: user_id={user_id}")
                return True

            except Exception as e:
                self.log_operation("change_password", {
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def get_user_permissions(self, user_id: int) -> List[str]:
        """
        获取用户权限

        通过用户的角色获取所有权限列表。

        Args:
            user_id (int): 用户ID

        Returns:
            List[str]: 权限代码列表

        Raises:
            ResourceNotFoundError: 用户不存在
        """
        try:
            # 1. 检查用户是否存在
            user = self.get_by_id(user_id)

            # 2. 获取用户权限
            permissions = self.user_dao.get_user_permissions(user_id)
            permission_codes = [perm.permission_code for perm in permissions]

            # 3. 记录操作日志
            self.log_operation("get_user_permissions", {
                "user_id": user_id,
                "permission_count": len(permission_codes),
                "status": "success"
            })

            return permission_codes

        except Exception as e:
            self.log_operation("get_user_permissions", {
                "user_id": user_id,
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)

    async def enable_user(self, user_id: int) -> bool:
        """
        启用用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 启用成功返回True

        Raises:
            ResourceNotFoundError: 用户不存在
        """
        with self.transaction():
            try:
                # 1. 检查用户是否存在
                user = self.get_by_id(user_id)

                # 2. 检查当前状态
                if user.is_active():
                    self.logger.info(f"用户已经是启用状态: user_id={user_id}")
                    return True

                # 3. 启用用户
                success = self.user_dao.activate_user(user_id)

                if success:
                    # 4. 记录操作日志
                    self.log_operation("enable_user", {
                        "user_id": user_id,
                        "status": "success"
                    })

                    self.logger.info(f"用户启用成功: user_id={user_id}")

                return success

            except Exception as e:
                self.log_operation("enable_user", {
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def disable_user(self, user_id: int) -> bool:
        """
        禁用用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 禁用成功返回True

        Raises:
            ResourceNotFoundError: 用户不存在
        """
        with self.transaction():
            try:
                # 1. 检查用户是否存在
                user = self.get_by_id(user_id)

                # 2. 检查当前状态
                if not user.is_active():
                    self.logger.info(f"用户已经是禁用状态: user_id={user_id}")
                    return True

                # 3. 禁用用户
                success = self.user_dao.deactivate_user(user_id)

                if success:
                    # 4. 记录操作日志
                    self.log_operation("disable_user", {
                        "user_id": user_id,
                        "status": "success"
                    })

                    self.logger.info(f"用户禁用成功: user_id={user_id}")

                return success

            except Exception as e:
                self.log_operation("disable_user", {
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    # ==================== 辅助方法 ====================

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            username (str): 用户名

        Returns:
            Optional[User]: 用户对象，不存在返回None
        """
        try:
            if not username:
                raise DataValidationError("用户名不能为空")

            return self.user_dao.find_by_username(username.strip())

        except Exception as e:
            raise self._convert_exception(e)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            email (str): 邮箱地址

        Returns:
            Optional[User]: 用户对象，不存在返回None
        """
        try:
            if not email:
                raise DataValidationError("邮箱地址不能为空")

            return self.user_dao.find_by_email(email.strip().lower())

        except Exception as e:
            raise self._convert_exception(e)

    async def check_user_permission(self, user_id: int, permission_code: str) -> bool:
        """
        检查用户是否具有特定权限

        Args:
            user_id (int): 用户ID
            permission_code (str): 权限代码

        Returns:
            bool: 有权限返回True，否则返回False

        Raises:
            ResourceNotFoundError: 用户不存在
            DataValidationError: 权限代码无效
        """
        try:
            if not permission_code:
                raise DataValidationError("权限代码不能为空")

            # 检查用户是否存在
            self.get_by_id(user_id)

            # 检查权限
            has_permission = self.user_dao.has_permission(user_id, permission_code)

            self.log_operation("check_user_permission", {
                "user_id": user_id,
                "permission_code": permission_code,
                "has_permission": has_permission,
                "status": "success"
            })

            return has_permission

        except Exception as e:
            self.log_operation("check_user_permission", {
                "user_id": user_id,
                "permission_code": permission_code,
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)

    async def get_active_users(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[User]:
        """
        获取活跃用户列表

        Args:
            limit (int, optional): 限制数量
            offset (int, optional): 偏移量

        Returns:
            List[User]: 活跃用户列表
        """
        try:
            if limit is not None and limit <= 0:
                raise DataValidationError("限制数量必须大于0")
            if offset is not None and offset < 0:
                raise DataValidationError("偏移量不能为负数")

            # 使用BaseService的find_all方法
            users = self.find_all(limit=limit, offset=offset, status=1)

            return users

        except Exception as e:
            raise self._convert_exception(e)

    # ==================== 数据验证方法 ====================

    def _validate_user_data(self, username: str, email: str, password: str):
        """验证用户基础数据"""
        if not username or not email or not password:
            raise DataValidationError("用户名、邮箱和密码不能为空")

        self._validate_username(username)
        self._validate_email(email)

    def _validate_username(self, username: str):
        """验证用户名格式"""
        if not username:
            raise DataValidationError("用户名不能为空")

        username = username.strip()

        # 长度检查
        if len(username) < 3 or len(username) > 50:
            raise DataValidationError("用户名长度必须在3-50字符之间")

        # 格式检查：字母数字下划线，字母开头
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
            raise DataValidationError("用户名必须以字母开头，只能包含字母、数字和下划线")

    def _validate_email(self, email: str):
        """验证邮箱格式"""
        if not email:
            raise DataValidationError("邮箱地址不能为空")

        email = email.strip()

        # 长度检查
        if len(email) > 64:
            raise DataValidationError("邮箱地址长度不能超过64字符")

        # 格式检查
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise DataValidationError("邮箱地址格式不正确")

    def _validate_password_strength(self, password: str):
        """验证密码强度"""
        if not password:
            raise DataValidationError("密码不能为空")

        # 使用PasswordUtils的强度检查
        is_strong, message = self.password_utils.check_password_strength(password)
        if not is_strong:
            raise DataValidationError(f"密码强度不足: {message}")

    # ==================== 唯一性检查方法 ====================

    async def _check_user_uniqueness(self, username: str, email: str, exclude_user_id: Optional[int] = None):
        """检查用户名和邮箱唯一性"""
        await self._check_username_uniqueness(username, exclude_user_id)
        await self._check_email_uniqueness(email, exclude_user_id)

    async def _check_username_uniqueness(self, username: str, exclude_user_id: Optional[int] = None):
        """检查用户名唯一性"""
        existing_user = self.user_dao.find_by_username(username.strip())
        if existing_user and (exclude_user_id is None or existing_user.id != exclude_user_id):
            raise DuplicateResourceError(
                resource_type="User",
                field_name="username",
                field_value=username,
                message=f"用户名 '{username}' 已存在"
            )

    async def _check_email_uniqueness(self, email: str, exclude_user_id: Optional[int] = None):
        """检查邮箱唯一性"""
        existing_user = self.user_dao.find_by_email(email.strip().lower())
        if existing_user and (exclude_user_id is None or existing_user.id != exclude_user_id):
            raise DuplicateResourceError(
                resource_type="User",
                field_name="email",
                field_value=email,
                message=f"邮箱地址 '{email}' 已存在"
            )

    # ==================== 批量操作方法 ====================

    async def batch_create_users(self, users_data: List[Dict[str, Any]]) -> List[User]:
        """
        批量创建用户

        Args:
            users_data (List[Dict]): 用户数据列表

        Returns:
            List[User]: 创建的用户列表

        Raises:
            DataValidationError: 数据验证失败
            DuplicateResourceError: 用户名或邮箱重复
        """
        with self.transaction():
            try:
                created_users = []

                for i, user_data in enumerate(users_data):
                    try:
                        username = user_data.get('username')
                        email = user_data.get('email')
                        password = user_data.get('password')

                        if not all([username, email, password]):
                            raise DataValidationError(f"第{i+1}个用户数据不完整")

                        # 创建用户（会自动进行验证和唯一性检查）
                        user = await self.create_user(username, email, password, **{
                            k: v for k, v in user_data.items()
                            if k not in ['username', 'email', 'password']
                        })
                        created_users.append(user)

                    except Exception as e:
                        raise DataValidationError(f"第{i+1}个用户创建失败: {str(e)}")

                # 记录批量操作日志
                self.log_operation("batch_create_users", {
                    "total_count": len(users_data),
                    "success_count": len(created_users),
                    "status": "success"
                })

                self.logger.info(f"批量创建用户成功: 总数={len(users_data)}, 成功={len(created_users)}")
                return created_users

            except Exception as e:
                self.log_operation("batch_create_users", {
                    "total_count": len(users_data),
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def search_users(self, keyword: str, limit: int = 20, offset: int = 0) -> List[User]:
        """
        搜索用户

        Args:
            keyword (str): 搜索关键词（用户名或邮箱）
            limit (int): 限制数量
            offset (int): 偏移量

        Returns:
            List[User]: 搜索结果
        """
        try:
            if not keyword:
                raise DataValidationError("搜索关键词不能为空")

            if limit <= 0 or limit > 100:
                raise DataValidationError("限制数量必须在1-100之间")

            if offset < 0:
                raise DataValidationError("偏移量不能为负数")

            # 使用UserDao的搜索方法
            users = self.user_dao.search_users(keyword.strip(), limit, offset)

            self.log_operation("search_users", {
                "keyword": keyword,
                "limit": limit,
                "offset": offset,
                "result_count": len(users),
                "status": "success"
            })

            return users

        except Exception as e:
            self.log_operation("search_users", {
                "keyword": keyword,
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)

    # ==================== 统计方法 ====================

    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        获取用户统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {
                'total_users': self.count_all(),
                'active_users': self.count_all(status=1),
                'inactive_users': self.count_all(status=0),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.log_operation("get_user_statistics", {
                "stats": stats,
                "status": "success"
            })

            return stats

        except Exception as e:
            self.log_operation("get_user_statistics", {
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)
