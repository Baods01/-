"""
pytest测试配置文件

本模块提供pytest测试的全局配置、夹具和测试环境设置。

Fixtures:
    db_session: 数据库会话夹具
    test_engine: 测试数据库引擎夹具
    sample_user: 示例用户夹具
    sample_role: 示例角色夹具
    sample_permission: 示例权限夹具

Author: AI Assistant
Created: 2025-07-19
"""

import pytest
import logging
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models.base_model import Base
from models.user import User
from models.role import Role
from models.permission import Permission
from models.user_role import UserRole
from models.role_permission import RolePermission

# 配置测试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_engine():
    """
    创建测试数据库引擎
    
    使用内存SQLite数据库进行测试，每个测试会话创建一次
    
    Returns:
        Engine: SQLAlchemy数据库引擎
    """
    # 使用内存SQLite数据库
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,  # 设置为True可以看到SQL语句
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        }
    )
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    logger.info("测试数据库引擎创建成功")
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    创建数据库会话夹具
    
    每个测试函数都会获得一个独立的数据库会话，测试结束后自动回滚
    
    Args:
        test_engine: 测试数据库引擎
        
    Yields:
        Session: 数据库会话
    """
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    
    # 开始事务
    transaction = session.begin()
    
    try:
        yield session
    finally:
        # 测试结束后回滚事务，确保测试数据不会影响其他测试
        transaction.rollback()
        session.close()
        logger.debug("测试会话已关闭，事务已回滚")


@pytest.fixture
def sample_user(db_session) -> User:
    """
    创建示例用户夹具
    
    Args:
        db_session: 数据库会话
        
    Returns:
        User: 示例用户对象
    """
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq/3Hm.",  # "password123"的bcrypt哈希
        status=1
    )
    db_session.add(user)
    db_session.flush()  # 获取生成的ID
    return user


@pytest.fixture
def sample_role(db_session) -> Role:
    """
    创建示例角色夹具
    
    Args:
        db_session: 数据库会话
        
    Returns:
        Role: 示例角色对象
    """
    role = Role(
        role_name="测试角色",
        role_code="test_role",
        status=1
    )
    db_session.add(role)
    db_session.flush()  # 获取生成的ID
    return role


@pytest.fixture
def sample_permission(db_session) -> Permission:
    """
    创建示例权限夹具
    
    Args:
        db_session: 数据库会话
        
    Returns:
        Permission: 示例权限对象
    """
    permission = Permission(
        permission_name="测试权限",
        permission_code="test:view",
        resource_type="test",
        action_type="view"
    )
    db_session.add(permission)
    db_session.flush()  # 获取生成的ID
    return permission


@pytest.fixture
def sample_user_role(db_session, sample_user, sample_role) -> UserRole:
    """
    创建示例用户角色关联夹具
    
    Args:
        db_session: 数据库会话
        sample_user: 示例用户
        sample_role: 示例角色
        
    Returns:
        UserRole: 示例用户角色关联对象
    """
    user_role = UserRole(
        user_id=sample_user.id,
        role_id=sample_role.id,
        assigned_at=datetime.utcnow(),
        status=1
    )
    db_session.add(user_role)
    db_session.flush()
    return user_role


@pytest.fixture
def sample_role_permission(db_session, sample_role, sample_permission) -> RolePermission:
    """
    创建示例角色权限关联夹具
    
    Args:
        db_session: 数据库会话
        sample_role: 示例角色
        sample_permission: 示例权限
        
    Returns:
        RolePermission: 示例角色权限关联对象
    """
    role_permission = RolePermission(
        role_id=sample_role.id,
        permission_id=sample_permission.id,
        granted_at=datetime.utcnow(),
        status=1
    )
    db_session.add(role_permission)
    db_session.flush()
    return role_permission


@pytest.fixture
def multiple_users(db_session) -> list[User]:
    """
    创建多个用户夹具
    
    Args:
        db_session: 数据库会话
        
    Returns:
        list[User]: 用户列表
    """
    users = []
    for i in range(3):
        user = User(
            username=f"user{i+1}",
            email=f"user{i+1}@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq/3Hm.",
            status=1 if i < 2 else 0  # 前两个用户启用，第三个禁用
        )
        db_session.add(user)
        users.append(user)
    
    db_session.flush()
    return users


@pytest.fixture
def multiple_roles(db_session) -> list[Role]:
    """
    创建多个角色夹具
    
    Args:
        db_session: 数据库会话
        
    Returns:
        list[Role]: 角色列表
    """
    roles = []
    role_data = [
        ("管理员", "admin"),
        ("编辑者", "editor"),
        ("查看者", "viewer")
    ]
    
    for name, code in role_data:
        role = Role(
            role_name=name,
            role_code=code,
            status=1
        )
        db_session.add(role)
        roles.append(role)
    
    db_session.flush()
    return roles


@pytest.fixture
def multiple_permissions(db_session) -> list[Permission]:
    """
    创建多个权限夹具
    
    Args:
        db_session: 数据库会话
        
    Returns:
        list[Permission]: 权限列表
    """
    permissions = []
    permission_data = [
        ("用户查看", "user:view", "user", "view"),
        ("用户创建", "user:create", "user", "create"),
        ("用户编辑", "user:edit", "user", "edit"),
        ("用户删除", "user:delete", "user", "delete"),
        ("系统配置", "system:config", "system", "config")
    ]
    
    for name, code, resource, action in permission_data:
        permission = Permission(
            permission_name=name,
            permission_code=code,
            resource_type=resource,
            action_type=action
        )
        db_session.add(permission)
        permissions.append(permission)
    
    db_session.flush()
    return permissions


# pytest配置
def pytest_configure(config):
    """pytest配置函数"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# 测试会话钩子
def pytest_sessionstart(session):
    """测试会话开始时的钩子"""
    logger.info("开始RBAC系统单元测试")


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的钩子"""
    logger.info(f"RBAC系统单元测试结束，退出状态: {exitstatus}")


# 测试失败时的钩子
def pytest_runtest_logreport(report):
    """测试运行报告钩子"""
    if report.failed:
        logger.error(f"测试失败: {report.nodeid}")
        if hasattr(report, 'longrepr'):
            logger.error(f"失败原因: {report.longrepr}")


# 自定义断言帮助函数
def assert_user_equal(user1: User, user2: User, exclude_fields: list = None):
    """
    断言两个用户对象相等
    
    Args:
        user1: 第一个用户对象
        user2: 第二个用户对象
        exclude_fields: 要排除比较的字段列表
    """
    exclude_fields = exclude_fields or []
    
    if 'id' not in exclude_fields:
        assert user1.id == user2.id
    if 'username' not in exclude_fields:
        assert user1.username == user2.username
    if 'email' not in exclude_fields:
        assert user1.email == user2.email
    if 'status' not in exclude_fields:
        assert user1.status == user2.status


def assert_role_equal(role1: Role, role2: Role, exclude_fields: list = None):
    """
    断言两个角色对象相等
    
    Args:
        role1: 第一个角色对象
        role2: 第二个角色对象
        exclude_fields: 要排除比较的字段列表
    """
    exclude_fields = exclude_fields or []
    
    if 'id' not in exclude_fields:
        assert role1.id == role2.id
    if 'role_name' not in exclude_fields:
        assert role1.role_name == role2.role_name
    if 'role_code' not in exclude_fields:
        assert role1.role_code == role2.role_code
    if 'status' not in exclude_fields:
        assert role1.status == role2.status


def assert_permission_equal(permission1: Permission, permission2: Permission, exclude_fields: list = None):
    """
    断言两个权限对象相等
    
    Args:
        permission1: 第一个权限对象
        permission2: 第二个权限对象
        exclude_fields: 要排除比较的字段列表
    """
    exclude_fields = exclude_fields or []
    
    if 'id' not in exclude_fields:
        assert permission1.id == permission2.id
    if 'permission_name' not in exclude_fields:
        assert permission1.permission_name == permission2.permission_name
    if 'permission_code' not in exclude_fields:
        assert permission1.permission_code == permission2.permission_code
    if 'resource_type' not in exclude_fields:
        assert permission1.resource_type == permission2.resource_type
    if 'action_type' not in exclude_fields:
        assert permission1.action_type == permission2.action_type
