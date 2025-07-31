#!/usr/bin/env python3
"""
RBAC权限系统 - 权限业务服务

本模块定义了权限业务服务类，提供权限管理的完整业务逻辑，
包括权限创建、更新、删除、权限树构建、权限检查等功能。

Classes:
    PermissionService: 权限业务服务类

Author: RBAC System Development Team
Created: 2025-07-21
Version: 1.0.0
"""

import re
from typing import List, Dict, Optional, Any, Set
from datetime import datetime

from dao.permission_dao import PermissionDao
from dao.role_permission_dao import RolePermissionDao
from dao.user_role_dao import UserRoleDao
from dao.role_dao import RoleDao
from dao.user_dao import UserDao
from models.permission import Permission
from models.role import Role
from models.user import User
from services.base_service import BaseService
from services.exceptions import (
    BusinessLogicError,
    DataValidationError,
    DuplicateResourceError,
    ResourceNotFoundError
)


class PermissionService(BaseService[Permission]):
    """
    权限业务服务类
    
    提供权限管理的完整业务逻辑，包括权限的创建、更新、删除、查询，
    权限树结构构建，权限检查机制，以及批量操作等功能。
    
    Features:
        - 权限CRUD操作：创建、更新、删除、查询权限
        - 权限代码规范：resource:action格式验证和生成
        - 权限树结构：按资源类型分组的层级结构构建
        - 权限检查机制：用户权限验证和继承检查
        - 批量操作：支持批量创建、更新、删除权限
        - 关联查询：权限角色关联、权限用户关联
        - 数据验证：权限代码格式、唯一性验证
        - 缓存优化：高频权限检查的缓存机制
    
    Attributes:
        permission_dao (PermissionDao): 权限数据访问对象
        role_permission_dao (RolePermissionDao): 角色权限关联数据访问对象
        user_role_dao (UserRoleDao): 用户角色关联数据访问对象
        role_dao (RoleDao): 角色数据访问对象
        user_dao (UserDao): 用户数据访问对象
        _permission_cache (Dict): 权限检查缓存
    
    Example:
        >>> with PermissionService() as service:
        ...     # 创建权限
        ...     permission = await service.create_permission(
        ...         "用户查看", "user:view", "user", "view", "查看用户信息"
        ...     )
        ...     
        ...     # 检查用户权限
        ...     has_permission = await service.check_permission(1, "user:view")
        ...     
        ...     # 获取权限树
        ...     tree = await service.get_permission_tree("user")
    """
    
    def __init__(self, session=None):
        """
        初始化权限业务服务
        
        Args:
            session: 数据库会话，如果为None则自动创建
        """
        super().__init__(session)
        
        # 初始化DAO组件
        self.permission_dao = PermissionDao(self.session)
        self.role_permission_dao = RolePermissionDao(self.session)
        self.user_role_dao = UserRoleDao(self.session)
        self.role_dao = RoleDao(self.session)
        self.user_dao = UserDao(self.session)
        
        # 权限检查缓存
        self._permission_cache: Dict[str, Any] = {}
        
        self.logger.info("PermissionService 初始化完成")
    
    def get_model_class(self) -> type:
        """获取模型类"""
        return Permission
    
    # ==================== 核心业务方法 ====================
    
    async def create_permission(
        self, 
        name: str, 
        code: str, 
        resource_type: str, 
        action_type: str, 
        description: str = None
    ) -> Permission:
        """
        创建权限
        
        Args:
            name (str): 权限名称
            code (str): 权限代码（resource:action格式）
            resource_type (str): 资源类型
            action_type (str): 操作类型
            description (str, optional): 权限描述
            
        Returns:
            Permission: 创建的权限对象
            
        Raises:
            DataValidationError: 数据验证失败
            DuplicateResourceError: 权限代码重复
            BusinessLogicError: 业务逻辑错误
        """
        try:
            with self.transaction():
                # 1. 数据验证
                await self._validate_permission_data(name, code, resource_type, action_type)
                
                # 2. 检查权限代码唯一性
                await self._check_permission_code_uniqueness(code)
                
                # 3. 验证权限代码格式
                self._validate_permission_code_format(code, resource_type, action_type)
                
                # 4. 创建权限对象
                permission = Permission(
                    permission_name=name.strip(),
                    permission_code=code.strip().lower(),
                    resource_type=resource_type.strip().lower(),
                    action_type=action_type.strip().lower(),
                    description=description.strip() if description else None
                )
                
                # 5. 保存权限
                saved_permission = self.save_entity(permission)
                
                # 6. 清除相关缓存
                self._clear_permission_cache()
                
                # 7. 记录操作日志
                self.log_operation("create_permission", {
                    "permission_id": saved_permission.id,
                    "permission_name": name,
                    "permission_code": code,
                    "resource_type": resource_type,
                    "action_type": action_type,
                    "status": "success"
                })
                
                self.logger.info(f"权限创建成功: name={name}, code={code}, permission_id={saved_permission.id}")
                return saved_permission
                
        except Exception as e:
            # 记录失败日志
            self.log_operation("create_permission", {
                "permission_name": name,
                "permission_code": code,
                "resource_type": resource_type,
                "action_type": action_type,
                "status": "failed",
                "error": str(e)
            })
            
            self.logger.error(f"事务回滚: {str(e)}")
            raise self._convert_exception(e)
    
    async def update_permission(self, permission_id: int, **update_data) -> Permission:
        """
        更新权限信息
        
        Args:
            permission_id (int): 权限ID
            **update_data: 要更新的字段数据
            
        Returns:
            Permission: 更新后的权限对象
            
        Raises:
            ResourceNotFoundError: 权限不存在
            DataValidationError: 数据验证失败
            DuplicateResourceError: 权限代码重复
        """
        try:
            with self.transaction():
                # 1. 验证权限存在
                permission = self.get_by_id(permission_id)
                
                # 2. 过滤禁止更新的字段
                forbidden_fields = {'id', 'created_at'}
                filtered_data = {k: v for k, v in update_data.items() if k not in forbidden_fields}
                
                # 3. 验证更新数据
                if 'permission_code' in filtered_data:
                    new_code = filtered_data['permission_code'].strip().lower()
                    if new_code != permission.permission_code:
                        await self._check_permission_code_uniqueness(new_code, permission_id)
                
                # 4. 验证权限代码格式一致性
                if any(field in filtered_data for field in ['permission_code', 'resource_type', 'action_type']):
                    resource_type = filtered_data.get('resource_type', permission.resource_type)
                    action_type = filtered_data.get('action_type', permission.action_type)
                    code = filtered_data.get('permission_code', permission.permission_code)
                    self._validate_permission_code_format(code, resource_type, action_type)
                
                # 5. 更新权限
                updated_permission = self.update_entity(permission, **filtered_data)
                
                # 6. 清除相关缓存
                self._clear_permission_cache()
                
                # 7. 记录操作日志
                self.log_operation("update_permission", {
                    "permission_id": permission_id,
                    "updated_fields": list(filtered_data.keys()),
                    "status": "success"
                })
                
                self.logger.info(f"权限信息更新成功: permission_id={permission_id}, fields={list(filtered_data.keys())}")
                return updated_permission
                
        except Exception as e:
            # 记录失败日志
            self.log_operation("update_permission", {
                "permission_id": permission_id,
                "status": "failed",
                "error": str(e)
            })
            
            self.logger.error(f"事务回滚: {str(e)}")
            raise self._convert_exception(e)
    
    async def delete_permission(self, permission_id: int, force: bool = False) -> bool:
        """
        删除权限
        
        Args:
            permission_id (int): 权限ID
            force (bool): 是否强制删除（忽略依赖关系）
            
        Returns:
            bool: 删除成功返回True
            
        Raises:
            ResourceNotFoundError: 权限不存在
            BusinessLogicError: 权限有依赖关系且非强制删除
        """
        try:
            with self.transaction():
                # 1. 验证权限存在
                permission = self.get_by_id(permission_id)
                
                # 2. 检查权限依赖关系
                if not force:
                    await self._check_permission_dependencies(permission_id)
                
                # 3. 处理级联删除
                await self._handle_permission_cascade_deletion(permission_id)
                
                # 4. 删除权限
                success = self.delete_by_id(permission_id)
                
                # 5. 清除相关缓存
                self._clear_permission_cache()
                
                # 6. 记录操作日志
                self.log_operation("delete_permission", {
                    "permission_id": permission_id,
                    "permission_name": permission.permission_name,
                    "permission_code": permission.permission_code,
                    "force": force,
                    "status": "success"
                })
                
                self.logger.info(f"权限删除成功: permission_id={permission_id}, name={permission.permission_name}")
                return success
                
        except Exception as e:
            # 记录失败日志
            self.log_operation("delete_permission", {
                "permission_id": permission_id,
                "force": force,
                "status": "failed",
                "error": str(e)
            })
            
            self.logger.error(f"事务回滚: {str(e)}")
            raise self._convert_exception(e)

    async def get_permission_tree(self, resource_type: str = None) -> Dict[str, Any]:
        """
        获取权限树结构

        Args:
            resource_type (str, optional): 指定资源类型，为None时返回所有资源的权限树

        Returns:
            Dict[str, Any]: 权限树结构

        Example:
            {
                "user": {
                    "resource_name": "用户管理",
                    "permissions": [
                        {"id": 1, "name": "查看用户", "code": "user:view", "action": "view"},
                        {"id": 2, "name": "创建用户", "code": "user:create", "action": "create"}
                    ]
                },
                "role": {
                    "resource_name": "角色管理",
                    "permissions": [...]
                }
            }
        """
        try:
            # 1. 获取权限数据
            if resource_type:
                permissions = self.permission_dao.find_by_resource_type(resource_type.strip().lower())
            else:
                grouped_permissions = self.permission_dao.get_permissions_by_resource()
                permissions = []
                for perms in grouped_permissions.values():
                    permissions.extend(perms)

            # 2. 构建权限树
            tree = {}
            for permission in permissions:
                resource = permission.resource_type
                if resource not in tree:
                    tree[resource] = {
                        "resource_name": self._get_resource_display_name(resource),
                        "resource_type": resource,
                        "permissions": []
                    }

                tree[resource]["permissions"].append({
                    "id": permission.id,
                    "name": permission.permission_name,
                    "code": permission.permission_code,
                    "action": permission.action_type,
                    "description": getattr(permission, 'description', None),
                    "created_at": permission.created_at.isoformat() if permission.created_at else None
                })

            # 3. 按操作类型排序权限
            for resource_data in tree.values():
                resource_data["permissions"].sort(key=lambda x: self._get_action_priority(x["action"]))

            # 4. 记录操作日志
            self.log_operation("get_permission_tree", {
                "resource_type": resource_type,
                "tree_size": len(tree),
                "total_permissions": sum(len(data["permissions"]) for data in tree.values()),
                "status": "success"
            })

            return tree

        except Exception as e:
            raise self._convert_exception(e)

    async def check_permission(self, user_id: int, permission_code: str) -> bool:
        """
        检查用户是否具有指定权限

        Args:
            user_id (int): 用户ID
            permission_code (str): 权限代码

        Returns:
            bool: 有权限返回True，否则返回False

        Raises:
            ResourceNotFoundError: 用户不存在
            DataValidationError: 权限代码格式错误
        """
        try:
            # 1. 验证用户存在
            user = self.user_dao.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", str(user_id))

            # 2. 验证权限代码格式
            if not self._is_valid_permission_code(permission_code):
                raise DataValidationError(f"权限代码格式错误: {permission_code}")

            # 3. 检查缓存
            cache_key = f"user:{user_id}:permission:{permission_code}"
            if cache_key in self._permission_cache:
                cached_result = self._permission_cache[cache_key]
                if cached_result['expires'] > datetime.now():
                    return cached_result['has_permission']

            # 4. 检查管理员权限（admin:* 拥有所有权限）
            if await self._check_admin_permission(user_id):
                self._cache_permission_result(cache_key, True)
                return True

            # 5. 检查直接权限
            has_direct_permission = await self._check_direct_permission(user_id, permission_code)
            if has_direct_permission:
                self._cache_permission_result(cache_key, True)
                return True

            # 6. 检查继承权限
            has_inherited_permission = await self._check_inherited_permission(user_id, permission_code)

            # 7. 缓存结果
            result = has_direct_permission or has_inherited_permission
            self._cache_permission_result(cache_key, result)

            # 8. 记录操作日志
            self.log_operation("check_permission", {
                "user_id": user_id,
                "permission_code": permission_code,
                "has_permission": result,
                "check_method": "direct" if has_direct_permission else ("inherited" if has_inherited_permission else "none"),
                "status": "success"
            })

            return result

        except Exception as e:
            raise self._convert_exception(e)

    async def get_resource_permissions(self, resource_type: str) -> List[Permission]:
        """
        获取指定资源类型的所有权限

        Args:
            resource_type (str): 资源类型

        Returns:
            List[Permission]: 权限列表
        """
        try:
            if not resource_type:
                raise DataValidationError("资源类型不能为空")

            permissions = self.permission_dao.find_by_resource_type(resource_type.strip().lower())

            # 记录操作日志
            self.log_operation("get_resource_permissions", {
                "resource_type": resource_type,
                "permission_count": len(permissions),
                "status": "success"
            })

            return permissions

        except Exception as e:
            raise self._convert_exception(e)

    async def get_permission_roles(self, permission_id: int) -> List[Role]:
        """
        获取拥有指定权限的所有角色

        Args:
            permission_id (int): 权限ID

        Returns:
            List[Role]: 角色列表

        Raises:
            ResourceNotFoundError: 权限不存在
        """
        try:
            # 1. 验证权限存在
            permission = self.get_by_id(permission_id)

            # 2. 获取权限角色
            roles = self.permission_dao.get_permission_roles(permission_id)

            # 3. 记录操作日志
            self.log_operation("get_permission_roles", {
                "permission_id": permission_id,
                "permission_code": permission.permission_code,
                "role_count": len(roles),
                "status": "success"
            })

            return roles

        except Exception as e:
            raise self._convert_exception(e)

    async def batch_create_permissions(self, permissions_data: List[Dict[str, Any]]) -> List[Permission]:
        """
        批量创建权限

        Args:
            permissions_data (List[Dict]): 权限数据列表
                每个字典包含: name, code, resource_type, action_type, description(可选)

        Returns:
            List[Permission]: 创建的权限列表

        Raises:
            DataValidationError: 数据验证失败
            BusinessLogicError: 业务逻辑错误
        """
        try:
            with self.transaction():
                created_permissions = []
                failed_permissions = []

                for i, perm_data in enumerate(permissions_data):
                    try:
                        # 验证必需字段
                        required_fields = ['name', 'code', 'resource_type', 'action_type']
                        for field in required_fields:
                            if field not in perm_data:
                                raise DataValidationError(f"第{i+1}个权限缺少必需字段: {field}")

                        # 创建权限
                        permission = await self.create_permission(
                            name=perm_data['name'],
                            code=perm_data['code'],
                            resource_type=perm_data['resource_type'],
                            action_type=perm_data['action_type'],
                            description=perm_data.get('description')
                        )
                        created_permissions.append(permission)

                    except Exception as e:
                        failed_permissions.append({
                            'index': i,
                            'data': perm_data,
                            'error': str(e)
                        })
                        self.logger.warning(f"批量创建权限跳过第{i+1}个: {str(e)}")

                # 记录操作日志
                self.log_operation("batch_create_permissions", {
                    "total_count": len(permissions_data),
                    "success_count": len(created_permissions),
                    "failed_count": len(failed_permissions),
                    "status": "success"
                })

                self.logger.info(f"批量创建权限完成: 总数={len(permissions_data)}, 成功={len(created_permissions)}, 失败={len(failed_permissions)}")
                return created_permissions

        except Exception as e:
            self.logger.error(f"批量创建权限失败: {str(e)}")
            raise self._convert_exception(e)

    # ==================== 辅助方法 ====================

    async def get_permission_by_code(self, permission_code: str) -> Optional[Permission]:
        """
        根据权限代码获取权限

        Args:
            permission_code (str): 权限代码

        Returns:
            Optional[Permission]: 权限对象，不存在返回None
        """
        try:
            if not permission_code:
                raise DataValidationError("权限代码不能为空")

            return self.permission_dao.find_by_permission_code(permission_code.strip().lower())

        except Exception as e:
            raise self._convert_exception(e)

    async def get_all_resource_types(self) -> List[str]:
        """
        获取所有资源类型

        Returns:
            List[str]: 资源类型列表
        """
        try:
            resource_types = self.permission_dao.get_resource_types()
            return sorted(resource_types)

        except Exception as e:
            raise self._convert_exception(e)

    async def get_all_action_types(self) -> List[str]:
        """
        获取所有操作类型

        Returns:
            List[str]: 操作类型列表
        """
        try:
            action_types = self.permission_dao.get_action_types()
            return sorted(action_types, key=self._get_action_priority)

        except Exception as e:
            raise self._convert_exception(e)

    async def search_permissions(self, keyword: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Permission]:
        """
        搜索权限

        Args:
            keyword (str): 搜索关键词
            limit (int, optional): 限制返回数量
            offset (int, optional): 偏移量

        Returns:
            List[Permission]: 匹配的权限列表
        """
        try:
            if not keyword:
                raise DataValidationError("搜索关键词不能为空")

            if limit and limit <= 0:
                raise DataValidationError("限制数量必须大于0")

            if offset and offset < 0:
                raise DataValidationError("偏移量不能为负数")

            # 使用PermissionDao的搜索方法
            permissions = self.permission_dao.search_permissions(keyword.strip(), limit)

            # 如果有偏移量，手动处理（PermissionDao的search_permissions不支持offset）
            if offset:
                permissions = permissions[offset:]

            self.log_operation("search_permissions", {
                "keyword": keyword,
                "limit": limit,
                "offset": offset,
                "result_count": len(permissions),
                "status": "success"
            })

            return permissions

        except Exception as e:
            raise self._convert_exception(e)

    async def get_permission_statistics(self) -> Dict[str, Any]:
        """
        获取权限统计信息

        Returns:
            Dict[str, Any]: 权限统计信息
        """
        try:
            # 获取基础统计
            total_permissions = self.count_all()

            # 获取资源类型统计
            grouped_permissions = self.permission_dao.get_permissions_by_resource()
            resource_stats = {}
            for resource_type, permissions in grouped_permissions.items():
                resource_stats[resource_type] = {
                    'permission_count': len(permissions),
                    'actions': list(set(p.action_type for p in permissions))
                }

            # 获取操作类型统计
            action_types = self.permission_dao.get_action_types()
            action_stats = {}
            for action_type in action_types:
                permissions = self.permission_dao.find_by_action_type(action_type)
                action_stats[action_type] = {
                    'permission_count': len(permissions),
                    'resources': list(set(p.resource_type for p in permissions))
                }

            stats = {
                'total_permissions': total_permissions,
                'resource_count': len(grouped_permissions),
                'action_count': len(action_types),
                'resource_stats': resource_stats,
                'action_stats': action_stats,
                'timestamp': datetime.now().isoformat()
            }

            # 记录操作日志
            self.log_operation("get_permission_statistics", {
                "stats": {
                    "total_permissions": total_permissions,
                    "resource_count": len(grouped_permissions),
                    "action_count": len(action_types)
                },
                "status": "success"
            })

            return stats

        except Exception as e:
            raise self._convert_exception(e)

    # ==================== 私有验证方法 ====================

    async def _validate_permission_data(self, name: str, code: str, resource_type: str, action_type: str):
        """验证权限数据"""
        if not name or not isinstance(name, str) or len(name.strip()) < 2:
            raise DataValidationError("权限名称长度必须在2-64字符之间")

        if len(name.strip()) > 64:
            raise DataValidationError("权限名称长度必须在2-64字符之间")

        if not code or not isinstance(code, str):
            raise DataValidationError("权限代码不能为空")

        if not resource_type or not isinstance(resource_type, str):
            raise DataValidationError("资源类型不能为空")

        if not action_type or not isinstance(action_type, str):
            raise DataValidationError("操作类型不能为空")

    async def _check_permission_code_uniqueness(self, permission_code: str, exclude_id: Optional[int] = None):
        """检查权限代码唯一性"""
        existing_permission = self.permission_dao.find_by_permission_code(permission_code.strip().lower())

        if existing_permission and (exclude_id is None or existing_permission.id != exclude_id):
            raise DuplicateResourceError("Permission", "permission_code", permission_code)

    def _validate_permission_code_format(self, code: str, resource_type: str, action_type: str):
        """验证权限代码格式"""
        # 权限代码应该是 resource:action 格式
        expected_code = f"{resource_type.strip().lower()}:{action_type.strip().lower()}"
        actual_code = code.strip().lower()

        if actual_code != expected_code:
            raise DataValidationError(f"权限代码格式错误，期望: {expected_code}，实际: {actual_code}")

        # 验证权限代码格式
        if not re.match(r'^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$', actual_code):
            raise DataValidationError("权限代码格式错误，应为 resource:action 格式，只能包含小写字母、数字、下划线")

    def _is_valid_permission_code(self, permission_code: str) -> bool:
        """检查权限代码格式是否有效"""
        if not permission_code or not isinstance(permission_code, str):
            return False

        return bool(re.match(r'^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$', permission_code.strip().lower()))

    async def _check_permission_dependencies(self, permission_id: int):
        """检查权限依赖关系"""
        # 检查是否有角色使用此权限
        roles = self.permission_dao.get_permission_roles(permission_id)
        if roles:
            role_names = [role.role_name for role in roles[:3]]  # 只显示前3个
            more_text = f" 等{len(roles)}个角色" if len(roles) > 3 else ""
            raise BusinessLogicError(f"权限被以下角色使用，无法删除: {', '.join(role_names)}{more_text}")

    async def _handle_permission_cascade_deletion(self, permission_id: int):
        """处理权限级联删除"""
        # 删除所有角色权限关联
        role_permissions = self.role_permission_dao.find_by_permission_id(permission_id)
        for rp in role_permissions:
            self.role_permission_dao.delete_by_id(rp.id)

        self.logger.info(f"权限级联删除: 删除了{len(role_permissions)}个角色权限关联")

    async def _check_admin_permission(self, user_id: int) -> bool:
        """检查用户是否具有管理员权限"""
        # 获取用户角色
        user_roles = self.user_role_dao.find_by_user_id(user_id, active_only=True)

        for user_role in user_roles:
            role = self.role_dao.find_by_id(user_role.role_id)
            if role and role.role_code == 'admin':
                return True

            # 检查角色是否有 admin:* 权限
            role_permissions = self.role_dao.get_role_permissions(role.id)
            for permission in role_permissions:
                if permission.permission_code.startswith('admin:'):
                    return True

        return False

    async def _check_direct_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户直接权限"""
        # 获取用户角色
        user_roles = self.user_role_dao.find_by_user_id(user_id, active_only=True)

        for user_role in user_roles:
            # 获取角色权限
            role_permissions = self.role_dao.get_role_permissions(user_role.role_id)
            for permission in role_permissions:
                if permission.permission_code == permission_code.lower():
                    return True

        return False

    async def _check_inherited_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户继承权限"""
        # 解析权限代码
        parts = permission_code.lower().split(':')
        if len(parts) != 2:
            return False

        resource_type, action_type = parts

        # 获取用户角色
        user_roles = self.user_role_dao.find_by_user_id(user_id, active_only=True)

        for user_role in user_roles:
            # 获取角色权限
            role_permissions = self.role_dao.get_role_permissions(user_role.role_id)
            for permission in role_permissions:
                perm_parts = permission.permission_code.split(':')
                if len(perm_parts) == 2:
                    perm_resource, perm_action = perm_parts

                    # 检查通配符权限
                    if perm_resource == resource_type and perm_action == '*':
                        return True
                    if perm_resource == '*' and perm_action == action_type:
                        return True
                    if perm_resource == '*' and perm_action == '*':
                        return True

        return False

    def _cache_permission_result(self, cache_key: str, has_permission: bool, ttl_minutes: int = 15):
        """缓存权限检查结果"""
        from datetime import timedelta

        self._permission_cache[cache_key] = {
            'has_permission': has_permission,
            'expires': datetime.now() + timedelta(minutes=ttl_minutes)
        }

    def _clear_permission_cache(self):
        """清除权限缓存"""
        self._permission_cache.clear()
        self.logger.debug("权限缓存已清除")

    def _get_resource_display_name(self, resource_type: str) -> str:
        """获取资源类型显示名称"""
        display_names = {
            'user': '用户管理',
            'role': '角色管理',
            'permission': '权限管理',
            'system': '系统管理',
            'report': '报表管理',
            'audit': '审计管理'
        }
        return display_names.get(resource_type, resource_type.title())

    def _get_action_priority(self, action_type: str) -> int:
        """获取操作类型优先级（用于排序）"""
        priorities = {
            'view': 1, 'list': 2, 'read': 3,
            'create': 4, 'add': 5,
            'edit': 6, 'update': 7, 'modify': 8,
            'delete': 9, 'remove': 10,
            'export': 11, 'import': 12,
            'approve': 13, 'audit': 14
        }
        return priorities.get(action_type, 999)
