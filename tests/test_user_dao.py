"""
用户DAO单元测试

本模块包含UserDao类的完整单元测试，覆盖所有CRUD操作和业务方法的正常流程和异常流程。

Test Class:
    TestUserDao: 用户DAO测试类

Author: AI Assistant
Created: 2025-07-19
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from dao.user_dao import UserDao
from dao.base_dao import DatabaseError, ValidationError, NotFoundError
from models.user import User
from models.role import Role
from models.permission import Permission
from models.user_role import UserRole
from models.role_permission import RolePermission


class TestUserDao:
    """用户DAO测试类"""
    
    @pytest.fixture
    def user_dao(self, db_session):
        """创建UserDao实例"""
        return UserDao(db_session)
    
    # ==================== 基础CRUD操作测试 ====================
    
    def test_create_user_success(self, user_dao, db_session):
        """测试创建用户成功"""
        # Given
        user = User(
            username="newuser",
            email="newuser@example.com",
            password_hash="hashed_password",
            status=1
        )
        
        # When
        result = user_dao.create(user)
        
        # Then
        assert result is not None
        assert result.id is not None
        assert result.username == "newuser"
        assert result.email == "newuser@example.com"
        assert result.status == 1
        assert result.created_at is not None
        assert result.updated_at is not None
    
    def test_create_user_duplicate_username(self, user_dao, sample_user):
        """测试用户名重复异常"""
        # Given
        duplicate_user = User(
            username=sample_user.username,  # 重复用户名
            email="different@example.com",
            password_hash="hashed_password",
            status=1
        )
        
        # When & Then
        with pytest.raises(DatabaseError):
            user_dao.create(duplicate_user)
    
    def test_create_user_duplicate_email(self, user_dao, sample_user):
        """测试邮箱重复异常"""
        # Given
        duplicate_user = User(
            username="differentuser",
            email=sample_user.email,  # 重复邮箱
            password_hash="hashed_password",
            status=1
        )
        
        # When & Then
        with pytest.raises(DatabaseError):
            user_dao.create(duplicate_user)
    
    def test_find_by_id_success(self, user_dao, sample_user):
        """测试根据ID查询成功"""
        # When
        result = user_dao.find_by_id(sample_user.id)
        
        # Then
        assert result is not None
        assert result.id == sample_user.id
        assert result.username == sample_user.username
        assert result.email == sample_user.email
    
    def test_find_by_id_not_found(self, user_dao):
        """测试查询不存在的用户"""
        # When
        result = user_dao.find_by_id(99999)
        
        # Then
        assert result is None
    
    def test_find_by_id_invalid_id(self, user_dao):
        """测试无效ID"""
        # When & Then
        with pytest.raises(ValueError):
            user_dao.find_by_id(0)
        
        with pytest.raises(ValueError):
            user_dao.find_by_id(-1)
        
        with pytest.raises(ValueError):
            user_dao.find_by_id(None)
    
    def test_find_all_success(self, user_dao, multiple_users):
        """测试查询所有用户"""
        # When
        result = user_dao.find_all()
        
        # Then
        assert len(result) == 3
        usernames = [user.username for user in result]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames
    
    def test_update_user_success(self, user_dao, sample_user):
        """测试更新用户成功"""
        # Given
        original_updated_at = sample_user.updated_at
        sample_user.username = "updated_user"
        sample_user.email = "updated@example.com"
        
        # When
        result = user_dao.update(sample_user)
        
        # Then
        assert result.username == "updated_user"
        assert result.email == "updated@example.com"
        assert result.updated_at > original_updated_at
    
    def test_update_user_not_found(self, user_dao):
        """测试更新不存在的用户"""
        # Given
        non_existent_user = User(
            id=99999,
            username="nonexistent",
            email="nonexistent@example.com",
            password_hash="hashed_password",
            status=1
        )
        
        # When & Then
        with pytest.raises(NotFoundError):
            user_dao.update(non_existent_user)
    
    def test_delete_by_id_success(self, user_dao, sample_user):
        """测试删除用户成功"""
        # When
        result = user_dao.delete_by_id(sample_user.id)
        
        # Then
        assert result is True
        
        # 验证用户已被删除
        deleted_user = user_dao.find_by_id(sample_user.id)
        assert deleted_user is None
    
    def test_delete_by_id_not_found(self, user_dao):
        """测试删除不存在的用户"""
        # When
        result = user_dao.delete_by_id(99999)
        
        # Then
        assert result is False
    
    # ==================== 用户特有方法测试 ====================
    
    def test_find_by_username_success(self, user_dao, sample_user):
        """测试根据用户名查询成功"""
        # When
        result = user_dao.find_by_username(sample_user.username)
        
        # Then
        assert result is not None
        assert result.username == sample_user.username
        assert result.id == sample_user.id
    
    def test_find_by_username_not_found(self, user_dao):
        """测试根据用户名查询不存在的用户"""
        # When
        result = user_dao.find_by_username("nonexistent")
        
        # Then
        assert result is None
    
    def test_find_by_username_invalid_input(self, user_dao):
        """测试无效用户名输入"""
        # When & Then
        with pytest.raises(ValueError):
            user_dao.find_by_username("")
        
        with pytest.raises(ValueError):
            user_dao.find_by_username(None)
        
        with pytest.raises(ValueError):
            user_dao.find_by_username(123)
    
    def test_find_by_email_success(self, user_dao, sample_user):
        """测试根据邮箱查询成功"""
        # When
        result = user_dao.find_by_email(sample_user.email)
        
        # Then
        assert result is not None
        assert result.email == sample_user.email
        assert result.id == sample_user.id
    
    def test_find_by_email_not_found(self, user_dao):
        """测试根据邮箱查询不存在的用户"""
        # When
        result = user_dao.find_by_email("nonexistent@example.com")
        
        # Then
        assert result is None
    
    def test_find_active_users(self, user_dao, multiple_users):
        """测试查询启用用户"""
        # When
        result = user_dao.find_active_users()
        
        # Then
        assert len(result) == 2  # 只有前两个用户是启用的
        for user in result:
            assert user.status == 1
    
    def test_find_by_status(self, user_dao, multiple_users):
        """测试根据状态查询用户"""
        # When - 查询启用用户
        active_users = user_dao.find_by_status(1)
        
        # Then
        assert len(active_users) == 2
        for user in active_users:
            assert user.status == 1
        
        # When - 查询禁用用户
        inactive_users = user_dao.find_by_status(0)
        
        # Then
        assert len(inactive_users) == 1
        assert inactive_users[0].status == 0
    
    def test_find_by_status_invalid_status(self, user_dao):
        """测试无效状态参数"""
        # When & Then
        with pytest.raises(ValueError):
            user_dao.find_by_status(2)
        
        with pytest.raises(ValueError):
            user_dao.find_by_status(-1)
    
    def test_search_users(self, user_dao, multiple_users):
        """测试用户搜索功能"""
        # When - 按用户名搜索
        result1 = user_dao.search_users("user1")
        
        # Then
        assert len(result1) == 1
        assert result1[0].username == "user1"
        
        # When - 按邮箱搜索
        result2 = user_dao.search_users("user2@example.com")
        
        # Then
        assert len(result2) == 1
        assert result2[0].email == "user2@example.com"
        
        # When - 模糊搜索
        result3 = user_dao.search_users("user")
        
        # Then
        assert len(result3) == 3  # 所有用户都包含"user"
    
    def test_search_users_with_limit(self, user_dao, multiple_users):
        """测试带限制的用户搜索"""
        # When
        result = user_dao.search_users("user", limit=2)
        
        # Then
        assert len(result) == 2
    
    def test_search_users_invalid_keyword(self, user_dao):
        """测试无效搜索关键词"""
        # When & Then
        with pytest.raises(ValueError):
            user_dao.search_users("")
        
        with pytest.raises(ValueError):
            user_dao.search_users(None)
    
    # ==================== 用户角色权限测试 ====================
    
    def test_get_user_roles(self, user_dao, sample_user, sample_role, sample_user_role):
        """测试获取用户角色"""
        # When
        result = user_dao.get_user_roles(sample_user.id)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_role.id
        assert result[0].role_code == sample_role.role_code
    
    def test_get_user_permissions(self, user_dao, sample_user, sample_role, sample_permission, 
                                 sample_user_role, sample_role_permission):
        """测试获取用户权限"""
        # When
        result = user_dao.get_user_permissions(sample_user.id)
        
        # Then
        assert len(result) == 1
        assert result[0].id == sample_permission.id
        assert result[0].permission_code == sample_permission.permission_code
    
    def test_has_role(self, user_dao, sample_user, sample_role, sample_user_role):
        """测试检查用户角色"""
        # When & Then
        assert user_dao.has_role(sample_user.id, sample_role.role_code) is True
        assert user_dao.has_role(sample_user.id, "nonexistent_role") is False
    
    def test_has_permission(self, user_dao, sample_user, sample_role, sample_permission,
                           sample_user_role, sample_role_permission):
        """测试检查用户权限"""
        # When & Then
        assert user_dao.has_permission(sample_user.id, sample_permission.permission_code) is True
        assert user_dao.has_permission(sample_user.id, "nonexistent:permission") is False
    
    # ==================== 用户管理方法测试 ====================
    
    def test_activate_user(self, user_dao, db_session):
        """测试启用用户"""
        # Given - 创建禁用用户
        user = User(
            username="inactive_user",
            email="inactive@example.com",
            password_hash="hashed_password",
            status=0
        )
        db_session.add(user)
        db_session.flush()
        
        # When
        result = user_dao.activate_user(user.id)
        
        # Then
        assert result is True
        updated_user = user_dao.find_by_id(user.id)
        assert updated_user.status == 1
    
    def test_activate_user_not_found(self, user_dao):
        """测试启用不存在的用户"""
        # When
        result = user_dao.activate_user(99999)
        
        # Then
        assert result is False
    
    def test_deactivate_user(self, user_dao, sample_user):
        """测试禁用用户"""
        # When
        result = user_dao.deactivate_user(sample_user.id)
        
        # Then
        assert result is True
        updated_user = user_dao.find_by_id(sample_user.id)
        assert updated_user.status == 0
    
    def test_update_password(self, user_dao, sample_user):
        """测试更新用户密码"""
        # Given
        new_password_hash = "new_hashed_password"
        
        # When
        result = user_dao.update_password(sample_user.id, new_password_hash)
        
        # Then
        assert result is True
        updated_user = user_dao.find_by_id(sample_user.id)
        assert updated_user.password_hash == new_password_hash
    
    def test_update_password_invalid_input(self, user_dao, sample_user):
        """测试更新密码无效输入"""
        # When & Then
        with pytest.raises(ValueError):
            user_dao.update_password(sample_user.id, "")
        
        with pytest.raises(ValueError):
            user_dao.update_password(sample_user.id, None)
        
        with pytest.raises(ValueError):
            user_dao.update_password(0, "valid_hash")
    
    # ==================== 异常场景测试 ====================
    
    def test_create_user_invalid_data(self, user_dao):
        """测试创建用户无效数据"""
        # Given - 无效用户名
        invalid_user1 = User(
            username="ab",  # 用户名太短
            email="test@example.com",
            password_hash="hashed_password",
            status=1
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            user_dao.create(invalid_user1)
        
        # Given - 无效邮箱
        invalid_user2 = User(
            username="validuser",
            email="invalid-email",  # 无效邮箱格式
            password_hash="hashed_password",
            status=1
        )
        
        # When & Then
        with pytest.raises(ValidationError):
            user_dao.create(invalid_user2)
    
    def test_operations_with_null_values(self, user_dao):
        """测试空值处理"""
        # When & Then
        with pytest.raises(ValueError):
            user_dao.get_user_roles(None)
        
        with pytest.raises(ValueError):
            user_dao.has_role(None, "admin")
        
        with pytest.raises(ValueError):
            user_dao.has_permission(1, None)
    
    @patch('dao.user_dao.UserDao.session')
    def test_database_connection_error(self, mock_session, user_dao):
        """测试数据库连接异常"""
        # Given
        mock_session.query.side_effect = SQLAlchemyError("Connection failed")
        
        # When & Then
        with pytest.raises(DatabaseError):
            user_dao.find_by_id(1)
