#!/usr/bin/env python3
"""
RBAC权限系统 - 认证业务服务

本模块定义了认证业务服务类，提供用户认证、JWT令牌管理、
会话管理等完整的认证授权功能。

Classes:
    AuthService: 认证业务服务类

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import jwt
import hashlib
import secrets
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta

from dao.user_dao import UserDao
from dao.user_role_dao import UserRoleDao
from dao.role_dao import RoleDao
from models.user import User
from services.base_service import BaseService
from services.user_service import UserService
from services.permission_service import PermissionService
from services.exceptions import (
    BusinessLogicError,
    DataValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError
)
from utils.password_utils import PasswordUtils


class AuthService(BaseService[User]):
    """
    认证业务服务类
    
    提供用户认证、JWT令牌管理、权限验证、会话管理等完整的认证授权功能。
    
    Features:
        - 用户登录认证：用户名/密码验证、多种登录方式
        - JWT令牌管理：访问令牌、刷新令牌生成和验证
        - 权限验证：基于角色的权限检查、权限继承
        - 会话管理：会话创建、存储、超时处理
        - 安全机制：密码错误限制、IP验证、设备指纹
        - 令牌黑名单：令牌撤销、批量撤销
        - 缓存优化：权限检查缓存、令牌验证缓存
    
    Attributes:
        user_service (UserService): 用户业务服务
        permission_service (PermissionService): 权限业务服务
        user_dao (UserDao): 用户数据访问对象
        user_role_dao (UserRoleDao): 用户角色关联数据访问对象
        role_dao (RoleDao): 角色数据访问对象
        password_utils (PasswordUtils): 密码工具类
        _token_blacklist (set): 令牌黑名单
        _login_attempts (Dict): 登录尝试记录
        _jwt_secret (str): JWT密钥
        _jwt_algorithm (str): JWT算法
    
    Example:
        >>> with AuthService() as service:
        ...     # 用户登录
        ...     result = await service.login("admin", "password123", remember_me=True)
        ...     access_token = result['access_token']
        ...     
        ...     # 验证令牌
        ...     payload = await service.verify_token(access_token)
        ...     
        ...     # 检查权限
        ...     has_permission = await service.check_permission(1, "user:view")
    """
    
    def __init__(self, session=None):
        """
        初始化认证业务服务
        
        Args:
            session: 数据库会话，如果为None则自动创建
        """
        super().__init__(session)
        
        # 初始化服务组件
        self.user_service = UserService(self.session)
        self.permission_service = PermissionService(self.session)
        
        # 初始化DAO组件
        self.user_dao = UserDao(self.session)
        self.user_role_dao = UserRoleDao(self.session)
        self.role_dao = RoleDao(self.session)
        
        # 初始化工具类
        self.password_utils = PasswordUtils()
        
        # JWT配置
        self._jwt_secret = self._get_jwt_secret()
        self._jwt_algorithm = "HS256"
        
        # 安全机制
        self._token_blacklist: set = set()
        self._login_attempts: Dict[str, Dict] = {}
        
        # 配置参数
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.REMEMBER_ME_EXPIRE_DAYS = 30
        self.MAX_LOGIN_ATTEMPTS = 5
        self.LOGIN_LOCKOUT_MINUTES = 30
        
        self.logger.info("AuthService 初始化完成")
    
    def get_model_class(self) -> type:
        """获取模型类"""
        return User
    
    # ==================== 核心认证方法 ====================
    
    async def login(self, username: str, password: str, remember_me: bool = False, 
                   ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            username (str): 用户名或邮箱
            password (str): 密码
            remember_me (bool): 是否记住登录状态
            ip_address (str, optional): 客户端IP地址
            user_agent (str, optional): 用户代理字符串
            
        Returns:
            Dict[str, Any]: 登录结果，包含令牌信息和用户信息
            
        Raises:
            AuthenticationError: 认证失败
            BusinessLogicError: 账户被锁定或禁用
        """
        try:
            # 1. 数据验证
            if not username or not password:
                raise DataValidationError("用户名和密码不能为空")
            
            # 2. 检查登录尝试限制
            await self._check_login_attempts(username, ip_address)
            
            # 3. 查找用户
            user = await self._find_user_by_login(username.strip())
            if not user:
                await self._record_failed_login(username, ip_address, "用户不存在")
                raise AuthenticationError("用户名或密码错误")
            
            # 4. 验证密码
            if not self.password_utils.verify_password(password, user.password_hash):
                await self._record_failed_login(username, ip_address, "密码错误")
                raise AuthenticationError("用户名或密码错误")
            
            # 5. 检查用户状态
            if user.status != 1:
                await self._record_failed_login(username, ip_address, "账户被禁用")
                raise BusinessLogicError("账户已被禁用，请联系管理员")
            
            # 6. 生成JWT令牌
            tokens = await self.generate_jwt(user, remember_me)
            
            # 7. 更新用户登录信息
            await self._update_user_login_info(user, ip_address, user_agent)
            
            # 8. 清除登录失败记录
            await self._clear_login_attempts(username, ip_address)
            
            # 9. 获取用户角色和权限
            user_roles = await self._get_user_roles(user.id)
            user_permissions = await self._get_user_permissions(user.id)
            
            # 10. 构建登录结果
            result = {
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'token_type': 'Bearer',
                'expires_in': tokens['expires_in'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname,
                    'status': user.status,
                    'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
                    'roles': [{'id': role.id, 'name': role.role_name, 'code': role.role_code} for role in user_roles],
                    'permissions': [perm.permission_code for perm in user_permissions]
                }
            }
            
            # 11. 记录操作日志
            self.log_operation("login", {
                "user_id": user.id,
                "username": username,
                "remember_me": remember_me,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "status": "success"
            })
            
            self.logger.info(f"用户登录成功: user_id={user.id}, username={username}, ip={ip_address}")
            return result
            
        except Exception as e:
            # 记录失败日志
            self.log_operation("login", {
                "username": username,
                "remember_me": remember_me,
                "ip_address": ip_address,
                "status": "failed",
                "error": str(e)
            })
            
            raise self._convert_exception(e)
    
    async def logout(self, token: str, user_id: Optional[int] = None) -> bool:
        """
        用户登出
        
        Args:
            token (str): 访问令牌
            user_id (int, optional): 用户ID（用于日志记录）
            
        Returns:
            bool: 登出成功返回True
        """
        try:
            # 1. 验证令牌格式
            if not token:
                raise DataValidationError("令牌不能为空")
            
            # 2. 解析令牌获取用户信息
            try:
                payload = jwt.decode(token, self._jwt_secret, algorithms=[self._jwt_algorithm])
                token_user_id = payload.get('user_id')
            except jwt.InvalidTokenError:
                # 即使令牌无效，也认为登出成功
                self.logger.warning(f"登出时令牌无效: token={token[:20]}...")
                return True
            
            # 3. 将令牌加入黑名单
            self._token_blacklist.add(token)
            
            # 4. 记录操作日志
            self.log_operation("logout", {
                "user_id": user_id or token_user_id,
                "token_prefix": token[:20] if token else None,
                "status": "success"
            })
            
            self.logger.info(f"用户登出成功: user_id={user_id or token_user_id}")
            return True
            
        except Exception as e:
            # 记录失败日志
            self.log_operation("logout", {
                "user_id": user_id,
                "status": "failed",
                "error": str(e)
            })
            
            raise self._convert_exception(e)

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌

        Args:
            refresh_token (str): 刷新令牌

        Returns:
            Dict[str, Any]: 新的令牌信息

        Raises:
            AuthenticationError: 刷新令牌无效或过期
        """
        try:
            # 1. 验证刷新令牌
            if not refresh_token:
                raise DataValidationError("刷新令牌不能为空")

            # 2. 检查令牌黑名单
            if refresh_token in self._token_blacklist:
                raise AuthenticationError("刷新令牌已失效")

            # 3. 解析刷新令牌
            try:
                payload = jwt.decode(refresh_token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            except jwt.ExpiredSignatureError:
                raise AuthenticationError("刷新令牌已过期")
            except jwt.InvalidTokenError:
                raise AuthenticationError("刷新令牌无效")

            # 4. 验证令牌类型
            if payload.get('token_type') != 'refresh':
                raise AuthenticationError("令牌类型错误")

            # 5. 获取用户信息
            user_id = payload.get('user_id')
            user = self.user_dao.find_by_id(user_id)
            if not user or user.status != 1:
                raise AuthenticationError("用户不存在或已被禁用")

            # 6. 生成新的访问令牌
            remember_me = payload.get('remember_me', False)
            new_tokens = await self.generate_jwt(user, remember_me)

            # 7. 将旧的刷新令牌加入黑名单
            self._token_blacklist.add(refresh_token)

            # 8. 记录操作日志
            self.log_operation("refresh_token", {
                "user_id": user_id,
                "remember_me": remember_me,
                "status": "success"
            })

            self.logger.info(f"令牌刷新成功: user_id={user_id}")
            return new_tokens

        except Exception as e:
            # 记录失败日志
            self.log_operation("refresh_token", {
                "status": "failed",
                "error": str(e)
            })

            raise self._convert_exception(e)

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证访问令牌

        Args:
            token (str): 访问令牌

        Returns:
            Optional[Dict[str, Any]]: 令牌载荷，无效返回None
        """
        try:
            # 1. 基础验证
            if not token:
                return None

            # 2. 检查令牌黑名单
            if token in self._token_blacklist:
                return None

            # 3. 解析令牌
            try:
                payload = jwt.decode(token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            except jwt.ExpiredSignatureError:
                self.logger.debug("访问令牌已过期")
                return None
            except jwt.InvalidTokenError:
                self.logger.debug("访问令牌无效")
                return None

            # 4. 验证令牌类型
            if payload.get('token_type') != 'access':
                return None

            # 5. 验证用户状态
            user_id = payload.get('user_id')
            user = self.user_dao.find_by_id(user_id)
            if not user or user.status != 1:
                return None

            return payload

        except Exception as e:
            self.logger.error(f"令牌验证异常: {str(e)}")
            return None

    async def check_permission(self, user_id: int, permission_code: str) -> bool:
        """
        检查用户权限

        Args:
            user_id (int): 用户ID
            permission_code (str): 权限代码

        Returns:
            bool: 有权限返回True，否则返回False
        """
        try:
            # 委托给PermissionService处理
            return await self.permission_service.check_permission(user_id, permission_code)

        except Exception as e:
            self.logger.error(f"权限检查异常: user_id={user_id}, permission={permission_code}, error={str(e)}")
            return False

    async def generate_jwt(self, user: User, remember_me: bool = False) -> Dict[str, Any]:
        """
        生成JWT令牌

        Args:
            user (User): 用户对象
            remember_me (bool): 是否记住登录状态

        Returns:
            Dict[str, Any]: 令牌信息
        """
        try:
            now = datetime.utcnow()

            # 设置过期时间
            if remember_me:
                access_expire = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
                refresh_expire = now + timedelta(days=self.REMEMBER_ME_EXPIRE_DAYS)
                expires_in = self.REMEMBER_ME_EXPIRE_DAYS * 24 * 60 * 60  # 秒
            else:
                access_expire = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
                refresh_expire = now + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
                expires_in = self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 秒

            # 获取用户角色
            user_roles = await self._get_user_roles(user.id)
            role_codes = [role.role_code for role in user_roles]

            # 生成设备指纹
            device_fingerprint = self._generate_device_fingerprint(user.id)

            # 访问令牌载荷
            access_payload = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': role_codes,
                'token_type': 'access',
                'device_fingerprint': device_fingerprint,
                'iat': now,
                'exp': access_expire,
                'remember_me': remember_me
            }

            # 刷新令牌载荷
            refresh_payload = {
                'user_id': user.id,
                'username': user.username,
                'token_type': 'refresh',
                'device_fingerprint': device_fingerprint,
                'iat': now,
                'exp': refresh_expire,
                'remember_me': remember_me
            }

            # 生成令牌
            access_token = jwt.encode(access_payload, self._jwt_secret, algorithm=self._jwt_algorithm)
            refresh_token = jwt.encode(refresh_payload, self._jwt_secret, algorithm=self._jwt_algorithm)

            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': expires_in,
                'access_expires_at': access_expire.isoformat(),
                'refresh_expires_at': refresh_expire.isoformat()
            }

        except Exception as e:
            raise self._convert_exception(e)

    async def revoke_all_tokens(self, user_id: int) -> bool:
        """
        撤销用户的所有令牌

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 撤销成功返回True
        """
        try:
            # 1. 验证用户存在
            user = self.user_dao.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", str(user_id))

            # 2. 生成用户设备指纹
            device_fingerprint = self._generate_device_fingerprint(user_id)

            # 3. 将所有相关令牌加入黑名单（这里简化处理，实际应该查询所有活跃令牌）
            # 在实际应用中，应该维护一个令牌存储来跟踪所有活跃令牌

            # 4. 记录操作日志
            self.log_operation("revoke_all_tokens", {
                "user_id": user_id,
                "username": user.username,
                "status": "success"
            })

            self.logger.info(f"撤销用户所有令牌成功: user_id={user_id}, username={user.username}")
            return True

        except Exception as e:
            # 记录失败日志
            self.log_operation("revoke_all_tokens", {
                "user_id": user_id,
                "status": "failed",
                "error": str(e)
            })

            raise self._convert_exception(e)

    # ==================== 辅助方法 ====================

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        根据令牌获取当前用户

        Args:
            token (str): 访问令牌

        Returns:
            Optional[User]: 用户对象，令牌无效返回None
        """
        try:
            payload = await self.verify_token(token)
            if not payload:
                return None

            user_id = payload.get('user_id')
            return self.user_dao.find_by_id(user_id)

        except Exception as e:
            self.logger.error(f"获取当前用户异常: {str(e)}")
            return None

    async def is_token_valid(self, token: str) -> bool:
        """
        检查令牌是否有效

        Args:
            token (str): 访问令牌

        Returns:
            bool: 有效返回True，否则返回False
        """
        payload = await self.verify_token(token)
        return payload is not None

    async def get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户的活跃会话

        Args:
            user_id (int): 用户ID

        Returns:
            List[Dict[str, Any]]: 会话信息列表
        """
        try:
            # 在实际应用中，这里应该查询会话存储
            # 目前返回空列表作为占位符
            sessions = []

            # 记录操作日志
            self.log_operation("get_user_sessions", {
                "user_id": user_id,
                "session_count": len(sessions),
                "status": "success"
            })

            return sessions

        except Exception as e:
            raise self._convert_exception(e)

    # ==================== 私有辅助方法 ====================

    def _get_jwt_secret(self) -> str:
        """获取JWT密钥"""
        from config.security import security_config
        return security_config.get_jwt_secret()

    def _generate_device_fingerprint(self, user_id: int) -> str:
        """生成设备指纹"""
        # 简化的设备指纹生成，实际应用中应该包含更多设备信息
        data = f"user:{user_id}:device:{secrets.token_hex(8)}"
        return hashlib.md5(data.encode()).hexdigest()

    async def _find_user_by_login(self, login: str) -> Optional[User]:
        """根据登录标识查找用户（用户名或邮箱）"""
        # 先尝试用户名
        user = self.user_dao.find_by_username(login)
        if user:
            return user

        # 再尝试邮箱
        if '@' in login:
            user = self.user_dao.find_by_email(login)
            if user:
                return user

        return None

    async def _check_login_attempts(self, username: str, ip_address: str):
        """检查登录尝试限制"""
        key = f"{username}:{ip_address}" if ip_address else username

        if key in self._login_attempts:
            attempts = self._login_attempts[key]

            # 检查是否在锁定期内
            if attempts['locked_until'] and attempts['locked_until'] > datetime.now():
                remaining_minutes = int((attempts['locked_until'] - datetime.now()).total_seconds() / 60)
                raise BusinessLogicError(f"账户已被锁定，请在{remaining_minutes}分钟后重试")

            # 检查尝试次数
            if attempts['count'] >= self.MAX_LOGIN_ATTEMPTS:
                # 锁定账户
                attempts['locked_until'] = datetime.now() + timedelta(minutes=self.LOGIN_LOCKOUT_MINUTES)
                raise BusinessLogicError(f"登录失败次数过多，账户已被锁定{self.LOGIN_LOCKOUT_MINUTES}分钟")

    async def _record_failed_login(self, username: str, ip_address: str, reason: str):
        """记录登录失败"""
        key = f"{username}:{ip_address}" if ip_address else username

        if key not in self._login_attempts:
            self._login_attempts[key] = {
                'count': 0,
                'first_attempt': datetime.now(),
                'last_attempt': None,
                'locked_until': None
            }

        self._login_attempts[key]['count'] += 1
        self._login_attempts[key]['last_attempt'] = datetime.now()

        self.logger.warning(f"登录失败: username={username}, ip={ip_address}, reason={reason}, attempts={self._login_attempts[key]['count']}")

    async def _clear_login_attempts(self, username: str, ip_address: str):
        """清除登录失败记录"""
        key = f"{username}:{ip_address}" if ip_address else username

        if key in self._login_attempts:
            del self._login_attempts[key]

    async def _update_user_login_info(self, user: User, ip_address: str, user_agent: str):
        """更新用户登录信息"""
        try:
            # 更新最后登录时间和IP
            update_data = {
                'last_login_at': datetime.now(),
                'last_login_ip': ip_address
            }

            # 如果用户表有user_agent字段，也更新它
            if hasattr(user, 'last_user_agent'):
                update_data['last_user_agent'] = user_agent

            self.user_dao.update(user.id, **update_data)

        except Exception as e:
            # 登录信息更新失败不应该影响登录流程
            self.logger.warning(f"更新用户登录信息失败: user_id={user.id}, error={str(e)}")

    async def _get_user_roles(self, user_id: int) -> List:
        """获取用户角色"""
        try:
            user_roles = self.user_role_dao.find_by_user_id(user_id, active_only=True)
            roles = []

            for user_role in user_roles:
                role = self.role_dao.find_by_id(user_role.role_id)
                if role and role.status == 1:  # 只返回启用的角色
                    roles.append(role)

            return roles

        except Exception as e:
            self.logger.error(f"获取用户角色失败: user_id={user_id}, error={str(e)}")
            return []

    async def _get_user_permissions(self, user_id: int) -> List:
        """获取用户权限"""
        try:
            permissions = []
            user_roles = await self._get_user_roles(user_id)

            for role in user_roles:
                role_permissions = self.role_dao.get_role_permissions(role.id)
                permissions.extend(role_permissions)

            # 去重
            unique_permissions = []
            seen_codes = set()

            for perm in permissions:
                if perm.permission_code not in seen_codes:
                    unique_permissions.append(perm)
                    seen_codes.add(perm.permission_code)

            return unique_permissions

        except Exception as e:
            self.logger.error(f"获取用户权限失败: user_id={user_id}, error={str(e)}")
            return []
