"""
用户角色关联DAO单元测试

本模块包含UserRoleDao类的完整单元测试，覆盖所有关系管理操作和业务方法的正常流程和异常流程。

Test Class:
    TestUserRoleDao: 用户角色关联DAO测试类

Author: AI Assistant
Created: 2025-07-19
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from dao.user_role_dao import UserRoleDao
from dao.base_dao import DatabaseError, ValidationError, NotFoundError
from models.user_role import UserRole
from models.user import User
from models.role import Role


class TestUserRoleDao:
    """用户角色关联DAO测试类"""
    
    @pytest.fixture
    def user_role_dao(self, db_session):
        """创建UserRoleDao实例"""
        return UserRoleDao(db_session)
    
    @pytest.fixture
    def admin_user(self, db_session):
        """创建管理员用户夹具"""
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash="admin_hash",
            status=1
        )
        db_session.add(admin)
        db_session.flush()
        return admin
    
    # ==================== 用户角色关系管理测试 ====================
    
    def test_assign_role_success(self, user_role_dao, sample_user, sample_role, admin_user):
        """测试分配角色成功"""
        # When
        result = user_role_dao.assign_role(sample_user.id, sample_role.id, admin_user.id)
        
        # Then
        assert result is not None
        assert result.user_id == sample_user.id
        assert result.role_id == sample_role.id
        assert result.assigned_by == admin_user.id
        assert result.status == 1
        assert result.assigned_at is not None
    
    def test_assign_role_without_assigner(self, user_role_dao, sample_user, sample_role):
        """测试分配角色不指定分配人"""
        # When
        result = user_role_dao.assign_role(sample_user.id, sample_role.id)
        
        # Then
        assert result is not None
        assert result.user_id == sample_user.id
        assert result.role_id == sample_role.id
        assert result.assigned_by is None
        assert result.status == 1
    
    def test_assign_role_duplicate(self, user_role_dao, sample_user, sample_role):
        """测试重复分配角色"""
        # Given - 先分配一次
        user_role_dao.assign_role(sample_user.id, sample_role.id)
        
        # When & Then - 再次分配应该抛出异常
        with pytest.raises(ValidationError):
            user_role_dao.assign_role(sample_user.id, sample_role.id)
    
    def test_assign_role_reactivate_existing(self, user_role_dao, sample_user, sample_role, db_session):
        """测试重新启用已存在的关联"""
        # Given - 创建禁用的关联
        existing_user_role = UserRole(
            user_id=sample_user.id,
            role_id=sample_role.id,
            status=0
        )
        db_session.add(existing_user_role)
        db_session.flush()
        
        # When
        result = user_role_dao.assign_role(sample_user.id, sample_role.id)
        
        # Then
        assert result.status == 1
        assert result.user_id == sample_user.id
        assert result.role_id == sample_role.id
    
    def test_assign_role_user_not_found(self, user_role_dao, sample_role):
        """测试分配角色给不存在的用户"""
        # When & Then
        with pytest.raises(ValidationError):
            user_role_dao.assign_role(99999, sample_role.id)
    
    def test_assign_role_role_not_found(self, user_role_dao, sample_user):
        """测试分配不存在的角色"""
        # When & Then
        with pytest.raises(ValidationError):
            user_role_dao.assign_role(sample_user.id, 99999)
    
    def test_revoke_role_success(self, user_role_dao, sample_user_role):
        """测试撤销角色成功"""
        # When
        result = user_role_dao.revoke_role(sample_user_role.user_id, sample_user_role.role_id)
        
        # Then
        assert result is True
        
        # 验证关联已被禁用
        updated_user_role = user_role_dao.session.query(UserRole).filter(
            UserRole.user_id == sample_user_role.user_id,
            UserRole.role_id == sample_user_role.role_id
        ).first()
        assert updated_user_role.status == 0
    
    def test_revoke_role_not_found(self, user_role_dao, sample_user, sample_role):
        """测试撤销不存在的关联"""
        # When
        result = user_role_dao.revoke_role(sample_user.id, sample_role.id)
        
        # Then
        assert result is False
    
    def test_reassign_role_success(self, user_role_dao, sample_user, multiple_roles, admin_user):
        """测试重新分配角色成功"""
        # Given - 先分配一个角色
        user_role_dao.assign_role(sample_user.id, multiple_roles[0].id)
        
        # When - 重新分配为另一个角色
        result = user_role_dao.reassign_role(
            sample_user.id, 
            multiple_roles[0].id, 
            multiple_roles[1].id, 
            admin_user.id
        )
        
        # Then
        assert result is not None
        assert result.user_id == sample_user.id
        assert result.role_id == multiple_roles[1].id
        assert result.assigned_by == admin_user.id
        
        # 验证旧角色已被撤销
        old_user_role = user_role_dao.session.query(UserRole).filter(
            UserRole.user_id == sample_user.id,
            UserRole.role_id == multiple_roles[0].id
        ).first()
        assert old_user_role.status == 0
    
    def test_reassign_role_old_role_not_found(self, user_role_dao, sample_user, multiple_roles):
        """测试重新分配角色但旧角色不存在"""
        # When & Then
        with pytest.raises(ValidationError):
            user_role_dao.reassign_role(sample_user.id, 99999, multiple_roles[1].id)
    
    # ==================== 查询方法测试 ====================
    
    def test_find_by_user_id(self, user_role_dao, sample_user, multiple_roles):
        """测试查询用户的角色关联"""
        # Given - 分配多个角色
        user_role_dao.assign_role(sample_user.id, multiple_roles[0].id)
        user_role_dao.assign_role(sample_user.id, multiple_roles[1].id)
        
        # When
        result = user_role_dao.find_by_user_id(sample_user.id)
        
        # Then
        assert len(result) == 2
        role_ids = [ur.role_id for ur in result]
        assert multiple_roles[0].id in role_ids
        assert multiple_roles[1].id in role_ids
    
    def test_find_by_user_id_include_inactive(self, user_role_dao, sample_user, sample_role, db_session):
        """测试查询用户角色关联包含禁用的"""
        # Given - 创建启用和禁用的关联
        active_user_role = UserRole(user_id=sample_user.id, role_id=sample_role.id, status=1)
        inactive_user_role = UserRole(user_id=sample_user.id, role_id=sample_role.id + 1, status=0)
        db_session.add_all([active_user_role, inactive_user_role])
        db_session.flush()
        
        # When - 查询所有关联
        result = user_role_dao.find_by_user_id(sample_user.id, active_only=False)
        
        # Then
        assert len(result) == 2
        
        # When - 只查询启用的关联
        active_result = user_role_dao.find_by_user_id(sample_user.id, active_only=True)
        
        # Then
        assert len(active_result) == 1
        assert active_result[0].status == 1
    
    def test_find_by_role_id(self, user_role_dao, multiple_users, sample_role):
        """测试查询角色的用户关联"""
        # Given - 分配角色给多个用户
        user_role_dao.assign_role(multiple_users[0].id, sample_role.id)
        user_role_dao.assign_role(multiple_users[1].id, sample_role.id)
        
        # When
        result = user_role_dao.find_by_role_id(sample_role.id)
        
        # Then
        assert len(result) == 2
        user_ids = [ur.user_id for ur in result]
        assert multiple_users[0].id in user_ids
        assert multiple_users[1].id in user_ids
    
    def test_find_active_assignments(self, user_role_dao, sample_user, sample_role, db_session):
        """测试查询所有启用的关联"""
        # Given - 创建启用和禁用的关联
        active_user_role = UserRole(user_id=sample_user.id, role_id=sample_role.id, status=1)
        inactive_user_role = UserRole(user_id=sample_user.id + 1, role_id=sample_role.id, status=0)
        db_session.add_all([active_user_role, inactive_user_role])
        db_session.flush()
        
        # When
        result = user_role_dao.find_active_assignments()
        
        # Then
        assert len(result) >= 1  # 至少有一个启用的关联
        for user_role in result:
            assert user_role.status == 1
    
    def test_find_by_assigned_by(self, user_role_dao, sample_user, sample_role, admin_user):
        """测试查询分配人的关联"""
        # Given
        user_role_dao.assign_role(sample_user.id, sample_role.id, admin_user.id)
        
        # When
        result = user_role_dao.find_by_assigned_by(admin_user.id)
        
        # Then
        assert len(result) == 1
        assert result[0].assigned_by == admin_user.id
        assert result[0].user_id == sample_user.id
        assert result[0].role_id == sample_role.id
    
    # ==================== 批量操作测试 ====================
    
    def test_batch_assign_roles(self, user_role_dao, sample_user, multiple_roles, admin_user):
        """测试批量分配角色"""
        # Given
        role_ids = [role.id for role in multiple_roles]
        
        # When
        result = user_role_dao.batch_assign_roles(sample_user.id, role_ids, admin_user.id)
        
        # Then
        assert len(result) == 3
        for user_role in result:
            assert user_role.user_id == sample_user.id
            assert user_role.assigned_by == admin_user.id
            assert user_role.status == 1
    
    def test_batch_assign_roles_with_duplicates(self, user_role_dao, sample_user, multiple_roles):
        """测试批量分配角色包含重复"""
        # Given - 先分配一个角色
        user_role_dao.assign_role(sample_user.id, multiple_roles[0].id)
        
        role_ids = [role.id for role in multiple_roles]
        
        # When - 批量分配包含已存在的角色
        result = user_role_dao.batch_assign_roles(sample_user.id, role_ids)
        
        # Then - 应该跳过重复的角色
        assert len(result) == 2  # 只有两个新角色被分配
    
    def test_batch_revoke_roles(self, user_role_dao, sample_user, multiple_roles):
        """测试批量撤销角色"""
        # Given - 先分配多个角色
        role_ids = [role.id for role in multiple_roles]
        user_role_dao.batch_assign_roles(sample_user.id, role_ids)
        
        # When
        revoked_count = user_role_dao.batch_revoke_roles(sample_user.id, role_ids[:2])
        
        # Then
        assert revoked_count == 2
        
        # 验证角色已被撤销
        remaining_roles = user_role_dao.find_by_user_id(sample_user.id)
        assert len(remaining_roles) == 1
    
    def test_batch_assign_users(self, user_role_dao, multiple_users, sample_role, admin_user):
        """测试批量分配用户"""
        # Given
        user_ids = [user.id for user in multiple_users[:2]]  # 只取前两个启用的用户
        
        # When
        result = user_role_dao.batch_assign_users(sample_role.id, user_ids, admin_user.id)
        
        # Then
        assert len(result) == 2
        for user_role in result:
            assert user_role.role_id == sample_role.id
            assert user_role.assigned_by == admin_user.id
            assert user_role.status == 1
    
    # ==================== 状态管理测试 ====================
    
    def test_activate_assignment(self, user_role_dao, sample_user, sample_role, db_session):
        """测试启用关联"""
        # Given - 创建禁用的关联
        user_role = UserRole(user_id=sample_user.id, role_id=sample_role.id, status=0)
        db_session.add(user_role)
        db_session.flush()
        
        # When
        result = user_role_dao.activate_assignment(sample_user.id, sample_role.id)
        
        # Then
        assert result is True
        
        # 验证关联已被启用
        updated_user_role = user_role_dao.session.query(UserRole).filter(
            UserRole.user_id == sample_user.id,
            UserRole.role_id == sample_role.id
        ).first()
        assert updated_user_role.status == 1
    
    def test_activate_assignment_not_found(self, user_role_dao, sample_user, sample_role):
        """测试启用不存在的关联"""
        # When
        result = user_role_dao.activate_assignment(sample_user.id, sample_role.id)
        
        # Then
        assert result is False
    
    def test_deactivate_assignment(self, user_role_dao, sample_user_role):
        """测试禁用关联"""
        # When
        result = user_role_dao.deactivate_assignment(sample_user_role.user_id, sample_user_role.role_id)
        
        # Then
        assert result is True
        
        # 验证关联已被禁用
        updated_user_role = user_role_dao.session.query(UserRole).filter(
            UserRole.user_id == sample_user_role.user_id,
            UserRole.role_id == sample_user_role.role_id
        ).first()
        assert updated_user_role.status == 0
    
    # ==================== 异常场景测试 ====================
    
    def test_assign_role_invalid_user_id(self, user_role_dao, sample_role):
        """测试分配角色无效用户ID"""
        # When & Then
        with pytest.raises(ValueError):
            user_role_dao.assign_role(0, sample_role.id)
        
        with pytest.raises(ValueError):
            user_role_dao.assign_role(-1, sample_role.id)
        
        with pytest.raises(ValueError):
            user_role_dao.assign_role(None, sample_role.id)
    
    def test_assign_role_invalid_role_id(self, user_role_dao, sample_user):
        """测试分配角色无效角色ID"""
        # When & Then
        with pytest.raises(ValueError):
            user_role_dao.assign_role(sample_user.id, 0)
        
        with pytest.raises(ValueError):
            user_role_dao.assign_role(sample_user.id, -1)
        
        with pytest.raises(ValueError):
            user_role_dao.assign_role(sample_user.id, None)
    
    def test_assign_role_invalid_assigned_by(self, user_role_dao, sample_user, sample_role):
        """测试分配角色无效分配人ID"""
        # When & Then
        with pytest.raises(ValueError):
            user_role_dao.assign_role(sample_user.id, sample_role.id, 0)
        
        with pytest.raises(ValueError):
            user_role_dao.assign_role(sample_user.id, sample_role.id, -1)
    
    def test_operations_with_null_values(self, user_role_dao):
        """测试空值处理"""
        # When & Then
        with pytest.raises(ValueError):
            user_role_dao.find_by_user_id(0)
        
        with pytest.raises(ValueError):
            user_role_dao.find_by_role_id(-1)
        
        with pytest.raises(ValueError):
            user_role_dao.find_by_assigned_by(None)
        
        with pytest.raises(ValueError):
            user_role_dao.activate_assignment(0, 1)
        
        with pytest.raises(ValueError):
            user_role_dao.deactivate_assignment(1, 0)
    
    def test_batch_operations_empty_lists(self, user_role_dao, sample_user, sample_role):
        """测试批量操作空列表"""
        # When & Then
        result1 = user_role_dao.batch_assign_roles(sample_user.id, [])
        assert result1 == []
        
        result2 = user_role_dao.batch_revoke_roles(sample_user.id, [])
        assert result2 == 0
        
        result3 = user_role_dao.batch_assign_users(sample_role.id, [])
        assert result3 == []
    
    @patch('dao.user_role_dao.UserRoleDao.session')
    def test_database_connection_error(self, mock_session, user_role_dao):
        """测试数据库连接异常"""
        # Given
        mock_session.query.side_effect = SQLAlchemyError("Connection failed")
        
        # When & Then
        with pytest.raises(DatabaseError):
            user_role_dao.find_by_user_id(1)
