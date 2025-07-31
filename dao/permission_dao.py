"""
RBAC系统权限DAO模块

本模块定义了权限数据访问对象，提供权限相关的数据库操作接口。

Classes:
    PermissionDao: 权限DAO类

Author: AI Assistant
Created: 2025-07-19
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from sqlalchemy import and_, or_, func, distinct
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from models.permission import Permission
from models.role_permission import RolePermission
from models.role import Role
from models.user_role import UserRole
from models.user import User
from .base_dao import BaseDao, DatabaseError, NotFoundError


class PermissionDao(BaseDao[Permission]):
    """
    权限数据访问对象
    
    提供权限相关的数据库操作接口，包括基础CRUD操作和权限特有的查询方法。
    
    Methods:
        基础CRUD操作（继承自BaseDao）:
            create, find_by_id, find_all, update, delete_by_id
            batch_create, batch_update, batch_delete
        
        权限特有查询方法:
            find_by_permission_code: 根据权限代码查询
            find_by_resource_type: 根据资源类型查询
            find_by_action_type: 根据操作类型查询
            find_by_resource_action: 根据资源和操作查询
            search_permissions: 权限搜索
        
        权限关系相关方法:
            get_permission_roles: 获取拥有该权限的所有角色
            get_permission_users: 获取拥有该权限的所有用户
        
        权限分组方法:
            get_permissions_by_resource: 按资源类型分组获取权限
            get_resource_types: 获取所有资源类型
            get_action_types: 获取所有操作类型
    """
    
    def _get_model_class(self) -> type:
        """获取模型类"""
        return Permission
    
    def find_by_permission_code(self, permission_code: str) -> Optional[Permission]:
        """
        根据权限代码查询权限
        
        Args:
            permission_code (str): 权限代码
            
        Returns:
            Optional[Permission]: 找到的权限对象，如果不存在则返回None
            
        Raises:
            ValueError: 权限代码参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not permission_code or not isinstance(permission_code, str):
                raise ValueError("权限代码不能为空")
            
            permission = self.session.query(Permission).filter(
                Permission.permission_code == permission_code.strip()
            ).first()
            
            return permission
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据权限代码查询权限失败: permission_code={permission_code}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_resource_type(self, resource_type: str) -> List[Permission]:
        """
        根据资源类型查询权限
        
        Args:
            resource_type (str): 资源类型
            
        Returns:
            List[Permission]: 该资源类型的权限列表
            
        Raises:
            ValueError: 资源类型参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not resource_type or not isinstance(resource_type, str):
                raise ValueError("资源类型不能为空")
            
            permissions = self.session.query(Permission).filter(
                Permission.resource_type == resource_type.strip()
            ).order_by(Permission.action_type).all()
            
            return permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据资源类型查询权限失败: resource_type={resource_type}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_action_type(self, action_type: str) -> List[Permission]:
        """
        根据操作类型查询权限
        
        Args:
            action_type (str): 操作类型
            
        Returns:
            List[Permission]: 该操作类型的权限列表
            
        Raises:
            ValueError: 操作类型参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not action_type or not isinstance(action_type, str):
                raise ValueError("操作类型不能为空")
            
            permissions = self.session.query(Permission).filter(
                Permission.action_type == action_type.strip()
            ).order_by(Permission.resource_type).all()
            
            return permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据操作类型查询权限失败: action_type={action_type}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_resource_action(self, resource_type: str, action_type: str) -> Optional[Permission]:
        """
        根据资源类型和操作类型查询权限
        
        Args:
            resource_type (str): 资源类型
            action_type (str): 操作类型
            
        Returns:
            Optional[Permission]: 找到的权限对象，如果不存在则返回None
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not resource_type or not isinstance(resource_type, str):
                raise ValueError("资源类型不能为空")
            if not action_type or not isinstance(action_type, str):
                raise ValueError("操作类型不能为空")
            
            permission = self.session.query(Permission).filter(
                and_(
                    Permission.resource_type == resource_type.strip(),
                    Permission.action_type == action_type.strip()
                )
            ).first()
            
            return permission
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据资源和操作类型查询权限失败: resource_type={resource_type}, action_type={action_type}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def search_permissions(self, keyword: str, limit: Optional[int] = None) -> List[Permission]:
        """
        权限搜索（权限名称或权限代码）
        
        Args:
            keyword (str): 搜索关键词
            limit (int, optional): 限制返回记录数
            
        Returns:
            List[Permission]: 匹配的权限列表
            
        Raises:
            ValueError: 关键词参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not keyword or not isinstance(keyword, str):
                raise ValueError("搜索关键词不能为空")
            
            keyword = f"%{keyword.strip()}%"
            query = self.session.query(Permission).filter(
                or_(
                    Permission.permission_name.like(keyword),
                    Permission.permission_code.like(keyword),
                    Permission.resource_type.like(keyword),
                    Permission.action_type.like(keyword)
                )
            ).order_by(Permission.resource_type, Permission.action_type)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"搜索权限失败: keyword={keyword}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_permission_roles(self, permission_id: int) -> List[Role]:
        """
        获取拥有该权限的所有角色
        
        Args:
            permission_id (int): 权限ID
            
        Returns:
            List[Role]: 拥有该权限的角色列表
            
        Raises:
            ValueError: 权限ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            
            roles = self.session.query(Role).join(RolePermission).filter(
                and_(
                    RolePermission.permission_id == permission_id,
                    RolePermission.status == 1,
                    Role.status == 1
                )
            ).order_by(Role.role_name).all()
            
            return roles
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取权限角色失败: permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_permission_users(self, permission_id: int) -> List[User]:
        """
        获取拥有该权限的所有用户（通过角色）
        
        Args:
            permission_id (int): 权限ID
            
        Returns:
            List[User]: 拥有该权限的用户列表
            
        Raises:
            ValueError: 权限ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            
            users = self.session.query(User).join(UserRole).join(Role).join(RolePermission).filter(
                and_(
                    RolePermission.permission_id == permission_id,
                    RolePermission.status == 1,
                    Role.status == 1,
                    UserRole.status == 1,
                    User.status == 1
                )
            ).distinct().order_by(User.username).all()
            
            return users
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取权限用户失败: permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_permissions_by_resource(self) -> Dict[str, List[Permission]]:
        """
        按资源类型分组获取权限
        
        Returns:
            Dict[str, List[Permission]]: 按资源类型分组的权限字典
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            permissions = self.session.query(Permission).order_by(
                Permission.resource_type, Permission.action_type
            ).all()
            
            grouped_permissions = {}
            for permission in permissions:
                resource_type = permission.resource_type
                if resource_type not in grouped_permissions:
                    grouped_permissions[resource_type] = []
                grouped_permissions[resource_type].append(permission)
            
            return grouped_permissions
            
        except SQLAlchemyError as e:
            self.logger.error(f"按资源类型分组获取权限失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_resource_types(self) -> List[str]:
        """
        获取所有资源类型
        
        Returns:
            List[str]: 资源类型列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            resource_types = self.session.query(
                distinct(Permission.resource_type)
            ).order_by(Permission.resource_type).all()
            
            return [rt[0] for rt in resource_types]
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取资源类型失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_action_types(self) -> List[str]:
        """
        获取所有操作类型
        
        Returns:
            List[str]: 操作类型列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            action_types = self.session.query(
                distinct(Permission.action_type)
            ).order_by(Permission.action_type).all()
            
            return [at[0] for at in action_types]
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取操作类型失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_permission_statistics(self, permission_id: int) -> Dict[str, Any]:
        """
        获取权限统计信息
        
        Args:
            permission_id (int): 权限ID
            
        Returns:
            Dict[str, Any]: 权限统计信息
            
        Raises:
            ValueError: 权限ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            
            permission = self.find_by_id(permission_id)
            if not permission:
                raise NotFoundError(f"权限不存在: permission_id={permission_id}")
            
            # 统计角色数量
            role_count = self.session.query(RolePermission).filter(
                and_(
                    RolePermission.permission_id == permission_id,
                    RolePermission.status == 1
                )
            ).count()
            
            # 统计用户数量（通过角色）
            user_count = self.session.query(User).join(UserRole).join(Role).join(RolePermission).filter(
                and_(
                    RolePermission.permission_id == permission_id,
                    RolePermission.status == 1,
                    Role.status == 1,
                    UserRole.status == 1,
                    User.status == 1
                )
            ).distinct().count()
            
            return {
                'permission_id': permission_id,
                'permission_name': permission.permission_name,
                'permission_code': permission.permission_code,
                'resource_type': permission.resource_type,
                'action_type': permission.action_type,
                'role_count': role_count,
                'user_count': user_count,
                'is_system_permission': permission.is_system_permission(),
                'is_read_permission': permission.is_read_permission(),
                'is_write_permission': permission.is_write_permission(),
                'created_at': permission.created_at.isoformat() if permission.created_at else None
            }
            
        except (ValueError, NotFoundError):
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取权限统计信息失败: permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_system_permissions(self) -> List[Permission]:
        """
        查找所有系统级权限
        
        Returns:
            List[Permission]: 系统级权限列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            permissions = self.session.query(Permission).filter(
                Permission.resource_type == 'system'
            ).order_by(Permission.action_type).all()
            
            return permissions
            
        except SQLAlchemyError as e:
            self.logger.error(f"查找系统权限失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_read_permissions(self) -> List[Permission]:
        """
        查找所有只读权限
        
        Returns:
            List[Permission]: 只读权限列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            permissions = self.session.query(Permission).filter(
                Permission.action_type.in_(['view', 'list', 'read'])
            ).order_by(Permission.resource_type, Permission.action_type).all()
            
            return permissions
            
        except SQLAlchemyError as e:
            self.logger.error(f"查找只读权限失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_write_permissions(self) -> List[Permission]:
        """
        查找所有写权限
        
        Returns:
            List[Permission]: 写权限列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            permissions = self.session.query(Permission).filter(
                Permission.action_type.in_(['create', 'edit', 'update', 'delete', 'write'])
            ).order_by(Permission.resource_type, Permission.action_type).all()
            
            return permissions
            
        except SQLAlchemyError as e:
            self.logger.error(f"查找写权限失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
