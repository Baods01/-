"""
RBAC系统用户角色关联DAO模块

本模块定义了用户角色关联数据访问对象，提供用户角色关系管理的数据库操作接口。

Classes:
    UserRoleDao: 用户角色关联DAO类

Author: AI Assistant
Created: 2025-07-19
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from models.user_role import UserRole
from models.user import User
from models.role import Role
from .base_dao import BaseDao, DatabaseError, NotFoundError, ValidationError


class UserRoleDao(BaseDao[UserRole]):
    """
    用户角色关联数据访问对象
    
    提供用户角色关系管理的数据库操作接口，包括角色分配、撤销、批量操作等。
    
    Methods:
        用户角色关系管理:
            assign_role: 分配角色给用户
            revoke_role: 撤销用户角色
            reassign_role: 重新分配角色
        
        查询方法:
            find_by_user_id: 查询用户的所有角色关联
            find_by_role_id: 查询角色的所有用户关联
            find_active_assignments: 查询所有启用的关联
            find_by_assigned_by: 查询某人分配的所有关联
        
        批量操作:
            batch_assign_roles: 批量分配角色
            batch_revoke_roles: 批量撤销角色
            batch_assign_users: 批量分配用户
        
        状态管理:
            activate_assignment: 启用关联
            deactivate_assignment: 禁用关联
    """
    
    def _get_model_class(self) -> type:
        """获取模型类"""
        return UserRole
    
    def assign_role(self, user_id: int, role_id: int, assigned_by: Optional[int] = None) -> UserRole:
        """
        分配角色给用户
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            assigned_by (int, optional): 分配人ID
            
        Returns:
            UserRole: 创建的用户角色关联对象
            
        Raises:
            ValueError: 参数无效
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if assigned_by is not None and assigned_by <= 0:
                raise ValueError("分配人ID必须是正整数")
            
            # 检查用户和角色是否存在
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValidationError(f"用户不存在: user_id={user_id}")
            
            role = self.session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ValidationError(f"角色不存在: role_id={role_id}")
            
            # 检查是否已经存在关联
            existing = self.session.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            ).first()
            
            if existing:
                if existing.status == 1:
                    raise ValidationError(f"用户已经拥有该角色: user_id={user_id}, role_id={role_id}")
                else:
                    # 重新启用已存在的关联
                    existing.activate()
                    existing.assigned_by = assigned_by
                    existing.assigned_at = datetime.utcnow()
                    self.session.flush()
                    self.logger.info(f"重新启用用户角色关联: user_id={user_id}, role_id={role_id}")
                    return existing
            
            # 创建新的关联
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
                assigned_at=datetime.utcnow(),
                status=1
            )
            
            self.session.add(user_role)
            self.session.flush()
            
            self.logger.info(f"分配角色成功: user_id={user_id}, role_id={role_id}, assigned_by={assigned_by}")
            return user_role
            
        except (ValueError, ValidationError):
            raise
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"分配角色数据完整性错误: {str(e)}")
            raise DatabaseError(f"数据完整性错误: {str(e)}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"分配角色失败: user_id={user_id}, role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def revoke_role(self, user_id: int, role_id: int) -> bool:
        """
        撤销用户角色
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            bool: 撤销成功返回True，关联不存在返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            user_role = self.session.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                    UserRole.status == 1
                )
            ).first()
            
            if not user_role:
                return False
            
            user_role.deactivate()
            self.session.flush()
            
            self.logger.info(f"撤销角色成功: user_id={user_id}, role_id={role_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"撤销角色失败: user_id={user_id}, role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def reassign_role(self, user_id: int, old_role_id: int, new_role_id: int, assigned_by: Optional[int] = None) -> UserRole:
        """
        重新分配角色
        
        Args:
            user_id (int): 用户ID
            old_role_id (int): 旧角色ID
            new_role_id (int): 新角色ID
            assigned_by (int, optional): 分配人ID
            
        Returns:
            UserRole: 新的用户角色关联对象
            
        Raises:
            ValueError: 参数无效
            ValidationError: 数据验证失败
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not old_role_id or old_role_id <= 0:
                raise ValueError("旧角色ID必须是正整数")
            if not new_role_id or new_role_id <= 0:
                raise ValueError("新角色ID必须是正整数")
            
            # 撤销旧角色
            revoked = self.revoke_role(user_id, old_role_id)
            if not revoked:
                raise ValidationError(f"用户没有旧角色: user_id={user_id}, old_role_id={old_role_id}")
            
            # 分配新角色
            new_user_role = self.assign_role(user_id, new_role_id, assigned_by)
            
            self.logger.info(f"重新分配角色成功: user_id={user_id}, old_role_id={old_role_id}, new_role_id={new_role_id}")
            return new_user_role
            
        except (ValueError, ValidationError, DatabaseError):
            raise
    
    def find_by_user_id(self, user_id: int, active_only: bool = True) -> List[UserRole]:
        """
        查询用户的所有角色关联
        
        Args:
            user_id (int): 用户ID
            active_only (bool): 是否只查询启用的关联
            
        Returns:
            List[UserRole]: 用户的角色关联列表
            
        Raises:
            ValueError: 用户ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            
            query = self.session.query(UserRole).filter(UserRole.user_id == user_id)
            
            if active_only:
                query = query.filter(UserRole.status == 1)
            
            user_roles = query.order_by(UserRole.assigned_at.desc()).all()
            return user_roles
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询用户角色关联失败: user_id={user_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e

    def find_by_user_role(self, user_id: int, role_id: int) -> Optional[UserRole]:
        """
        查询特定用户和角色的关联

        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID

        Returns:
            Optional[UserRole]: 找到的关联对象，如果不存在则返回None

        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")

            user_role = self.session.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            ).first()

            return user_role

        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询用户角色关联失败: user_id={user_id}, role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e

    def find_by_role_id(self, role_id: int, active_only: bool = True) -> List[UserRole]:
        """
        查询角色的所有用户关联
        
        Args:
            role_id (int): 角色ID
            active_only (bool): 是否只查询启用的关联
            
        Returns:
            List[UserRole]: 角色的用户关联列表
            
        Raises:
            ValueError: 角色ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            query = self.session.query(UserRole).filter(UserRole.role_id == role_id)
            
            if active_only:
                query = query.filter(UserRole.status == 1)
            
            user_roles = query.order_by(UserRole.assigned_at.desc()).all()
            return user_roles
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询角色用户关联失败: role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_active_assignments(self) -> List[UserRole]:
        """
        查询所有启用的关联
        
        Returns:
            List[UserRole]: 启用的用户角色关联列表
            
        Raises:
            DatabaseError: 数据库操作失败
        """
        try:
            user_roles = self.session.query(UserRole).filter(
                UserRole.status == 1
            ).order_by(UserRole.assigned_at.desc()).all()
            
            return user_roles
            
        except SQLAlchemyError as e:
            self.logger.error(f"查询启用关联失败: {str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def find_by_assigned_by(self, assigned_by: int) -> List[UserRole]:
        """
        查询某人分配的所有关联
        
        Args:
            assigned_by (int): 分配人ID
            
        Returns:
            List[UserRole]: 该分配人的关联列表
            
        Raises:
            ValueError: 分配人ID参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not assigned_by or assigned_by <= 0:
                raise ValueError("分配人ID必须是正整数")
            
            user_roles = self.session.query(UserRole).filter(
                UserRole.assigned_by == assigned_by
            ).order_by(UserRole.assigned_at.desc()).all()
            
            return user_roles
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"查询分配人关联失败: assigned_by={assigned_by}, error={str(e)}")
            raise DatabaseError(f"数据库查询失败: {str(e)}") from e
    
    def batch_assign_roles(self, user_id: int, role_ids: List[int], assigned_by: Optional[int] = None) -> List[UserRole]:
        """
        批量分配角色
        
        Args:
            user_id (int): 用户ID
            role_ids (List[int]): 角色ID列表
            assigned_by (int, optional): 分配人ID
            
        Returns:
            List[UserRole]: 创建的用户角色关联列表
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_ids:
                return []
            
            user_roles = []
            for role_id in role_ids:
                try:
                    user_role = self.assign_role(user_id, role_id, assigned_by)
                    user_roles.append(user_role)
                except ValidationError as e:
                    self.logger.warning(f"批量分配角色跳过: user_id={user_id}, role_id={role_id}, error={str(e)}")
                    continue
            
            self.logger.info(f"批量分配角色成功: user_id={user_id}, 成功分配{len(user_roles)}个角色")
            return user_roles
            
        except ValueError:
            raise
        except DatabaseError:
            raise
    
    def batch_revoke_roles(self, user_id: int, role_ids: List[int]) -> int:
        """
        批量撤销角色
        
        Args:
            user_id (int): 用户ID
            role_ids (List[int]): 角色ID列表
            
        Returns:
            int: 实际撤销的角色数量
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_ids:
                return 0
            
            revoked_count = 0
            for role_id in role_ids:
                if self.revoke_role(user_id, role_id):
                    revoked_count += 1
            
            self.logger.info(f"批量撤销角色成功: user_id={user_id}, 撤销{revoked_count}个角色")
            return revoked_count
            
        except ValueError:
            raise
        except DatabaseError:
            raise
    
    def batch_assign_users(self, role_id: int, user_ids: List[int], assigned_by: Optional[int] = None) -> List[UserRole]:
        """
        批量分配用户
        
        Args:
            role_id (int): 角色ID
            user_ids (List[int]): 用户ID列表
            assigned_by (int, optional): 分配人ID
            
        Returns:
            List[UserRole]: 创建的用户角色关联列表
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            if not user_ids:
                return []
            
            user_roles = []
            for user_id in user_ids:
                try:
                    user_role = self.assign_role(user_id, role_id, assigned_by)
                    user_roles.append(user_role)
                except ValidationError as e:
                    self.logger.warning(f"批量分配用户跳过: user_id={user_id}, role_id={role_id}, error={str(e)}")
                    continue
            
            self.logger.info(f"批量分配用户成功: role_id={role_id}, 成功分配{len(user_roles)}个用户")
            return user_roles
            
        except ValueError:
            raise
        except DatabaseError:
            raise
    
    def activate_assignment(self, user_id: int, role_id: int) -> bool:
        """
        启用关联
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            bool: 操作成功返回True，关联不存在返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            user_role = self.session.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            ).first()
            
            if not user_role:
                return False
            
            user_role.activate()
            self.session.flush()
            
            self.logger.info(f"启用用户角色关联成功: user_id={user_id}, role_id={role_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"启用关联失败: user_id={user_id}, role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
    
    def deactivate_assignment(self, user_id: int, role_id: int) -> bool:
        """
        禁用关联
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            bool: 操作成功返回True，关联不存在返回False
            
        Raises:
            ValueError: 参数无效
            DatabaseError: 数据库操作失败
        """
        try:
            if not user_id or user_id <= 0:
                raise ValueError("用户ID必须是正整数")
            if not role_id or role_id <= 0:
                raise ValueError("角色ID必须是正整数")
            
            user_role = self.session.query(UserRole).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            ).first()
            
            if not user_role:
                return False
            
            user_role.deactivate()
            self.session.flush()
            
            self.logger.info(f"禁用用户角色关联成功: user_id={user_id}, role_id={role_id}")
            return True
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            self.logger.error(f"禁用关联失败: user_id={user_id}, role_id={role_id}, error={str(e)}")
            raise DatabaseError(f"数据库操作失败: {str(e)}") from e
