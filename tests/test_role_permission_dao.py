"""
角色权限关联DAO单元测试

本模块包含RolePermissionDao类的完整单元测试，覆盖所有关系管理操作和业务方法的正常流程和异常流程。

Test Class:
    TestRolePermissionDao: 角色权限关联DAO测试类

Author: AI Assistant
Created: 2025-07-19
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from dao.role_permission_dao import RolePermissionDao
from dao.base_dao import DatabaseError, ValidationError, NotFoundError
from models.role_permission import RolePermission
from models.role import Role
from models.permission import Permission
from models.user import User


class TestRolePermissionDao:
    """角色权限关联DAO测试类"""
    
    @pytest.fixture
    def role_permission_dao(self, db_session):
        """创建RolePermissionDao实例"""
        return RolePermissionDao(db_session)
    
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
    
    # ==================== 角色权限关系管理测试 ====================
    
    def test_grant_permission_success(self, role_permission_dao, sample_role, sample_permission, admin_user):
        """测试授予权限成功"""
        # When
        result = role_permission_dao.grant_permission(sample_role.id, sample_permission.id, admin_user.id)
        
        # Then
        assert result is not None
        assert result.role_id == sample_role.id
        assert result.permission_id == sample_permission.id
        assert result.granted_by == admin_user.id
        assert result.status == 1
        assert result.granted_at is not None
    
    def test_grant_permission_without_granter(self, role_permission_dao, sample_role, sample_permission):
        """测试授予权限不指定授权人"""
        # When
        result = role_permission_dao.grant_permission(sample_role.id, sample_permission.id)
        
        # Then
        assert result is not None
        assert result.role_id == sample_role.id
        assert result.permission_id == sample_permission.id
        assert result.granted_by is None
        assert result.status == 1
    
    def test_grant_permission_duplicate(self, role_permission_dao, sample_role, sample_permission):
        """测试重复授予权限"""
        # Given - 先授予一次
        role_permission_dao.grant_permission(sample_role.id, sample_permission.id)
        
        # When & Then - 再次授予应该抛出异常
        with pytest.raises(ValidationError):
            role_permission_dao.grant_permission(sample_role.id, sample_permission.id)
    
    def test_grant_permission_reactivate_existing(self, role_permission_dao, sample_role, sample_permission, db_session):
        """测试重新启用已存在的关联"""
        # Given - 创建禁用的关联
        existing_role_permission = RolePermission(
            role_id=sample_role.id,
            permission_id=sample_permission.id,
            status=0
        )
        db_session.add(existing_role_permission)
        db_session.flush()
        
        # When
        result = role_permission_dao.grant_permission(sample_role.id, sample_permission.id)
        
        # Then
        assert result.status == 1
        assert result.role_id == sample_role.id
        assert result.permission_id == sample_permission.id
    
    def test_grant_permission_role_not_found(self, role_permission_dao, sample_permission):
        """测试授予权限给不存在的角色"""
        # When & Then
        with pytest.raises(ValidationError):
            role_permission_dao.grant_permission(99999, sample_permission.id)
    
    def test_grant_permission_permission_not_found(self, role_permission_dao, sample_role):
        """测试授予不存在的权限"""
        # When & Then
        with pytest.raises(ValidationError):
            role_permission_dao.grant_permission(sample_role.id, 99999)
    
    def test_revoke_permission_success(self, role_permission_dao, sample_role_permission):
        """测试撤销权限成功"""
        # When
        result = role_permission_dao.revoke_permission(sample_role_permission.role_id, sample_role_permission.permission_id)
        
        # Then
        assert result is True
        
        # 验证关联已被禁用
        updated_role_permission = role_permission_dao.session.query(RolePermission).filter(
            RolePermission.role_id == sample_role_permission.role_id,
            RolePermission.permission_id == sample_role_permission.permission_id
        ).first()
        assert updated_role_permission.status == 0
    
    def test_revoke_permission_not_found(self, role_permission_dao, sample_role, sample_permission):
        """测试撤销不存在的关联"""
        # When
        result = role_permission_dao.revoke_permission(sample_role.id, sample_permission.id)
        
        # Then
        assert result is False
    
    def test_regrant_permission_success(self, role_permission_dao, sample_role, multiple_permissions, admin_user):
        """测试重新授权成功"""
        # Given - 先授予一个权限
        role_permission_dao.grant_permission(sample_role.id, multiple_permissions[0].id)
        
        # When - 重新授权为另一个权限
        result = role_permission_dao.regrant_permission(
            sample_role.id, 
            multiple_permissions[0].id, 
            multiple_permissions[1].id, 
            admin_user.id
        )
        
        # Then
        assert result is not None
        assert result.role_id == sample_role.id
        assert result.permission_id == multiple_permissions[1].id
        assert result.granted_by == admin_user.id
        
        # 验证旧权限已被撤销
        old_role_permission = role_permission_dao.session.query(RolePermission).filter(
            RolePermission.role_id == sample_role.id,
            RolePermission.permission_id == multiple_permissions[0].id
        ).first()
        assert old_role_permission.status == 0
    
    def test_regrant_permission_old_permission_not_found(self, role_permission_dao, sample_role, multiple_permissions):
        """测试重新授权但旧权限不存在"""
        # When & Then
        with pytest.raises(ValidationError):
            role_permission_dao.regrant_permission(sample_role.id, 99999, multiple_permissions[1].id)
    
    # ==================== 查询方法测试 ====================
    
    def test_find_by_role_id(self, role_permission_dao, sample_role, multiple_permissions):
        """测试查询角色的权限关联"""
        # Given - 授予多个权限
        role_permission_dao.grant_permission(sample_role.id, multiple_permissions[0].id)
        role_permission_dao.grant_permission(sample_role.id, multiple_permissions[1].id)
        
        # When
        result = role_permission_dao.find_by_role_id(sample_role.id)
        
        # Then
        assert len(result) == 2
        permission_ids = [rp.permission_id for rp in result]
        assert multiple_permissions[0].id in permission_ids
        assert multiple_permissions[1].id in permission_ids
    
    def test_find_by_role_id_include_inactive(self, role_permission_dao, sample_role, sample_permission, db_session):
        """测试查询角色权限关联包含禁用的"""
        # Given - 创建启用和禁用的关联
        active_role_permission = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id, status=1)
        inactive_role_permission = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id + 1, status=0)
        db_session.add_all([active_role_permission, inactive_role_permission])
        db_session.flush()
        
        # When - 查询所有关联
        result = role_permission_dao.find_by_role_id(sample_role.id, active_only=False)
        
        # Then
        assert len(result) == 2
        
        # When - 只查询启用的关联
        active_result = role_permission_dao.find_by_role_id(sample_role.id, active_only=True)
        
        # Then
        assert len(active_result) == 1
        assert active_result[0].status == 1
    
    def test_find_by_permission_id(self, role_permission_dao, multiple_roles, sample_permission):
        """测试查询权限的角色关联"""
        # Given - 授予权限给多个角色
        role_permission_dao.grant_permission(multiple_roles[0].id, sample_permission.id)
        role_permission_dao.grant_permission(multiple_roles[1].id, sample_permission.id)
        
        # When
        result = role_permission_dao.find_by_permission_id(sample_permission.id)
        
        # Then
        assert len(result) == 2
        role_ids = [rp.role_id for rp in result]
        assert multiple_roles[0].id in role_ids
        assert multiple_roles[1].id in role_ids
    
    def test_find_active_grants(self, role_permission_dao, sample_role, sample_permission, db_session):
        """测试查询所有启用的关联"""
        # Given - 创建启用和禁用的关联
        active_role_permission = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id, status=1)
        inactive_role_permission = RolePermission(role_id=sample_role.id + 1, permission_id=sample_permission.id, status=0)
        db_session.add_all([active_role_permission, inactive_role_permission])
        db_session.flush()
        
        # When
        result = role_permission_dao.find_active_grants()
        
        # Then
        assert len(result) >= 1  # 至少有一个启用的关联
        for role_permission in result:
            assert role_permission.status == 1
    
    def test_find_by_granted_by(self, role_permission_dao, sample_role, sample_permission, admin_user):
        """测试查询授权人的关联"""
        # Given
        role_permission_dao.grant_permission(sample_role.id, sample_permission.id, admin_user.id)
        
        # When
        result = role_permission_dao.find_by_granted_by(admin_user.id)
        
        # Then
        assert len(result) == 1
        assert result[0].granted_by == admin_user.id
        assert result[0].role_id == sample_role.id
        assert result[0].permission_id == sample_permission.id
    
    # ==================== 批量操作测试 ====================
    
    def test_batch_grant_permissions(self, role_permission_dao, sample_role, multiple_permissions, admin_user):
        """测试批量授予权限"""
        # Given
        permission_ids = [permission.id for permission in multiple_permissions]
        
        # When
        result = role_permission_dao.batch_grant_permissions(sample_role.id, permission_ids, admin_user.id)
        
        # Then
        assert len(result) == 5
        for role_permission in result:
            assert role_permission.role_id == sample_role.id
            assert role_permission.granted_by == admin_user.id
            assert role_permission.status == 1
    
    def test_batch_grant_permissions_with_duplicates(self, role_permission_dao, sample_role, multiple_permissions):
        """测试批量授予权限包含重复"""
        # Given - 先授予一个权限
        role_permission_dao.grant_permission(sample_role.id, multiple_permissions[0].id)
        
        permission_ids = [permission.id for permission in multiple_permissions]
        
        # When - 批量授予包含已存在的权限
        result = role_permission_dao.batch_grant_permissions(sample_role.id, permission_ids)
        
        # Then - 应该跳过重复的权限
        assert len(result) == 4  # 只有四个新权限被授予
    
    def test_batch_revoke_permissions(self, role_permission_dao, sample_role, multiple_permissions):
        """测试批量撤销权限"""
        # Given - 先授予多个权限
        permission_ids = [permission.id for permission in multiple_permissions]
        role_permission_dao.batch_grant_permissions(sample_role.id, permission_ids)
        
        # When
        revoked_count = role_permission_dao.batch_revoke_permissions(sample_role.id, permission_ids[:2])
        
        # Then
        assert revoked_count == 2
        
        # 验证权限已被撤销
        remaining_permissions = role_permission_dao.find_by_role_id(sample_role.id)
        assert len(remaining_permissions) == 3
    
    def test_batch_grant_roles(self, role_permission_dao, multiple_roles, sample_permission, admin_user):
        """测试批量授权角色"""
        # Given
        role_ids = [role.id for role in multiple_roles]
        
        # When
        result = role_permission_dao.batch_grant_roles(sample_permission.id, role_ids, admin_user.id)
        
        # Then
        assert len(result) == 3
        for role_permission in result:
            assert role_permission.permission_id == sample_permission.id
            assert role_permission.granted_by == admin_user.id
            assert role_permission.status == 1
    
    # ==================== 状态管理测试 ====================
    
    def test_activate_grant(self, role_permission_dao, sample_role, sample_permission, db_session):
        """测试启用关联"""
        # Given - 创建禁用的关联
        role_permission = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id, status=0)
        db_session.add(role_permission)
        db_session.flush()
        
        # When
        result = role_permission_dao.activate_grant(sample_role.id, sample_permission.id)
        
        # Then
        assert result is True
        
        # 验证关联已被启用
        updated_role_permission = role_permission_dao.session.query(RolePermission).filter(
            RolePermission.role_id == sample_role.id,
            RolePermission.permission_id == sample_permission.id
        ).first()
        assert updated_role_permission.status == 1
    
    def test_activate_grant_not_found(self, role_permission_dao, sample_role, sample_permission):
        """测试启用不存在的关联"""
        # When
        result = role_permission_dao.activate_grant(sample_role.id, sample_permission.id)
        
        # Then
        assert result is False
    
    def test_deactivate_grant(self, role_permission_dao, sample_role_permission):
        """测试禁用关联"""
        # When
        result = role_permission_dao.deactivate_grant(sample_role_permission.role_id, sample_role_permission.permission_id)
        
        # Then
        assert result is True
        
        # 验证关联已被禁用
        updated_role_permission = role_permission_dao.session.query(RolePermission).filter(
            RolePermission.role_id == sample_role_permission.role_id,
            RolePermission.permission_id == sample_role_permission.permission_id
        ).first()
        assert updated_role_permission.status == 0
    
    # ==================== 异常场景测试 ====================
    
    def test_grant_permission_invalid_role_id(self, role_permission_dao, sample_permission):
        """测试授予权限无效角色ID"""
        # When & Then
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(0, sample_permission.id)
        
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(-1, sample_permission.id)
        
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(None, sample_permission.id)
    
    def test_grant_permission_invalid_permission_id(self, role_permission_dao, sample_role):
        """测试授予权限无效权限ID"""
        # When & Then
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(sample_role.id, 0)
        
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(sample_role.id, -1)
        
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(sample_role.id, None)
    
    def test_grant_permission_invalid_granted_by(self, role_permission_dao, sample_role, sample_permission):
        """测试授予权限无效授权人ID"""
        # When & Then
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(sample_role.id, sample_permission.id, 0)
        
        with pytest.raises(ValueError):
            role_permission_dao.grant_permission(sample_role.id, sample_permission.id, -1)
    
    def test_operations_with_null_values(self, role_permission_dao):
        """测试空值处理"""
        # When & Then
        with pytest.raises(ValueError):
            role_permission_dao.find_by_role_id(0)
        
        with pytest.raises(ValueError):
            role_permission_dao.find_by_permission_id(-1)
        
        with pytest.raises(ValueError):
            role_permission_dao.find_by_granted_by(None)
        
        with pytest.raises(ValueError):
            role_permission_dao.activate_grant(0, 1)
        
        with pytest.raises(ValueError):
            role_permission_dao.deactivate_grant(1, 0)
    
    def test_batch_operations_empty_lists(self, role_permission_dao, sample_role, sample_permission):
        """测试批量操作空列表"""
        # When & Then
        result1 = role_permission_dao.batch_grant_permissions(sample_role.id, [])
        assert result1 == []
        
        result2 = role_permission_dao.batch_revoke_permissions(sample_role.id, [])
        assert result2 == 0
        
        result3 = role_permission_dao.batch_grant_roles(sample_permission.id, [])
        assert result3 == []
    
    def test_batch_operations_invalid_ids(self, role_permission_dao, sample_role, sample_permission):
        """测试批量操作无效ID"""
        # When & Then
        with pytest.raises(ValueError):
            role_permission_dao.batch_grant_permissions(0, [sample_permission.id])
        
        with pytest.raises(ValueError):
            role_permission_dao.batch_revoke_permissions(-1, [sample_permission.id])
        
        with pytest.raises(ValueError):
            role_permission_dao.batch_grant_roles(0, [sample_role.id])
    
    @patch('dao.role_permission_dao.RolePermissionDao.session')
    def test_database_connection_error(self, mock_session, role_permission_dao):
        """测试数据库连接异常"""
        # Given
        mock_session.query.side_effect = SQLAlchemyError("Connection failed")
        
        # When & Then
        with pytest.raises(DatabaseError):
            role_permission_dao.find_by_role_id(1)
