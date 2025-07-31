"""
权限DAO单元测试

本模块包含PermissionDao类的完整单元测试，覆盖所有CRUD操作和业务方法的正常流程和异常流程。

Test Class:
    TestPermissionDao: 权限DAO测试类

Author: AI Assistant
Created: 2025-07-19
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from dao.permission_dao import PermissionDao
from dao.base_dao import DatabaseError, ValidationError, NotFoundError
from models.permission import Permission
from models.role import Role
from models.user import User
from models.role_permission import RolePermission
from models.user_role import UserRole


class TestPermissionDao:
    """权限DAO测试类"""
    
    @pytest.fixture
    def permission_dao(self, db_session):
        """创建PermissionDao实例"""
        return PermissionDao(db_session)
    
    # ==================== 基础CRUD操作测试 ====================
    
    def test_create_permission_success(self, permission_dao, db_session):
        """测试创建权限成功"""
        # Given
        permission = Permission(
            permission_name="新权限",
            permission_code="new:create",
            resource_type="new",
            action_type="create"
        )
        
        # When
        result = permission_dao.create(permission)
        
        # Then
        assert result is not None
        assert result.id is not None
        assert result.permission_name == "新权限"
        assert result.permission_code == "new:create"
        assert result.resource_type == "new"
        assert result.action_type == "create"
        assert result.created_at is not None
    
    def test_create_permission_duplicate_code(self, permission_dao, sample_permission):
        """测试权限代码重复异常"""
        # Given
        duplicate_permission = Permission(
            permission_name="不同名称",
            permission_code=sample_permission.permission_code,  # 重复权限代码
            resource_type="different",
            action_type="different"
        )
        
        # When & Then
        with pytest.raises(DatabaseError):
            permission_dao.create(duplicate_permission)
    
    def test_find_by_id_success(self, permission_dao, sample_permission):
        """测试根据ID查询成功"""
        # When
        result = permission_dao.find_by_id(sample_permission.id)
        
        # Then
        assert result is not None
        assert result.id == sample_permission.id
        assert result.permission_name == sample_permission.permission_name
        assert result.permission_code == sample_permission.permission_code
    
    def test_find_by_id_not_found(self, permission_dao):
        """测试查询不存在的权限"""
        # When
        result = permission_dao.find_by_id(99999)
        
        # Then
        assert result is None
    
    def test_find_all_success(self, permission_dao, multiple_permissions):
        """测试查询所有权限"""
        # When
        result = permission_dao.find_all()
        
        # Then
        assert len(result) == 5
        permission_codes = [p.permission_code for p in result]
        assert "user:view" in permission_codes
        assert "user:create" in permission_codes
        assert "system:config" in permission_codes
    
    def test_update_permission_success(self, permission_dao, sample_permission):
        """测试更新权限成功"""
        # Given
        sample_permission.permission_name = "更新后的权限"
        
        # When
        result = permission_dao.update(sample_permission)
        
        # Then
        assert result.permission_name == "更新后的权限"
    
    def test_delete_by_id_success(self, permission_dao, sample_permission):
        """测试删除权限成功"""
        # When
        result = permission_dao.delete_by_id(sample_permission.id)
        
        # Then
        assert result is True
        
        # 验证权限已被删除
        deleted_permission = permission_dao.find_by_id(sample_permission.id)
        assert deleted_permission is None
    
    # ==================== 权限特有方法测试 ====================
    
    def test_find_by_permission_code_success(self, permission_dao, sample_permission):
        """测试根据权限代码查询成功"""
        # When
        result = permission_dao.find_by_permission_code(sample_permission.permission_code)
        
        # Then
        assert result is not None
        assert result.permission_code == sample_permission.permission_code
        assert result.id == sample_permission.id
    
    def test_find_by_permission_code_not_found(self, permission_dao):
        """测试根据权限代码查询不存在的权限"""
        # When
        result = permission_dao.find_by_permission_code("nonexistent:permission")
        
        # Then
        assert result is None
    
    def test_find_by_resource_type(self, permission_dao, multiple_permissions):
        """测试根据资源类型查询权限"""
        # When
        result = permission_dao.find_by_resource_type("user")
        
        # Then
        assert len(result) == 4  # user:view, user:create, user:edit, user:delete
        for permission in result:
            assert permission.resource_type == "user"
    
    def test_find_by_action_type(self, permission_dao, multiple_permissions):
        """测试根据操作类型查询权限"""
        # When
        result = permission_dao.find_by_action_type("view")
        
        # Then
        assert len(result) == 1  # user:view
        assert result[0].action_type == "view"
        assert result[0].resource_type == "user"
    
    def test_find_by_resource_action(self, permission_dao, multiple_permissions):
        """测试根据资源和操作类型查询权限"""
        # When
        result = permission_dao.find_by_resource_action("user", "create")
        
        # Then
        assert result is not None
        assert result.resource_type == "user"
        assert result.action_type == "create"
        assert result.permission_code == "user:create"
    
    def test_find_by_resource_action_not_found(self, permission_dao):
        """测试根据资源和操作类型查询不存在的权限"""
        # When
        result = permission_dao.find_by_resource_action("nonexistent", "action")
        
        # Then
        assert result is None
    
    def test_search_permissions(self, permission_dao, multiple_permissions):
        """测试权限搜索功能"""
        # When - 按权限名称搜索
        result1 = permission_dao.search_permissions("用户查看")
        
        # Then
        assert len(result1) == 1
        assert result1[0].permission_name == "用户查看"
        
        # When - 按权限代码搜索
        result2 = permission_dao.search_permissions("user:create")
        
        # Then
        assert len(result2) == 1
        assert result2[0].permission_code == "user:create"
        
        # When - 按资源类型搜索
        result3 = permission_dao.search_permissions("user")
        
        # Then
        assert len(result3) == 4  # 所有user相关权限
        
        # When - 按操作类型搜索
        result4 = permission_dao.search_permissions("create")
        
        # Then
        assert len(result4) == 1
        assert result4[0].action_type == "create"
    
    def test_search_permissions_with_limit(self, permission_dao, multiple_permissions):
        """测试带限制的权限搜索"""
        # When
        result = permission_dao.search_permissions("user", limit=2)
        
        # Then
        assert len(result) == 2
    
    # ==================== 权限关系测试 ====================
    
    def test_get_permission_roles(self, permission_dao, sample_permission, sample_role, sample_role_permission):
        """测试获取拥有权限的角色"""
        # When
        result = permission_dao.get_permission_roles(sample_permission.id)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_role.id
        assert result[0].role_code == sample_role.role_code
    
    def test_get_permission_users(self, permission_dao, sample_permission, sample_role, sample_user,
                                 sample_role_permission, sample_user_role):
        """测试获取拥有权限的用户"""
        # When
        result = permission_dao.get_permission_users(sample_permission.id)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_user.id
        assert result[0].username == sample_user.username
    
    # ==================== 权限分组方法测试 ====================
    
    def test_get_permissions_by_resource(self, permission_dao, multiple_permissions):
        """测试按资源类型分组获取权限"""
        # When
        result = permission_dao.get_permissions_by_resource()
        
        # Then
        assert "user" in result
        assert "system" in result
        assert len(result["user"]) == 4  # user:view, create, edit, delete
        assert len(result["system"]) == 1  # system:config
    
    def test_get_resource_types(self, permission_dao, multiple_permissions):
        """测试获取所有资源类型"""
        # When
        result = permission_dao.get_resource_types()
        
        # Then
        assert "user" in result
        assert "system" in result
        assert len(result) == 2
    
    def test_get_action_types(self, permission_dao, multiple_permissions):
        """测试获取所有操作类型"""
        # When
        result = permission_dao.get_action_types()
        
        # Then
        expected_actions = {"view", "create", "edit", "delete", "config"}
        assert set(result) == expected_actions
    
    def test_get_permission_statistics(self, permission_dao, sample_permission, sample_role, sample_user,
                                      sample_role_permission, sample_user_role):
        """测试获取权限统计信息"""
        # When
        result = permission_dao.get_permission_statistics(sample_permission.id)
        
        # Then
        assert result['permission_id'] == sample_permission.id
        assert result['permission_name'] == sample_permission.permission_name
        assert result['permission_code'] == sample_permission.permission_code
        assert result['resource_type'] == sample_permission.resource_type
        assert result['action_type'] == sample_permission.action_type
        assert result['role_count'] == 1
        assert result['user_count'] == 1
        assert 'is_system_permission' in result
        assert 'is_read_permission' in result
        assert 'is_write_permission' in result
        assert 'created_at' in result
    
    def test_get_permission_statistics_not_found(self, permission_dao):
        """测试获取不存在权限的统计信息"""
        # When & Then
        with pytest.raises(NotFoundError):
            permission_dao.get_permission_statistics(99999)
    
    def test_find_system_permissions(self, permission_dao, multiple_permissions):
        """测试查找系统权限"""
        # When
        result = permission_dao.find_system_permissions()
        
        # Then
        assert len(result) == 1
        assert result[0].resource_type == "system"
        assert result[0].permission_code == "system:config"
    
    def test_find_read_permissions(self, permission_dao, multiple_permissions):
        """测试查找只读权限"""
        # When
        result = permission_dao.find_read_permissions()
        
        # Then
        assert len(result) == 1
        assert result[0].action_type == "view"
        assert result[0].permission_code == "user:view"
    
    def test_find_write_permissions(self, permission_dao, multiple_permissions):
        """测试查找写权限"""
        # When
        result = permission_dao.find_write_permissions()
        
        # Then
        assert len(result) == 3  # create, edit, delete
        action_types = [p.action_type for p in result]
        assert "create" in action_types
        assert "edit" in action_types
        assert "delete" in action_types
    
    # ==================== 异常场景测试 ====================
    
    def test_create_permission_invalid_data(self, permission_dao):
        """测试创建权限无效数据"""
        # Given - 无效权限代码格式
        invalid_permission1 = Permission(
            permission_name="有效名称",
            permission_code="invalid_format",  # 缺少冒号
            resource_type="user",
            action_type="view"
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            permission_dao.create(invalid_permission1)
        
        # Given - 权限代码与资源操作不一致
        invalid_permission2 = Permission(
            permission_name="有效名称",
            permission_code="user:view",
            resource_type="different",  # 与权限代码不一致
            action_type="view"
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            permission_dao.create(invalid_permission2)
    
    def test_operations_with_null_values(self, permission_dao):
        """测试空值处理"""
        # When & Then
        with pytest.raises(ValueError):
            permission_dao.find_by_permission_code("")
        
        with pytest.raises(ValueError):
            permission_dao.find_by_permission_code(None)
        
        with pytest.raises(ValueError):
            permission_dao.find_by_resource_type("")
        
        with pytest.raises(ValueError):
            permission_dao.find_by_action_type(None)
        
        with pytest.raises(ValueError):
            permission_dao.get_permission_roles(0)
        
        with pytest.raises(ValueError):
            permission_dao.get_permission_users(-1)
    
    def test_find_by_resource_action_invalid_input(self, permission_dao):
        """测试根据资源和操作查询无效输入"""
        # When & Then
        with pytest.raises(ValueError):
            permission_dao.find_by_resource_action("", "view")
        
        with pytest.raises(ValueError):
            permission_dao.find_by_resource_action("user", "")
        
        with pytest.raises(ValueError):
            permission_dao.find_by_resource_action(None, "view")
        
        with pytest.raises(ValueError):
            permission_dao.find_by_resource_action("user", None)
    
    def test_search_permissions_invalid_keyword(self, permission_dao):
        """测试搜索权限无效关键词"""
        # When & Then
        with pytest.raises(ValueError):
            permission_dao.search_permissions("")
        
        with pytest.raises(ValueError):
            permission_dao.search_permissions(None)
        
        with pytest.raises(ValueError):
            permission_dao.search_permissions(123)
    
    def test_get_statistics_invalid_id(self, permission_dao):
        """测试获取统计信息无效ID"""
        # When & Then
        with pytest.raises(ValueError):
            permission_dao.get_permission_statistics(0)
        
        with pytest.raises(ValueError):
            permission_dao.get_permission_statistics(-1)
        
        with pytest.raises(ValueError):
            permission_dao.get_permission_statistics(None)
    
    @patch('dao.permission_dao.PermissionDao.session')
    def test_database_connection_error(self, mock_session, permission_dao):
        """测试数据库连接异常"""
        # Given
        mock_session.query.side_effect = SQLAlchemyError("Connection failed")
        
        # When & Then
        with pytest.raises(DatabaseError):
            permission_dao.find_by_id(1)
    
    def test_permission_code_validation(self, permission_dao):
        """测试权限代码验证"""
        # Given - 权限代码太短
        invalid_permission1 = Permission(
            permission_name="测试",
            permission_code="a:b",  # 太短
            resource_type="a",
            action_type="b"
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            permission_dao.create(invalid_permission1)
        
        # Given - 权限代码太长
        long_code = "a" * 30 + ":" + "b" * 30  # 超过64字符
        invalid_permission2 = Permission(
            permission_name="测试",
            permission_code=long_code,
            resource_type="a" * 30,
            action_type="b" * 30
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            permission_dao.create(invalid_permission2)
