#!/usr/bin/env python3
"""
RBAC权限系统 - 数据库初始化脚本

创建所有必要的数据库表，插入基础数据，创建索引。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models.base_model import Base, db_config
from models.user import User
from models.role import Role
from models.permission import Permission
from models.user_role import UserRole
from models.role_permission import RolePermission
from utils.password_utils import PasswordUtils


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self):
        self.database_url = db_config.database_url
        self.engine = db_config.engine
        self.SessionLocal = db_config.SessionLocal
        self.password_utils = PasswordUtils()
        
    def initialize_database(self):
        """初始化数据库"""
        print("🚀 开始初始化RBAC权限系统数据库...")
        print("=" * 60)
        
        try:
            # 1. 创建所有表
            self._create_tables()
            
            # 2. 创建索引
            self._create_indexes()
            
            # 3. 插入基础数据
            self._insert_base_data()
            
            print("\n" + "=" * 60)
            print("✅ 数据库初始化完成！")
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {str(e)}")
            raise
    
    def _create_tables(self):
        """创建所有表"""
        print("\n📋 创建数据库表...")
        
        # 创建所有表
        Base.metadata.create_all(bind=self.engine)
        
        # 验证表是否创建成功
        with self.engine.connect() as conn:
            # 检查SQLite表
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['users', 'roles', 'permissions', 'user_roles', 'role_permissions']
            
            for table in expected_tables:
                if table in tables:
                    print(f"  ✅ {table} 表创建成功")
                else:
                    print(f"  ❌ {table} 表创建失败")
                    
        print("📋 数据库表创建完成")
    
    def _create_indexes(self):
        """创建索引"""
        print("\n🔍 创建数据库索引...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
            "CREATE INDEX IF NOT EXISTS idx_roles_code ON roles(role_code)",
            "CREATE INDEX IF NOT EXISTS idx_roles_status ON roles(status)",
            "CREATE INDEX IF NOT EXISTS idx_permissions_code ON permissions(permission_code)",
            "CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource_type)",
            "CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_roles_status ON user_roles(status)",
            "CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON role_permissions(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id ON role_permissions(permission_id)",
            "CREATE INDEX IF NOT EXISTS idx_role_permissions_status ON role_permissions(status)"
        ]
        
        with self.engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    index_name = index_sql.split()[5]  # 提取索引名
                    print(f"  ✅ {index_name} 索引创建成功")
                except Exception as e:
                    print(f"  ❌ 索引创建失败: {str(e)}")
            
            conn.commit()
        
        print("🔍 数据库索引创建完成")
    
    def _insert_base_data(self):
        """插入基础数据"""
        print("\n📝 插入基础数据...")
        
        session = self.SessionLocal()
        try:
            # 1. 创建基础权限
            permissions = self._create_base_permissions(session)
            
            # 2. 创建基础角色
            roles = self._create_base_roles(session)
            
            # 3. 分配角色权限
            self._assign_role_permissions(session, roles, permissions)
            
            # 4. 创建默认管理员用户
            admin_user = self._create_admin_user(session)
            
            # 5. 分配用户角色
            self._assign_user_roles(session, admin_user, roles)
            
            session.commit()
            print("📝 基础数据插入完成")
            
        except Exception as e:
            session.rollback()
            print(f"❌ 基础数据插入失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def _create_base_permissions(self, session):
        """创建基础权限"""
        print("  创建基础权限...")
        
        base_permissions = [
            # 用户管理权限
            ("查看用户", "user:view", "user", "view", "查看用户信息的权限"),
            ("创建用户", "user:create", "user", "create", "创建新用户的权限"),
            ("编辑用户", "user:edit", "user", "edit", "编辑用户信息的权限"),
            ("删除用户", "user:delete", "user", "delete", "删除用户的权限"),
            
            # 角色管理权限
            ("查看角色", "role:view", "role", "view", "查看角色信息的权限"),
            ("创建角色", "role:create", "role", "create", "创建新角色的权限"),
            ("编辑角色", "role:edit", "role", "edit", "编辑角色信息的权限"),
            ("删除角色", "role:delete", "role", "delete", "删除角色的权限"),
            
            # 权限管理权限
            ("查看权限", "permission:view", "permission", "view", "查看权限信息的权限"),
            ("创建权限", "permission:create", "permission", "create", "创建新权限的权限"),
            ("编辑权限", "permission:edit", "permission", "edit", "编辑权限信息的权限"),
            ("删除权限", "permission:delete", "permission", "delete", "删除权限的权限"),
            
            # 系统管理权限
            ("系统管理", "system:admin", "system", "admin", "系统管理员权限"),
            ("管理员所有权限", "admin:*", "admin", "*", "管理员拥有所有权限")
        ]
        
        permissions = {}
        for name, code, resource, action, desc in base_permissions:
            # 检查权限是否已存在
            existing = session.query(Permission).filter_by(permission_code=code).first()
            if not existing:
                permission = Permission(
                    permission_name=name,
                    permission_code=code,
                    resource_type=resource,
                    action_type=action,
                    description=desc,
                    status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(permission)
                session.flush()  # 获取ID
                permissions[code] = permission
                print(f"    ✅ 权限 {name} ({code}) 创建成功")
            else:
                permissions[code] = existing
                print(f"    ℹ️  权限 {name} ({code}) 已存在")
        
        return permissions
    
    def _create_base_roles(self, session):
        """创建基础角色"""
        print("  创建基础角色...")
        
        base_roles = [
            ("系统管理员", "admin", "系统管理员角色，拥有所有权限"),
            ("普通用户", "user", "普通用户角色，拥有基础权限"),
            ("访客", "guest", "访客角色，只有查看权限")
        ]
        
        roles = {}
        for name, code, desc in base_roles:
            # 检查角色是否已存在
            existing = session.query(Role).filter_by(role_code=code).first()
            if not existing:
                role = Role(
                    role_name=name,
                    role_code=code,
                    description=desc,
                    status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(role)
                session.flush()  # 获取ID
                roles[code] = role
                print(f"    ✅ 角色 {name} ({code}) 创建成功")
            else:
                roles[code] = existing
                print(f"    ℹ️  角色 {name} ({code}) 已存在")
        
        return roles
    
    def _assign_role_permissions(self, session, roles, permissions):
        """分配角色权限"""
        print("  分配角色权限...")
        
        # 管理员角色拥有所有权限
        admin_role = roles['admin']
        for perm_code, permission in permissions.items():
            existing = session.query(RolePermission).filter_by(
                role_id=admin_role.id, 
                permission_id=permission.id
            ).first()
            
            if not existing:
                role_perm = RolePermission(
                    role_id=admin_role.id,
                    permission_id=permission.id,
                    granted_by=1,  # 系统自动分配
                    status=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(role_perm)
        
        # 普通用户角色拥有查看权限
        user_role = roles['user']
        view_permissions = ['user:view', 'role:view', 'permission:view']
        for perm_code in view_permissions:
            if perm_code in permissions:
                permission = permissions[perm_code]
                existing = session.query(RolePermission).filter_by(
                    role_id=user_role.id, 
                    permission_id=permission.id
                ).first()
                
                if not existing:
                    role_perm = RolePermission(
                        role_id=user_role.id,
                        permission_id=permission.id,
                        granted_by=1,
                        status=1,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(role_perm)
        
        # 访客角色只有基础查看权限
        guest_role = roles['guest']
        guest_permissions = ['user:view']
        for perm_code in guest_permissions:
            if perm_code in permissions:
                permission = permissions[perm_code]
                existing = session.query(RolePermission).filter_by(
                    role_id=guest_role.id, 
                    permission_id=permission.id
                ).first()
                
                if not existing:
                    role_perm = RolePermission(
                        role_id=guest_role.id,
                        permission_id=permission.id,
                        granted_by=1,
                        status=1,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(role_perm)
        
        print("    ✅ 角色权限分配完成")
    
    def _create_admin_user(self, session):
        """创建默认管理员用户"""
        print("  创建默认管理员用户...")
        
        # 检查管理员是否已存在
        existing = session.query(User).filter_by(username='admin').first()
        if existing:
            print("    ℹ️  管理员用户已存在")
            return existing
        
        # 创建管理员用户
        password_hash = self.password_utils.hash_password('Admin123!')
        admin_user = User(
            username='admin',
            email='admin@rbac-system.com',
            password_hash=password_hash,
            nickname='系统管理员',
            phone='13800138000',
            status=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        session.add(admin_user)
        session.flush()  # 获取ID
        
        print("    ✅ 管理员用户创建成功")
        print("    📋 默认管理员账号信息:")
        print("       用户名: admin")
        print("       密码: Admin123!")
        print("       邮箱: admin@rbac-system.com")
        
        return admin_user
    
    def _assign_user_roles(self, session, user, roles):
        """分配用户角色"""
        print("  分配用户角色...")
        
        # 给管理员用户分配管理员角色
        admin_role = roles['admin']
        existing = session.query(UserRole).filter_by(
            user_id=user.id, 
            role_id=admin_role.id
        ).first()
        
        if not existing:
            user_role = UserRole(
                user_id=user.id,
                role_id=admin_role.id,
                assigned_by=1,  # 系统自动分配
                status=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(user_role)
            print("    ✅ 管理员角色分配完成")
        else:
            print("    ℹ️  管理员角色已分配")


def main():
    """主函数"""
    try:
        initializer = DatabaseInitializer()
        initializer.initialize_database()
        
        print("\n🎉 数据库初始化成功完成！")
        print("\n📋 初始化内容:")
        print("  ✅ 创建了5个数据库表")
        print("  ✅ 创建了13个数据库索引")
        print("  ✅ 插入了14个基础权限")
        print("  ✅ 创建了3个基础角色")
        print("  ✅ 配置了角色权限关系")
        print("  ✅ 创建了默认管理员用户")
        print("\n🚀 系统已准备就绪，可以开始使用！")
        
    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
