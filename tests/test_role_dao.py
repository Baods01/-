"""
角色DAO单元测试

本模块包含RoleDao类的完整单元测试，覆盖所有CRUD操作和业务方法的正常流程和异常流程。

Test Class:
    TestRoleDao: 角色DAO测试类

Author: AI Assistant
Created: 2025-07-19
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from dao.role_dao import RoleDao
from dao.base_dao import DatabaseError, ValidationError, NotFoundError
from models.role import Role
from models.user import User
from models.permission import Permission
from models.user_role import UserRole
from models.role_permission import RolePermission


class TestRoleDao:
    """角色DAO测试类"""
    
    @pytest.fixture
    def role_dao(self, db_session):
        """创建RoleDao实例"""
        return RoleDao(db_session)
    
    # ==================== 基础CRUD操作测试 ====================
    
    def test_create_role_success(self, role_dao, db_session):
        """测试创建角色成功"""
        # Given
        role = Role(
            role_name="新角色",
            role_code="new_role",
            status=1
        )
        
        # When
        result = role_dao.create(role)
        
        # Then
        assert result is not None
        assert result.id is not None
        assert result.role_name == "新角色"
        assert result.role_code == "new_role"
        assert result.status == 1
        assert result.created_at is not None
        assert result.updated_at is not None
    
    def test_create_role_duplicate_code(self, role_dao, sample_role):
        """测试角色代码重复异常"""
        # Given
        duplicate_role = Role(
            role_name="不同名称",
            role_code=sample_role.role_code,  # 重复角色代码
            status=1
        )
        
        # When & Then
        with pytest.raises(DatabaseError):
            role_dao.create(duplicate_role)
    
    def test_find_by_id_success(self, role_dao, sample_role):
        """测试根据ID查询成功"""
        # When
        result = role_dao.find_by_id(sample_role.id)
        
        # Then
        assert result is not None
        assert result.id == sample_role.id
        assert result.role_name == sample_role.role_name
        assert result.role_code == sample_role.role_code
    
    def test_find_by_id_not_found(self, role_dao):
        """测试查询不存在的角色"""
        # When
        result = role_dao.find_by_id(99999)
        
        # Then
        assert result is None
    
    def test_find_all_success(self, role_dao, multiple_roles):
        """测试查询所有角色"""
        # When
        result = role_dao.find_all()
        
        # Then
        assert len(result) == 3
        role_codes = [role.role_code for role in result]
        assert "admin" in role_codes
        assert "editor" in role_codes
        assert "viewer" in role_codes
    
    def test_update_role_success(self, role_dao, sample_role):
        """测试更新角色成功"""
        # Given
        original_updated_at = sample_role.updated_at
        sample_role.role_name = "更新后的角色"
        
        # When
        result = role_dao.update(sample_role)
        
        # Then
        assert result.role_name == "更新后的角色"
        assert result.updated_at > original_updated_at
    
    def test_delete_by_id_success(self, role_dao, sample_role):
        """测试删除角色成功"""
        # When
        result = role_dao.delete_by_id(sample_role.id)
        
        # Then
        assert result is True
        
        # 验证角色已被删除
        deleted_role = role_dao.find_by_id(sample_role.id)
        assert deleted_role is None
    
    # ==================== 角色特有方法测试 ====================
    
    def test_find_by_role_code_success(self, role_dao, sample_role):
        """测试根据角色代码查询成功"""
        # When
        result = role_dao.find_by_role_code(sample_role.role_code)
        
        # Then
        assert result is not None
        assert result.role_code == sample_role.role_code
        assert result.id == sample_role.id
    
    def test_find_by_role_code_not_found(self, role_dao):
        """测试根据角色代码查询不存在的角色"""
        # When
        result = role_dao.find_by_role_code("nonexistent_role")
        
        # Then
        assert result is None
    
    def test_find_by_role_code_invalid_input(self, role_dao):
        """测试无效角色代码输入"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.find_by_role_code("")
        
        with pytest.raises(ValueError):
            role_dao.find_by_role_code(None)
        
        with pytest.raises(ValueError):
            role_dao.find_by_role_code(123)
    
    def test_find_active_roles(self, role_dao, multiple_roles):
        """测试查询启用角色"""
        # When
        result = role_dao.find_active_roles()
        
        # Then
        assert len(result) == 3  # 所有角色都是启用的
        for role in result:
            assert role.status == 1
    
    def test_find_by_status(self, role_dao, multiple_roles, db_session):
        """测试根据状态查询角色"""
        # Given - 禁用一个角色
        multiple_roles[0].status = 0
        db_session.flush()
        
        # When - 查询启用角色
        active_roles = role_dao.find_by_status(1)
        
        # Then
        assert len(active_roles) == 2
        for role in active_roles:
            assert role.status == 1
        
        # When - 查询禁用角色
        inactive_roles = role_dao.find_by_status(0)
        
        # Then
        assert len(inactive_roles) == 1
        assert inactive_roles[0].status == 0
    
    def test_search_roles(self, role_dao, multiple_roles):
        """测试角色搜索功能"""
        # When - 按角色名称搜索
        result1 = role_dao.search_roles("管理员")
        
        # Then
        assert len(result1) == 1
        assert result1[0].role_name == "管理员"
        
        # When - 按角色代码搜索
        result2 = role_dao.search_roles("editor")
        
        # Then
        assert len(result2) == 1
        assert result2[0].role_code == "editor"
        
        # When - 模糊搜索
        result3 = role_dao.search_roles("者")
        
        # Then
        assert len(result3) == 2  # "编辑者"和"查看者"
    
    def test_search_roles_with_limit(self, role_dao, multiple_roles):
        """测试带限制的角色搜索"""
        # When
        result = role_dao.search_roles("者", limit=1)
        
        # Then
        assert len(result) == 1
    
    # ==================== 角色权限关系测试 ====================
    
    def test_get_role_permissions(self, role_dao, sample_role, sample_permission, sample_role_permission):
        """测试获取角色权限"""
        # When
        result = role_dao.get_role_permissions(sample_role.id)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_permission.id
        assert result[0].permission_code == sample_permission.permission_code
    
    def test_has_permission(self, role_dao, sample_role, sample_permission, sample_role_permission):
        """测试检查角色权限"""
        # When & Then
        assert role_dao.has_permission(sample_role.id, sample_permission.permission_code) is True
        assert role_dao.has_permission(sample_role.id, "nonexistent:permission") is False
    
    def test_get_role_users(self, role_dao, sample_role, sample_user, sample_user_role):
        """测试获取角色用户"""
        # When
        result = role_dao.get_role_users(sample_role.id)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_user.id
        assert result[0].username == sample_user.username
    
    # ==================== 角色管理方法测试 ====================
    
    def test_activate_role(self, role_dao, db_session):
        """测试启用角色"""
        # Given - 创建禁用角色
        role = Role(
            role_name="禁用角色",
            role_code="inactive_role",
            status=0
        )
        db_session.add(role)
        db_session.flush()
        
        # When
        result = role_dao.activate_role(role.id)
        
        # Then
        assert result is True
        updated_role = role_dao.find_by_id(role.id)
        assert updated_role.status == 1
    
    def test_activate_role_not_found(self, role_dao):
        """测试启用不存在的角色"""
        # When
        result = role_dao.activate_role(99999)
        
        # Then
        assert result is False
    
    def test_deactivate_role(self, role_dao, sample_role):
        """测试禁用角色"""
        # When
        result = role_dao.deactivate_role(sample_role.id)
        
        # Then
        assert result is True
        updated_role = role_dao.find_by_id(sample_role.id)
        assert updated_role.status == 0
    
    def test_get_role_statistics(self, role_dao, sample_role, sample_user, sample_permission,
                                sample_user_role, sample_role_permission):
        """测试获取角色统计信息"""
        # When
        result = role_dao.get_role_statistics(sample_role.id)
        
        # Then
        assert result['role_id'] == sample_role.id
        assert result['role_name'] == sample_role.role_name
        assert result['role_code'] == sample_role.role_code
        assert result['user_count'] == 1
        assert result['permission_count'] == 1
        assert 'created_at' in result
        assert 'updated_at' in result
    
    def test_get_role_statistics_not_found(self, role_dao):
        """测试获取不存在角色的统计信息"""
        # When & Then
        with pytest.raises(NotFoundError):
            role_dao.get_role_statistics(99999)
    
    def test_find_roles_by_permission(self, role_dao, sample_role, sample_permission, sample_role_permission):
        """测试根据权限查找角色"""
        # When
        result = role_dao.find_roles_by_permission(sample_permission.permission_code)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_role.id
        assert result[0].role_code == sample_role.role_code
    
    def test_get_permissions_by_resource(self, role_dao, sample_role, sample_permission, sample_role_permission):
        """测试获取角色在特定资源上的权限"""
        # When
        result = role_dao.get_permissions_by_resource(sample_role.id, sample_permission.resource_type)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_permission.id
        assert result[0].resource_type == sample_permission.resource_type
    
    # ==================== 异常场景测试 ====================
    
    def test_create_role_invalid_data(self, role_dao):
        """测试创建角色无效数据"""
        # Given - 无效角色代码
        invalid_role1 = Role(
            role_name="有效名称",
            role_code="A",  # 角色代码太短
            status=1
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            role_dao.create(invalid_role1)
        
        # Given - 无效角色名称
        invalid_role2 = Role(
            role_name="",  # 空角色名称
            role_code="valid_code",
            status=1
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            role_dao.create(invalid_role2)
    
    def test_operations_with_null_values(self, role_dao):
        """测试空值处理"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.get_role_permissions(None)
        
        with pytest.raises(ValueError):
            role_dao.has_permission(None, "test:view")
        
        with pytest.raises(ValueError):
            role_dao.has_permission(1, None)
        
        with pytest.raises(ValueError):
            role_dao.get_role_users(0)
    
    def test_invalid_status_parameter(self, role_dao):
        """测试无效状态参数"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.find_by_status(2)
        
        with pytest.raises(ValueError):
            role_dao.find_by_status(-1)
    
    def test_invalid_search_keyword(self, role_dao):
        """测试无效搜索关键词"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.search_roles("")
        
        with pytest.raises(ValueError):
            role_dao.search_roles(None)
    
    @patch('dao.role_dao.RoleDao.session')
    def test_database_connection_error(self, mock_session, role_dao):
        """测试数据库连接异常"""
        # Given
        mock_session.query.side_effect = SQLAlchemyError("Connection failed")
        
        # When & Then
        with pytest.raises(DatabaseError):
            role_dao.find_by_id(1)
    
    def test_activate_deactivate_invalid_id(self, role_dao):
        """测试启用/禁用角色无效ID"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.activate_role(0)
        
        with pytest.raises(ValueError):
            role_dao.activate_role(-1)
        
        with pytest.raises(ValueError):
            role_dao.deactivate_role(None)
    
    def test_get_statistics_invalid_id(self, role_dao):
        """测试获取统计信息无效ID"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.get_role_statistics(0)
        
        with pytest.raises(ValueError):
            role_dao.get_role_statistics(-1)
    
    def test_find_roles_by_permission_invalid_input(self, role_dao):
        """测试根据权限查找角色无效输入"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.find_roles_by_permission("")
        
        with pytest.raises(ValueError):
            role_dao.find_roles_by_permission(None)
    
    def test_get_permissions_by_resource_invalid_input(self, role_dao):
        """测试获取资源权限无效输入"""
        # When & Then
        with pytest.raises(ValueError):
            role_dao.get_permissions_by_resource(0, "user")
        
        with pytest.raises(ValueError):
            role_dao.get_permissions_by_resource(1, "")
        
        with pytest.raises(ValueError):
            role_dao.get_permissions_by_resource(1, None)
