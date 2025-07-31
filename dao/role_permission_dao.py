"""
RBAC系统角色权限关联DAO模块

本模块定义了角色权限关联数据访问对象，提供角色权限关系管理的数据库操作接口。

Classes:
    RolePermissionDao: 角色权限关联DAO类

Author: AI Assistant
Created: 2025-07-19
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from models.role_permission import RolePermission
from models.role import Role
from models.permission import Permission
from models.user import User
from .base_dao import BaseDao, DatabaseError, NotFoundError, ValidationError


class RolePermissionDao(BaseDao[RolePermission]):
    """
    角色权限关联数据访问对象
    
    提供角色权限关系管理的数据库操作接口，包括权限授权、撤销、批量操作等。
    
    Methods:
        角色权限关系管理:
            grant_permission: 授予权限给角色
            revoke_permission: 撤销角色权限
            regrant_permission: 重新授权
        
        查询方法:
            find_by_role_id: 查询角色的所有权限关联
            find_by_permission_id: 查询权限的所有角色关联
            find_active_grants: 查询所有启用的关联
            find_by_granted_by: 查询某人授权的所有关联
        
        批量操作:
            batch_grant_permissions: 批量授予权限
            batch_revoke_permissions: 批量撤销权限
            batch_grant_roles: 批量授权角色
        
        状态管理:
            activate_grant: 启用关联
            deactivate_grant: 禁用关联
    """
    
    def _get_model_class(self) -> type:
        """获取模型类"""
        return RolePermission
    
    def grant_permission(self, role_id: int, permission_id: int, granted_by: Optional[int] = None) -> RolePermission:
        """
        授予权限给角色
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            granted_by (int, optional): 授权人ID
            
        Returns:
            RolePermission: 创建的角色权限关联对象
            
        Raises:
            ValueError: 参数无效
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            if granted_by is not None and granted_by <= 0:
                raise ValueError("授权人ID必须是正整数")
            
            # 检查角色和权限是否存在
            role = self.session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ValidationError(f"角色不存在: role_id={role_id}")
            
            permission = self.session.query(Permission).filter(Permission.id == permission_id).first()
            if not permission:
                raise ValidationError(f"权限不存在: permission_id={permission_id}")
            
            # 检查是否已经存在关联
            existing = self.session.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            ).first()
            
            if existing:
                if existing.status == 1:
                    raise ValidationError(f"角色已经拥有该权限: role_id={role_id}, permission_id={permission_id}")
                else:
                    # 重新启用已存在的关联
                    existing.activate()
                    existing.granted_by = granted_by
                    existing.granted_at = datetime.utcnow()
                    self.session.flush()
                    self.logger.info(f"重新启用角色权限关联: role_id={role_id}, permission_id={permission_id}")
                    return existing
            
            # 创建新的关联
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                granted_by=granted_by,
                granted_at=datetime.utcnow(),
                status=1
            )
            
            self.session.add(role_permission)
            self.session.flush()
            
            self.logger.info(f"授予权限成功: role_id={role_id}, permission_id={permission_id}, granted_by={granted_by}")
            return role_permission
            
        except (ValueError, ValidationError):
            raise
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"授予权限数据完整性错误: {str(e)}")
            raise DatabaseError(f"数据完整性错误: {str(e)}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"授予权限失败: role_id={role_id}, permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def revoke_permission(self, role_id: int, permission_id: int) -> bool:
        """
        撤销角色权限
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            
        Returns:
            bool: 撤销成功返回True，关联不存在返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            
            role_permission = self.session.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                    RolePermission.status == 1
                )
            ).first()
            
            if not role_permission:
                return False
            
            role_permission.deactivate()
            self.session.flush()
            
            self.logger.info(f"撤销权限成功: role_id={role_id}, permission_id={permission_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"撤销权限失败: role_id={role_id}, permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def regrant_permission(self, role_id: int, old_permission_id: int, new_permission_id: int, granted_by: Optional[int] = None) -> RolePermission:
        """
        重新授权
        
        Args:
            role_id (int): 角色ID
            old_permission_id (int): 旧权限ID
            new_permission_id (int): 新权限ID
            granted_by (int, optional): 授权人ID
            
        Returns:
            RolePermission: 新的角色权限关联对象
            
        Raises:
            ValueError: 参数无效
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not old_permission_id or old_permission_id <= 0:
                raise ValueError("旧权限ID必须是正整数")
            if not new_permission_id or new_permission_id <= 0:
                raise ValueError("新权限ID必须是正整数")
            
            # 撤销旧权限
            revoked = self.revoke_permission(role_id, old_permission_id)
            if not revoked:
                raise ValidationError(f"角色没有旧权限: role_id={role_id}, old_permission_id={old_permission_id}")
            
            # 授予新权限
            new_role_permission = self.grant_permission(role_id, new_permission_id, granted_by)
            
            self.logger.info(f"重新授权成功: role_id={role_id}, old_permission_id={old_permission_id}, new_permission_id={new_permission_id}")
            return new_role_permission
            
        except (ValueError, ValidationError, DatabaseError):
            raise
    
    def find_by_role_id(self, role_id: int, active_only: bool = True) -> List[RolePermission]:
        """
        查询角色的所有权限关联
        
        Args:
            role_id (int): 角色ID
            active_only (bool): 是否只查询启用的关联
            
        Returns:
            List[RolePermission]: 角色的权限关联列表
            
        Raises:
            ValueError: 角色ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            query = self.session.query(RolePermission).filter(RolePermission.role_id == role_id)
            
            if active_only:
                query = query.filter(RolePermission.status == 1)
            
            role_permissions = query.order_by(RolePermission.granted_at.desc()).all()
            return role_permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询角色权限关联失败: role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e

    def find_by_role_permission(self, role_id: int, permission_id: int) -> Optional[RolePermission]:
        """
        查询特定角色和权限的关联

        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID

        Returns:
            Optional[RolePermission]: 找到的关联对象，如果不存在则返回None

        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")

            role_permission = self.session.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            ).first()

            return role_permission

        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询角色权限关联失败: role_id={role_id}, permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e

    def find_by_permission_id(self, permission_id: int, active_only: bool = True) -> List[RolePermission]:
        """
        查询权限的所有角色关联
        
        Args:
            permission_id (int): 权限ID
            active_only (bool): 是否只查询启用的关联
            
        Returns:
            List[RolePermission]: 权限的角色关联列表
            
        Raises:
            ValueError: 权限ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            
            query = self.session.query(RolePermission).filter(RolePermission.permission_id == permission_id)
            
            if active_only:
                query = query.filter(RolePermission.status == 1)
            
            role_permissions = query.order_by(RolePermission.granted_at.desc()).all()
            return role_permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询权限角色关联失败: permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_active_grants(self) -> List[RolePermission]:
        """
        查询所有启用的关联
        
        Returns:
            List[RolePermission]: 启用的角色权限关联列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            role_permissions = self.session.query(RolePermission).filter(
                RolePermission.status == 1
            ).order_by(RolePermission.granted_at.desc()).all()
            
            return role_permissions
            
        except SQLAlchemyError as e:
            self.logger.error(f"查询启用关联失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_granted_by(self, granted_by: int) -> List[RolePermission]:
        """
        查询某人授权的所有关联
        
        Args:
            granted_by (int): 授权人ID
            
        Returns:
            List[RolePermission]: 该授权人的关联列表
            
        Raises:
            ValueError: 授权人ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not granted_by or granted_by <= 0:
                raise ValueError("授权人ID必须是正整数")
            
            role_permissions = self.session.query(RolePermission).filter(
                RolePermission.granted_by == granted_by
            ).order_by(RolePermission.granted_at.desc()).all()
            
            return role_permissions
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询授权人关联失败: granted_by={granted_by}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def batch_grant_permissions(self, role_id: int, permission_ids: List[int], granted_by: Optional[int] = None) -> List[RolePermission]:
        """
        批量授予权限
        
        Args:
            role_id (int): 角色ID
            permission_ids (List[int]): 权限ID列表
            granted_by (int, optional): 授权人ID
            
        Returns:
            List[RolePermission]: 创建的角色权限关联列表
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_ids:
                return []
            
            role_permissions = []
            for permission_id in permission_ids:
                try:
                    role_permission = self.grant_permission(role_id, permission_id, granted_by)
                    role_permissions.append(role_permission)
                except ValidationError as e:
                    self.logger.warning(f"批量授予权限跳过: role_id={role_id}, permission_id={permission_id}, error={str(e)}")
                    continue
            
            self.logger.info(f"批量授予权限成功: role_id={role_id}, 成功授予{len(role_permissions)}个权限")
            return role_permissions
            
        except ValueError:
            raise
        except DatabaseError:
            raise
    
    def batch_revoke_permissions(self, role_id: int, permission_ids: List[int]) -> int:
        """
        批量撤销权限
        
        Args:
            role_id (int): 角色ID
            permission_ids (List[int]): 权限ID列表
            
        Returns:
            int: 实际撤销的权限数量
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_ids:
                return 0
            
            revoked_count = 0
            for permission_id in permission_ids:
                if self.revoke_permission(role_id, permission_id):
                    revoked_count += 1
            
            self.logger.info(f"批量撤销权限成功: role_id={role_id}, 撤销{revoked_count}个权限")
            return revoked_count
            
        except ValueError:
            raise
        except DatabaseError:
            raise
    
    def batch_grant_roles(self, permission_id: int, role_ids: List[int], granted_by: Optional[int] = None) -> List[RolePermission]:
        """
        批量授权角色
        
        Args:
            permission_id (int): 权限ID
            role_ids (List[int]): 角色ID列表
            granted_by (int, optional): 授权人ID
            
        Returns:
            List[RolePermission]: 创建的角色权限关联列表
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            if not role_ids:
                return []
            
            role_permissions = []
            for role_id in role_ids:
                try:
                    role_permission = self.grant_permission(role_id, permission_id, granted_by)
                    role_permissions.append(role_permission)
                except ValidationError as e:
                    self.logger.warning(f"批量授权角色跳过: role_id={role_id}, permission_id={permission_id}, error={str(e)}")
                    continue
            
            self.logger.info(f"批量授权角色成功: permission_id={permission_id}, 成功授权{len(role_permissions)}个角色")
            return role_permissions
            
        except ValueError:
            raise
        except DatabaseError:
            raise
    
    def activate_grant(self, role_id: int, permission_id: int) -> bool:
        """
        启用关联
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            
        Returns:
            bool: 操作成功返回True，关联不存在返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            
            role_permission = self.session.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            ).first()
            
            if not role_permission:
                return False
            
            role_permission.activate()
            self.session.flush()
            
            self.logger.info(f"启用角色权限关联成功: role_id={role_id}, permission_id={permission_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"启用关联失败: role_id={role_id}, permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def deactivate_grant(self, role_id: int, permission_id: int) -> bool:
        """
        禁用关联
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            
        Returns:
            bool: 操作成功返回True，关联不存在返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not permission_id or permission_id <= 0:
                raise ValueError("权限ID必须是正整数")
            
            role_permission = self.session.query(RolePermission).filter(
                and_(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                )
            ).first()
            
            if not role_permission:
                return False
            
            role_permission.deactivate()
            self.session.flush()
            
            self.logger.info(f"禁用角色权限关联成功: role_id={role_id}, permission_id={permission_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"禁用关联失败: role_id={role_id}, permission_id={permission_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
