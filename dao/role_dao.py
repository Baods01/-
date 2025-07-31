"""
RBAC系统角色DAO模块

本模块定义了角色数据访问对象，提供角色相关的数据库操作接口。

Classes:
    RoleDao: 角色DAO类

Author: AI Assistant
Created: 2025-07-19
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from models.role import Role
from models.user_role import UserRole
from models.user import User
from models.role_permission import RolePermission
from models.permission import Permission
from .base_dao import BaseDao, DatabaseError, NotFoundError


class RoleDao(BaseDao[Role]):
    """
    角色数据访问对象
    
    提供角色相关的数据库操作接口，包括基础CRUD操作和角色特有的查询方法。
    
    Methods:
        基础CRUD操作（继承自BaseDao）:
            create, find_by_id, find_all, update, delete_by_id
            batch_create, batch_update, batch_delete
        
        角色特有查询方法:
            find_by_role_code: 根据角色代码查询
            find_active_roles: 查询所有启用角色
            find_by_status: 根据状态查询
            search_roles: 角色搜索
        
        角色权限相关方法:
            get_role_permissions: 获取角色的所有权限
            has_permission: 检查角色是否具有特定权限
            get_role_users: 获取拥有该角色的所有用户
        
        角色管理方法:
            activate_role: 启用角色
            deactivate_role: 禁用角色
    """
    
    def _get_model_class(self) -> type:
        """获取模型类"""
        return Role
    
    def find_by_role_code(self, role_code: str) -> Optional[Role]:
        """
        根据角色代码查询角色
        
        Args:
            role_code (str): 角色代码
            
        Returns:
            Optional[Role]: 找到的角色对象，如果不存在则返回None
            
        Raises:
            ValueError: 角色代码参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_code or not isinstance(role_code, str):
                raise ValueError("角色代码不能为空")
            
            role = self.session.query(Role).filter(
                Role.role_code == role_code.strip()
            ).first()
            
            return role
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据角色代码查询角色失败: role_code={role_code}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e

    def find_by_name(self, role_name: str) -> Optional[Role]:
        """
        根据角色名称查询角色

        Args:
            role_name (str): 角色名称

        Returns:
            Optional[Role]: 找到的角色对象，如果不存在则返回None

        Raises:
            ValueError: 角色名称参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_name or not isinstance(role_name, str):
                raise ValueError("角色名称不能为空")

            role = self.session.query(Role).filter(
                Role.role_name == role_name.strip()
            ).first()

            return role

        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据角色名称查询角色失败: role_name={role_name}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e

    def find_active_roles(self) -> List[Role]:
        """
        查询所有启用角色
        
        Returns:
            List[Role]: 启用的角色列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            roles = self.session.query(Role).filter(
                Role.status == 1
            ).order_by(Role.role_name).all()
            
            return roles
            
        except SQLAlchemyError as e:
            self.logger.error(f"查询启用角色失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_status(self, status: int) -> List[Role]:
        """
        根据状态查询角色
        
        Args:
            status (int): 角色状态，1=启用，0=禁用
            
        Returns:
            List[Role]: 指定状态的角色列表
            
        Raises:
            ValueError: 状态参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if status not in [0, 1]:
                raise ValueError("角色状态只能是0（禁用）或1（启用）")
            
            roles = self.session.query(Role).filter(
                Role.status == status
            ).order_by(Role.role_name).all()
            
            return roles
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据状态查询角色失败: status={status}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def search_roles(self, keyword: str, limit: Optional[int] = None) -> List[Role]:
        """
        角色搜索（角色名称或角色代码）
        
        Args:
            keyword (str): 搜索关键词
            limit (int, optional): 限制返回记录数
            
        Returns:
            List[Role]: 匹配的角色列表
            
        Raises:
            ValueError: 关键词参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not keyword or not isinstance(keyword, str):
                raise ValueError("搜索关键词不能为空")
            
            keyword = f"%{keyword.strip()}%"
            query = self.session.query(Role).filter(
                or_(
                    Role.role_name.like(keyword),
                    Role.role_code.like(keyword)
                )
            ).order_by(Role.role_name)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"搜索角色失败: keyword={keyword}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """
        获取角色的所有权限
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            List[Permission]: 角色拥有的权限列表
            
        Raises:
            ValueError: 角色ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            permissions = self.session.query(Permission).join(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.status == 1
                )
            ).order_by(Permission.resource_type, Permission.action_type).all()
            
            return permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取角色权限失败: role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def has_permission(self, role_id: int, permission_code: str) -> bool:
        """
        检查角色是否具有特定权限
        
        Args:
            role_id (int): 角色ID
            permission_code (str): 权限代码
            
        Returns:
            bool: 如果角色具有该权限返回True，否则返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_code:
                raise ValueError("权限代码不能为空")
            
            count = self.session.query(RolePermission).join(Permission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    Permission.permission_code == permission_code,
                    RolePermission.status == 1
                )
            ).count()
            
            return count > 0
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"检查角色权限失败: role_id={role_id}, permission_code={permission_code}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_role_users(self, role_id: int) -> List[User]:
        """
        获取拥有该角色的所有用户
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            List[User]: 拥有该角色的用户列表
            
        Raises:
            ValueError: 角色ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            users = self.session.query(User).join(UserRole).filter(
                and_(
                    UserRole.role_id == role_id,
                    UserRole.status == 1,
                    User.status == 1
                )
            ).order_by(User.username).all()
            
            return users
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取角色用户失败: role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def activate_role(self, role_id: int) -> bool:
        """
        启用角色
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            bool: 操作成功返回True，角色不存在返回False
            
        Raises:
            ValueError: 角色ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            role = self.find_by_id(role_id)
            if not role:
                return False
            
            role.activate()
            self.session.flush()
            
            self.logger.info(f"启用角色成功: role_id={role_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"启用角色失败: role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def deactivate_role(self, role_id: int) -> bool:
        """
        禁用角色
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            bool: 操作成功返回True，角色不存在返回False
            
        Raises:
            ValueError: 角色ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            role = self.find_by_id(role_id)
            if not role:
                return False
            
            role.deactivate()
            self.session.flush()
            
            self.logger.info(f"禁用角色成功: role_id={role_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"禁用角色失败: role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def get_role_statistics(self, role_id: int) -> Dict[str, Any]:
        """
        获取角色统计信息
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            Dict[str, Any]: 角色统计信息
            
        Raises:
            ValueError: 角色ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            role = self.find_by_id(role_id)
            if not role:
                raise NotFoundError(f"角色不存在: role_id={role_id}")
            
            # 统计用户数量
            user_count = self.session.query(UserRole).filter(
                and_(
                    UserRole.role_id == role_id,
                    UserRole.status == 1
                )
            ).count()
            
            # 统计权限数量
            permission_count = self.session.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.status == 1
                )
            ).count()
            
            return {
                'role_id': role_id,
                'role_name': role.role_name,
                'role_code': role.role_code,
                'status': role.status,
                'user_count': user_count,
                'permission_count': permission_count,
                'created_at': role.created_at.isoformat() if role.created_at else None,
                'updated_at': role.updated_at.isoformat() if role.updated_at else None
            }
            
        except (ValueError, NotFoundError):
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取角色统计信息失败: role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_roles_by_permission(self, permission_code: str) -> List[Role]:
        """
        根据权限代码查找拥有该权限的角色
        
        Args:
            permission_code (str): 权限代码
            
        Returns:
            List[Role]: 拥有该权限的角色列表
            
        Raises:
            ValueError: 权限代码参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not permission_code:
                raise ValueError("权限代码不能为空")
            
            roles = self.session.query(Role).join(RolePermission).join(Permission).filter(
                and_(
                    Permission.permission_code == permission_code,
                    RolePermission.status == 1,
                    Role.status == 1
                )
            ).order_by(Role.role_name).all()
            
            return roles
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"根据权限查找角色失败: permission_code={permission_code}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def get_permissions_by_resource(self, role_id: int, resource_type: str) -> List[Permission]:
        """
        获取角色在特定资源类型上的权限
        
        Args:
            role_id (int): 角色ID
            resource_type (str): 资源类型
            
        Returns:
            List[Permission]: 该资源类型的权限列表
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not resource_type:
                raise ValueError("资源类型不能为空")
            
            permissions = self.session.query(Permission).join(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    Permission.resource_type == resource_type,
                    RolePermission.status == 1
                )
            ).order_by(Permission.action_type).all()
            
            return permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取角色资源权限失败: role_id={role_id}, resource_type={resource_type}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
