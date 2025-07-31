"""
RBAC权限系统 - 角色业务服务类

本模块定义了角色相关的业务逻辑服务，封装角色管理、权限分配、用户分配等核心功能。

Classes:
    RoleService: 角色业务服务类

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
from models.role import Role
from models.permission import Permission
from models.user import User
from dao.role_dao import RoleDao
from dao.role_permission_dao import RolePermissionDao
from dao.user_role_dao import UserRoleDao
from dao.permission_dao import PermissionDao
from dao.user_dao import UserDao


class RoleService(BaseService[Role]):
    """
    角色业务服务类
    
    封装角色相关的所有业务逻辑，包括角色管理、权限分配、用户分配、级联操作等。
    基于BaseService提供统一的事务管理、异常处理和日志记录。
    
    Features:
        - 角色创建、更新、删除
        - 权限分配和撤销
        - 用户角色分配
        - 级联操作处理
        - 完整的数据验证和审计日志
    
    Attributes:
        role_dao (RoleDao): 角色数据访问对象
        role_permission_dao (RolePermissionDao): 角色权限关联数据访问对象
        user_role_dao (UserRoleDao): 用户角色关联数据访问对象
        permission_dao (PermissionDao): 权限数据访问对象
        user_dao (UserDao): 用户数据访问对象
    
    Example:
        >>> with RoleService() as service:
        ...     role = await service.create_role("管理员", "admin", "系统管理员角色")
        ...     await service.assign_permissions(role.id, [1, 2, 3])
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        初始化角色服务
        
        Args:
            session (Session, optional): 数据库会话，如果不提供则创建新会话
        """
        super().__init__(session)
        
        # 初始化组件
        self.role_dao = RoleDao(self.session)
        self.role_permission_dao = RolePermissionDao(self.session)
        self.user_role_dao = UserRoleDao(self.session)
        self.permission_dao = PermissionDao(self.session)
        self.user_dao = UserDao(self.session)
        
        self.logger.info("RoleService 初始化完成")
    
    def get_model_class(self) -> Type[Role]:
        """获取服务对应的模型类"""
        return Role
    
    async def create_role(self, role_name: str, role_code: str, description: str = None, **kwargs) -> Role:
        """
        创建角色
        
        实现角色创建逻辑，包括数据验证、唯一性检查、角色创建等。
        
        Args:
            role_name (str): 角色名称
            role_code (str): 角色代码
            description (str, optional): 角色描述
            **kwargs: 其他角色属性
            
        Returns:
            Role: 创建的角色对象
            
        Raises:
            DataValidationError: 数据验证失败
            DuplicateResourceError: 角色名称或代码重复
            BusinessLogicError: 其他业务逻辑错误
        """
        with self.transaction():
            try:
                # 1. 数据验证
                self._validate_role_data(role_name, role_code)
                
                # 2. 唯一性检查
                await self._check_role_uniqueness(role_name, role_code)
                
                # 3. 创建角色对象
                role_data = {
                    'role_name': role_name.strip(),
                    'role_code': role_code.strip().lower(),
                    'status': kwargs.get('status', 1),  # 默认启用
                }
                
                # 添加描述字段（如果Role模型支持）
                if description:
                    role_data['description'] = description.strip()
                
                role = Role(**role_data)
                
                # 4. 数据验证
                role.validate()
                
                # 5. 保存角色
                created_role = self.save_entity(role)
                
                # 6. 记录操作日志
                self.log_operation("create_role", {
                    "role_id": created_role.id,
                    "role_name": role_name,
                    "role_code": role_code,
                    "status": "success"
                })
                
                self.logger.info(f"角色创建成功: role_name={role_name}, role_code={role_code}, role_id={created_role.id}")
                return created_role
                
            except Exception as e:
                self.log_operation("create_role", {
                    "role_name": role_name,
                    "role_code": role_code,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)
    
    async def update_role(self, role_id: int, **update_data) -> Role:
        """
        更新角色信息
        
        Args:
            role_id (int): 角色ID
            **update_data: 要更新的字段
            
        Returns:
            Role: 更新后的角色对象
            
        Raises:
            ResourceNotFoundError: 角色不存在
            DataValidationError: 数据验证失败
            DuplicateResourceError: 角色名称或代码重复
        """
        with self.transaction():
            try:
                # 1. 获取角色
                role = self.get_by_id(role_id)
                
                # 2. 验证更新数据
                if 'role_name' in update_data:
                    new_name = update_data['role_name'].strip()
                    if new_name != role.role_name:
                        self._validate_role_name(new_name)
                        await self._check_role_name_uniqueness(new_name, exclude_role_id=role_id)
                
                if 'role_code' in update_data:
                    new_code = update_data['role_code'].strip().lower()
                    if new_code != role.role_code:
                        self._validate_role_code(new_code)
                        await self._check_role_code_uniqueness(new_code, exclude_role_id=role_id)
                
                # 3. 过滤不允许直接更新的字段
                forbidden_fields = {'id', 'created_at'}
                filtered_data = {k: v for k, v in update_data.items() if k not in forbidden_fields}
                
                # 4. 更新角色
                updated_role = self.update_entity(role, **filtered_data)
                
                # 5. 记录操作日志
                self.log_operation("update_role", {
                    "role_id": role_id,
                    "updated_fields": list(filtered_data.keys()),
                    "status": "success"
                })
                
                self.logger.info(f"角色信息更新成功: role_id={role_id}, fields={list(filtered_data.keys())}")
                return updated_role
                
            except Exception as e:
                self.log_operation("update_role", {
                    "role_id": role_id,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)
    
    async def delete_role(self, role_id: int, force: bool = False) -> bool:
        """
        删除角色
        
        Args:
            role_id (int): 角色ID
            force (bool): 是否强制删除（忽略依赖检查）
            
        Returns:
            bool: 删除成功返回True
            
        Raises:
            ResourceNotFoundError: 角色不存在
            BusinessLogicError: 角色有依赖关系且未强制删除
        """
        with self.transaction():
            try:
                # 1. 检查角色是否存在
                role = self.get_by_id(role_id)
                
                # 2. 依赖关系检查
                if not force:
                    await self._check_role_dependencies(role_id)
                
                # 3. 级联删除处理
                await self._handle_role_cascade_deletion(role_id)
                
                # 4. 删除角色
                success = self.delete_by_id(role_id)
                
                if success:
                    # 5. 记录操作日志
                    self.log_operation("delete_role", {
                        "role_id": role_id,
                        "role_name": role.role_name,
                        "role_code": role.role_code,
                        "force": force,
                        "status": "success"
                    })
                    
                    self.logger.info(f"角色删除成功: role_id={role_id}, role_name={role.role_name}")
                
                return success
                
            except Exception as e:
                self.log_operation("delete_role", {
                    "role_id": role_id,
                    "force": force,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def assign_permissions(self, role_id: int, permission_ids: List[int], granted_by: Optional[int] = None) -> bool:
        """
        分配权限给角色

        Args:
            role_id (int): 角色ID
            permission_ids (List[int]): 权限ID列表
            granted_by (int, optional): 授权人ID

        Returns:
            bool: 分配成功返回True

        Raises:
            ResourceNotFoundError: 角色或权限不存在
            DataValidationError: 权限ID无效
            BusinessLogicError: 权限分配失败
        """
        with self.transaction():
            try:
                # 1. 验证角色存在
                role = self.get_by_id(role_id)

                # 2. 验证权限ID列表
                if not permission_ids:
                    raise DataValidationError("权限ID列表不能为空")

                valid_permission_ids = await self._validate_permission_ids(permission_ids)

                # 3. 检查权限分配的合理性
                await self._check_permission_assignment_validity(role_id, valid_permission_ids)

                # 4. 批量分配权限
                success_count = 0
                failed_permissions = []

                for permission_id in valid_permission_ids:
                    try:
                        # 检查是否已经分配
                        existing = self.role_permission_dao.find_by_role_permission(role_id, permission_id)
                        if existing and existing.status == 1:
                            continue  # 已经分配且启用，跳过

                        if existing and existing.status == 0:
                            # 重新启用已存在但禁用的关联
                            self.role_permission_dao.activate_grant(existing.id)
                        else:
                            # 创建新的权限分配
                            self.role_permission_dao.grant_permission(role_id, permission_id, granted_by)

                        success_count += 1

                    except Exception as e:
                        failed_permissions.append({"permission_id": permission_id, "error": str(e)})
                        self.logger.warning(f"权限分配失败: role_id={role_id}, permission_id={permission_id}, error={str(e)}")

                # 5. 记录操作日志
                self.log_operation("assign_permissions", {
                    "role_id": role_id,
                    "permission_ids": permission_ids,
                    "success_count": success_count,
                    "failed_count": len(failed_permissions),
                    "failed_permissions": failed_permissions,
                    "granted_by": granted_by,
                    "status": "success" if success_count > 0 else "failed"
                })

                if success_count > 0:
                    self.logger.info(f"权限分配成功: role_id={role_id}, success_count={success_count}")
                    return True
                else:
                    raise BusinessLogicError("所有权限分配都失败了")

            except Exception as e:
                self.log_operation("assign_permissions", {
                    "role_id": role_id,
                    "permission_ids": permission_ids,
                    "granted_by": granted_by,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def revoke_permissions(self, role_id: int, permission_ids: List[int]) -> bool:
        """
        撤销角色权限

        Args:
            role_id (int): 角色ID
            permission_ids (List[int]): 权限ID列表

        Returns:
            bool: 撤销成功返回True

        Raises:
            ResourceNotFoundError: 角色不存在
            DataValidationError: 权限ID无效
        """
        with self.transaction():
            try:
                # 1. 验证角色存在
                role = self.get_by_id(role_id)

                # 2. 验证权限ID列表
                if not permission_ids:
                    raise DataValidationError("权限ID列表不能为空")

                valid_permission_ids = await self._validate_permission_ids(permission_ids)

                # 3. 批量撤销权限
                success_count = 0
                failed_permissions = []

                for permission_id in valid_permission_ids:
                    try:
                        # 查找现有的权限分配
                        existing = self.role_permission_dao.find_by_role_permission(role_id, permission_id)
                        if existing and existing.status == 1:
                            # 撤销权限
                            self.role_permission_dao.revoke_permission(role_id, permission_id)
                            success_count += 1

                    except Exception as e:
                        failed_permissions.append({"permission_id": permission_id, "error": str(e)})
                        self.logger.warning(f"权限撤销失败: role_id={role_id}, permission_id={permission_id}, error={str(e)}")

                # 4. 记录操作日志
                self.log_operation("revoke_permissions", {
                    "role_id": role_id,
                    "permission_ids": permission_ids,
                    "success_count": success_count,
                    "failed_count": len(failed_permissions),
                    "failed_permissions": failed_permissions,
                    "status": "success" if success_count > 0 else "partial"
                })

                self.logger.info(f"权限撤销完成: role_id={role_id}, success_count={success_count}")
                return success_count > 0

            except Exception as e:
                self.log_operation("revoke_permissions", {
                    "role_id": role_id,
                    "permission_ids": permission_ids,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def get_role_users(self, role_id: int, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """
        获取角色用户（分页）

        Args:
            role_id (int): 角色ID
            page (int): 页码，从1开始
            size (int): 每页大小

        Returns:
            Dict[str, Any]: 包含用户列表和分页信息的字典

        Raises:
            ResourceNotFoundError: 角色不存在
            DataValidationError: 分页参数无效
        """
        try:
            # 1. 验证角色存在
            role = self.get_by_id(role_id)

            # 2. 验证分页参数
            if page < 1:
                raise DataValidationError("页码必须大于0")
            if size < 1 or size > 100:
                raise DataValidationError("每页大小必须在1-100之间")

            # 3. 获取角色用户
            users = self.role_dao.get_role_users(role_id)

            # 4. 分页处理
            total = len(users)
            start = (page - 1) * size
            end = start + size
            page_users = users[start:end]

            # 5. 构建返回数据
            result = {
                'users': [user.to_dict() for user in page_users],
                'pagination': {
                    'page': page,
                    'size': size,
                    'total': total,
                    'pages': (total + size - 1) // size
                },
                'role_info': {
                    'id': role.id,
                    'role_name': role.role_name,
                    'role_code': role.role_code
                }
            }

            # 6. 记录操作日志
            self.log_operation("get_role_users", {
                "role_id": role_id,
                "page": page,
                "size": size,
                "total": total,
                "status": "success"
            })

            return result

        except Exception as e:
            self.log_operation("get_role_users", {
                "role_id": role_id,
                "page": page,
                "size": size,
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)

    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """
        获取角色权限

        Args:
            role_id (int): 角色ID

        Returns:
            List[Permission]: 权限列表

        Raises:
            ResourceNotFoundError: 角色不存在
        """
        try:
            # 1. 验证角色存在
            role = self.get_by_id(role_id)

            # 2. 获取角色权限
            permissions = self.role_dao.get_role_permissions(role_id)

            # 3. 记录操作日志
            self.log_operation("get_role_permissions", {
                "role_id": role_id,
                "permission_count": len(permissions),
                "status": "success"
            })

            return permissions

        except Exception as e:
            self.log_operation("get_role_permissions", {
                "role_id": role_id,
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)

    async def assign_users(self, role_id: int, user_ids: List[int], assigned_by: Optional[int] = None) -> bool:
        """
        分配用户给角色

        Args:
            role_id (int): 角色ID
            user_ids (List[int]): 用户ID列表
            assigned_by (int, optional): 分配人ID

        Returns:
            bool: 分配成功返回True

        Raises:
            ResourceNotFoundError: 角色或用户不存在
            DataValidationError: 用户ID无效
            BusinessLogicError: 用户分配失败
        """
        with self.transaction():
            try:
                # 1. 验证角色存在
                role = self.get_by_id(role_id)

                # 2. 验证用户ID列表
                if not user_ids:
                    raise DataValidationError("用户ID列表不能为空")

                valid_user_ids = await self._validate_user_ids(user_ids)

                # 3. 批量分配用户
                success_count = 0
                failed_users = []

                for user_id in valid_user_ids:
                    try:
                        # 检查是否已经分配
                        existing = self.user_role_dao.find_by_user_role(user_id, role_id)
                        if existing and existing.status == 1:
                            continue  # 已经分配且启用，跳过

                        if existing and existing.status == 0:
                            # 重新启用已存在但禁用的关联
                            self.user_role_dao.activate_assignment(existing.id)
                        else:
                            # 创建新的用户角色分配
                            self.user_role_dao.assign_role(user_id, role_id, assigned_by)

                        success_count += 1

                    except Exception as e:
                        failed_users.append({"user_id": user_id, "error": str(e)})
                        self.logger.warning(f"用户分配失败: role_id={role_id}, user_id={user_id}, error={str(e)}")

                # 4. 记录操作日志
                self.log_operation("assign_users", {
                    "role_id": role_id,
                    "user_ids": user_ids,
                    "success_count": success_count,
                    "failed_count": len(failed_users),
                    "failed_users": failed_users,
                    "assigned_by": assigned_by,
                    "status": "success" if success_count > 0 else "failed"
                })

                if success_count > 0:
                    self.logger.info(f"用户分配成功: role_id={role_id}, success_count={success_count}")
                    return True
                else:
                    raise BusinessLogicError("所有用户分配都失败了")

            except Exception as e:
                self.log_operation("assign_users", {
                    "role_id": role_id,
                    "user_ids": user_ids,
                    "assigned_by": assigned_by,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def revoke_users(self, role_id: int, user_ids: List[int]) -> bool:
        """
        撤销角色用户

        Args:
            role_id (int): 角色ID
            user_ids (List[int]): 用户ID列表

        Returns:
            bool: 撤销成功返回True

        Raises:
            ResourceNotFoundError: 角色不存在
            DataValidationError: 用户ID无效
        """
        with self.transaction():
            try:
                # 1. 验证角色存在
                role = self.get_by_id(role_id)

                # 2. 验证用户ID列表
                if not user_ids:
                    raise DataValidationError("用户ID列表不能为空")

                valid_user_ids = await self._validate_user_ids(user_ids)

                # 3. 批量撤销用户
                success_count = 0
                failed_users = []

                for user_id in valid_user_ids:
                    try:
                        # 查找现有的用户角色分配
                        existing = self.user_role_dao.find_by_user_role(user_id, role_id)
                        if existing and existing.status == 1:
                            # 撤销用户角色
                            self.user_role_dao.revoke_role(user_id, role_id)
                            success_count += 1

                    except Exception as e:
                        failed_users.append({"user_id": user_id, "error": str(e)})
                        self.logger.warning(f"用户撤销失败: role_id={role_id}, user_id={user_id}, error={str(e)}")

                # 4. 记录操作日志
                self.log_operation("revoke_users", {
                    "role_id": role_id,
                    "user_ids": user_ids,
                    "success_count": success_count,
                    "failed_count": len(failed_users),
                    "failed_users": failed_users,
                    "status": "success" if success_count > 0 else "partial"
                })

                self.logger.info(f"用户撤销完成: role_id={role_id}, success_count={success_count}")
                return success_count > 0

            except Exception as e:
                self.log_operation("revoke_users", {
                    "role_id": role_id,
                    "user_ids": user_ids,
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    # ==================== 辅助方法 ====================

    async def get_role_by_code(self, role_code: str) -> Optional[Role]:
        """
        根据角色代码获取角色

        Args:
            role_code (str): 角色代码

        Returns:
            Optional[Role]: 角色对象，不存在返回None
        """
        try:
            if not role_code:
                raise DataValidationError("角色代码不能为空")

            return self.role_dao.find_by_role_code(role_code.strip().lower())

        except Exception as e:
            raise self._convert_exception(e)

    async def get_role_by_name(self, role_name: str) -> Optional[Role]:
        """
        根据角色名称获取角色

        Args:
            role_name (str): 角色名称

        Returns:
            Optional[Role]: 角色对象，不存在返回None
        """
        try:
            if not role_name:
                raise DataValidationError("角色名称不能为空")

            return self.role_dao.find_by_name(role_name.strip())

        except Exception as e:
            raise self._convert_exception(e)

    async def get_active_roles(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Role]:
        """
        获取活跃角色列表

        Args:
            limit (int, optional): 限制数量
            offset (int, optional): 偏移量

        Returns:
            List[Role]: 活跃角色列表
        """
        try:
            if limit is not None and limit <= 0:
                raise DataValidationError("限制数量必须大于0")
            if offset is not None and offset < 0:
                raise DataValidationError("偏移量不能为负数")

            # 使用BaseService的find_all方法
            roles = self.find_all(limit=limit, offset=offset, status=1)

            return roles

        except Exception as e:
            raise self._convert_exception(e)

    async def search_roles(self, keyword: str, limit: int = 20, offset: int = 0) -> List[Role]:
        """
        搜索角色

        Args:
            keyword (str): 搜索关键词（角色名称或代码）
            limit (int): 限制数量
            offset (int): 偏移量

        Returns:
            List[Role]: 搜索结果
        """
        try:
            if not keyword:
                raise DataValidationError("搜索关键词不能为空")

            if limit <= 0 or limit > 100:
                raise DataValidationError("限制数量必须在1-100之间")

            if offset < 0:
                raise DataValidationError("偏移量不能为负数")

            # 使用RoleDao的搜索方法
            roles = self.role_dao.search_roles(keyword.strip(), limit, offset)

            self.log_operation("search_roles", {
                "keyword": keyword,
                "limit": limit,
                "offset": offset,
                "result_count": len(roles),
                "status": "success"
            })

            return roles

        except Exception as e:
            self.log_operation("search_roles", {
                "keyword": keyword,
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)

    # ==================== 数据验证方法 ====================

    def _validate_role_data(self, role_name: str, role_code: str):
        """验证角色基础数据"""
        if not role_name or not role_code:
            raise DataValidationError("角色名称和角色代码不能为空")

        self._validate_role_name(role_name)
        self._validate_role_code(role_code)

    def _validate_role_name(self, role_name: str):
        """验证角色名称格式"""
        if not role_name:
            raise DataValidationError("角色名称不能为空")

        role_name = role_name.strip()

        # 长度检查
        if len(role_name) < 2 or len(role_name) > 100:
            raise DataValidationError("角色名称长度必须在2-100字符之间")

        # 格式检查：不能包含特殊字符
        if re.search(r'[<>"\'\\/]', role_name):
            raise DataValidationError("角色名称不能包含特殊字符 < > \" ' \\ /")

    def _validate_role_code(self, role_code: str):
        """验证角色代码格式"""
        if not role_code:
            raise DataValidationError("角色代码不能为空")

        role_code = role_code.strip().lower()

        # 长度检查
        if len(role_code) < 2 or len(role_code) > 50:
            raise DataValidationError("角色代码长度必须在2-50字符之间")

        # 格式检查：字母数字下划线，字母开头
        if not re.match(r'^[a-z][a-z0-9_]*$', role_code):
            raise DataValidationError("角色代码必须以字母开头，只能包含小写字母、数字和下划线")

    async def _validate_permission_ids(self, permission_ids: List[int]) -> List[int]:
        """验证权限ID列表"""
        if not permission_ids:
            raise DataValidationError("权限ID列表不能为空")

        # 去重并验证每个权限ID
        valid_ids = []
        for permission_id in set(permission_ids):
            if not isinstance(permission_id, int) or permission_id <= 0:
                raise DataValidationError(f"无效的权限ID: {permission_id}")

            # 检查权限是否存在
            permission = self.permission_dao.find_by_id(permission_id)
            if not permission:
                raise ResourceNotFoundError("Permission", str(permission_id))

            valid_ids.append(permission_id)

        return valid_ids

    async def _validate_user_ids(self, user_ids: List[int]) -> List[int]:
        """验证用户ID列表"""
        if not user_ids:
            raise DataValidationError("用户ID列表不能为空")

        # 去重并验证每个用户ID
        valid_ids = []
        for user_id in set(user_ids):
            if not isinstance(user_id, int) or user_id <= 0:
                raise DataValidationError(f"无效的用户ID: {user_id}")

            # 检查用户是否存在
            user = self.user_dao.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", str(user_id))

            valid_ids.append(user_id)

        return valid_ids

    # ==================== 唯一性检查方法 ====================

    async def _check_role_uniqueness(self, role_name: str, role_code: str, exclude_role_id: Optional[int] = None):
        """检查角色名称和代码唯一性"""
        await self._check_role_name_uniqueness(role_name, exclude_role_id)
        await self._check_role_code_uniqueness(role_code, exclude_role_id)

    async def _check_role_name_uniqueness(self, role_name: str, exclude_role_id: Optional[int] = None):
        """检查角色名称唯一性"""
        existing_role = self.role_dao.find_by_name(role_name.strip())
        if existing_role and (exclude_role_id is None or existing_role.id != exclude_role_id):
            raise DuplicateResourceError(
                resource_type="Role",
                field_name="role_name",
                field_value=role_name,
                message=f"角色名称 '{role_name}' 已存在"
            )

    async def _check_role_code_uniqueness(self, role_code: str, exclude_role_id: Optional[int] = None):
        """检查角色代码唯一性"""
        existing_role = self.role_dao.find_by_role_code(role_code.strip().lower())
        if existing_role and (exclude_role_id is None or existing_role.id != exclude_role_id):
            raise DuplicateResourceError(
                resource_type="Role",
                field_name="role_code",
                field_value=role_code,
                message=f"角色代码 '{role_code}' 已存在"
            )

    # ==================== 业务逻辑检查方法 ====================

    async def _check_role_dependencies(self, role_id: int):
        """检查角色依赖关系"""
        # 检查是否有用户使用此角色
        users = self.role_dao.get_role_users(role_id)
        if users:
            raise BusinessLogicError(
                f"角色正在被 {len(users)} 个用户使用，无法删除。请先撤销用户角色分配或使用强制删除。"
            )

    async def _check_permission_assignment_validity(self, role_id: int, permission_ids: List[int]):
        """检查权限分配的合理性"""
        # 这里可以添加业务规则检查，比如：
        # 1. 权限层级检查
        # 2. 权限冲突检测
        # 3. 权限范围验证
        # 目前暂时通过所有检查
        pass

    async def _handle_role_cascade_deletion(self, role_id: int):
        """处理角色级联删除"""
        try:
            # 1. 删除角色权限关联
            role_permissions = self.role_permission_dao.find_by_role_id(role_id)
            for rp in role_permissions:
                self.role_permission_dao.delete_by_id(rp.id)

            # 2. 删除用户角色关联
            user_roles = self.user_role_dao.find_by_role_id(role_id)
            for ur in user_roles:
                self.user_role_dao.delete_by_id(ur.id)

            self.logger.info(f"角色级联删除完成: role_id={role_id}, "
                           f"删除权限关联={len(role_permissions)}, 删除用户关联={len(user_roles)}")

        except Exception as e:
            self.logger.error(f"角色级联删除失败: role_id={role_id}, error={str(e)}")
            raise BusinessLogicError(f"角色级联删除失败: {str(e)}")

    # ==================== 统计方法 ====================

    async def get_role_statistics(self) -> Dict[str, Any]:
        """
        获取角色统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {
                'total_roles': self.count_all(),
                'active_roles': self.count_all(status=1),
                'inactive_roles': self.count_all(status=0),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # 获取角色权限统计
            all_roles = self.find_all()
            role_permission_stats = []
            for role in all_roles:
                permissions = self.role_dao.get_role_permissions(role.id)
                users = self.role_dao.get_role_users(role.id)
                role_permission_stats.append({
                    'role_id': role.id,
                    'role_name': role.role_name,
                    'role_code': role.role_code,
                    'permission_count': len(permissions),
                    'user_count': len(users)
                })

            stats['role_details'] = role_permission_stats

            self.log_operation("get_role_statistics", {
                "stats": {k: v for k, v in stats.items() if k != 'role_details'},
                "status": "success"
            })

            return stats

        except Exception as e:
            self.log_operation("get_role_statistics", {
                "status": "failed",
                "error": str(e)
            })
            raise self._convert_exception(e)

    # ==================== 批量操作方法 ====================

    async def batch_create_roles(self, roles_data: List[Dict[str, Any]]) -> List[Role]:
        """
        批量创建角色

        Args:
            roles_data (List[Dict]): 角色数据列表

        Returns:
            List[Role]: 创建的角色列表

        Raises:
            DataValidationError: 数据验证失败
            DuplicateResourceError: 角色名称或代码重复
        """
        with self.transaction():
            try:
                created_roles = []

                for i, role_data in enumerate(roles_data):
                    try:
                        role_name = role_data.get('role_name')
                        role_code = role_data.get('role_code')
                        description = role_data.get('description')

                        if not all([role_name, role_code]):
                            raise DataValidationError(f"第{i+1}个角色数据不完整")

                        # 创建角色（会自动进行验证和唯一性检查）
                        role = await self.create_role(role_name, role_code, description, **{
                            k: v for k, v in role_data.items()
                            if k not in ['role_name', 'role_code', 'description']
                        })
                        created_roles.append(role)

                    except Exception as e:
                        raise DataValidationError(f"第{i+1}个角色创建失败: {str(e)}")

                # 记录批量操作日志
                self.log_operation("batch_create_roles", {
                    "total_count": len(roles_data),
                    "success_count": len(created_roles),
                    "status": "success"
                })

                self.logger.info(f"批量创建角色成功: 总数={len(roles_data)}, 成功={len(created_roles)}")
                return created_roles

            except Exception as e:
                self.log_operation("batch_create_roles", {
                    "total_count": len(roles_data),
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)

    async def batch_assign_permissions(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量分配权限

        Args:
            assignments (List[Dict]): 分配数据列表，每个包含role_id和permission_ids

        Returns:
            Dict[str, Any]: 批量分配结果
        """
        with self.transaction():
            try:
                results = []
                total_success = 0
                total_failed = 0

                for assignment in assignments:
                    role_id = assignment.get('role_id')
                    permission_ids = assignment.get('permission_ids', [])
                    granted_by = assignment.get('granted_by')

                    try:
                        success = await self.assign_permissions(role_id, permission_ids, granted_by)
                        results.append({
                            'role_id': role_id,
                            'permission_ids': permission_ids,
                            'success': success,
                            'error': None
                        })
                        if success:
                            total_success += 1
                        else:
                            total_failed += 1

                    except Exception as e:
                        results.append({
                            'role_id': role_id,
                            'permission_ids': permission_ids,
                            'success': False,
                            'error': str(e)
                        })
                        total_failed += 1

                # 构建返回结果
                result = {
                    'total_assignments': len(assignments),
                    'success_count': total_success,
                    'failed_count': total_failed,
                    'results': results
                }

                # 记录批量操作日志
                self.log_operation("batch_assign_permissions", {
                    "total_assignments": len(assignments),
                    "success_count": total_success,
                    "failed_count": total_failed,
                    "status": "success"
                })

                self.logger.info(f"批量分配权限完成: 总数={len(assignments)}, 成功={total_success}, 失败={total_failed}")
                return result

            except Exception as e:
                self.log_operation("batch_assign_permissions", {
                    "total_assignments": len(assignments),
                    "status": "failed",
                    "error": str(e)
                })
                raise self._convert_exception(e)
