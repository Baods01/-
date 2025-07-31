-- =====================================================
-- RBAC权限系统优化数据库设计
-- 数据库：MySQL 8.0+
-- 字符集：utf8mb4
-- 优化时间：2025-07-17
-- =====================================================

-- 设置数据库字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS rbac_system 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

USE rbac_system;

-- =====================================================
-- 1. 用户表 (users) - 优化版
-- 存储用户基本信息，添加密码字段
-- =====================================================
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(32) NOT NULL COMMENT '用户名',
    email VARCHAR(64) NOT NULL COMMENT '邮箱地址',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值(bcrypt)',
    status TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：1=启用，0=禁用',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    KEY idx_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- =====================================================
-- 2. 角色表 (roles) - 优化版
-- 定义系统角色
-- =====================================================
DROP TABLE IF EXISTS roles;
CREATE TABLE roles (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '角色ID',
    role_name VARCHAR(32) NOT NULL COMMENT '角色名称',
    role_code VARCHAR(32) NOT NULL COMMENT '角色代码',
    status TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：1=启用，0=禁用',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_role_code (role_code),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- =====================================================
-- 3. 权限表 (permissions) - 优化版
-- 定义系统权限
-- =====================================================
DROP TABLE IF EXISTS permissions;
CREATE TABLE permissions (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '权限ID',
    permission_name VARCHAR(64) NOT NULL COMMENT '权限名称',
    permission_code VARCHAR(64) NOT NULL COMMENT '权限代码',
    resource_type VARCHAR(32) NOT NULL COMMENT '资源类型',
    action_type VARCHAR(16) NOT NULL COMMENT '操作类型',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_permission_code (permission_code),
    KEY idx_resource_action (resource_type, action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- =====================================================
-- 4. 用户角色关联表 (user_roles) - 优化版
-- 用户与角色的多对多关系
-- =====================================================
DROP TABLE IF EXISTS user_roles;
CREATE TABLE user_roles (
    user_id INT UNSIGNED NOT NULL COMMENT '用户ID',
    role_id SMALLINT UNSIGNED NOT NULL COMMENT '角色ID',
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    assigned_by INT UNSIGNED COMMENT '分配人ID',
    status TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：1=启用，0=禁用',
    
    PRIMARY KEY (user_id, role_id),
    KEY idx_role_id (role_id),
    KEY idx_assigned_by (assigned_by),
    KEY idx_status_assigned (status, assigned_at),
    
    CONSTRAINT fk_user_roles_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role_id FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_assigned_by FOREIGN KEY (assigned_by) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- =====================================================
-- 5. 角色权限关联表 (role_permissions) - 优化版
-- 角色与权限的多对多关系
-- =====================================================
DROP TABLE IF EXISTS role_permissions;
CREATE TABLE role_permissions (
    role_id SMALLINT UNSIGNED NOT NULL COMMENT '角色ID',
    permission_id SMALLINT UNSIGNED NOT NULL COMMENT '权限ID',
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    granted_by INT UNSIGNED COMMENT '授权人ID',
    status TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '状态：1=启用，0=禁用',
    
    PRIMARY KEY (role_id, permission_id),
    KEY idx_permission_id (permission_id),
    KEY idx_granted_by (granted_by),
    KEY idx_status_granted (status, granted_at),
    
    CONSTRAINT fk_role_permissions_role_id FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_permission_id FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_granted_by FOREIGN KEY (granted_by) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- =====================================================
-- 插入初始数据示例
-- =====================================================

-- 插入系统管理员用户（密码：password123，已加密）
INSERT INTO users (username, email, password_hash, status) VALUES 
('admin', 'admin@system.com', '$2b$12$placeholder_hash_will_be_generated_by_python', 1),
('system', 'system@system.com', '$2b$12$placeholder_hash_will_be_generated_by_python', 1);

-- 插入基础角色
INSERT INTO roles (role_name, role_code, status) VALUES 
('超级管理员', 'super_admin', 1),
('系统管理员', 'admin', 1),
('普通用户', 'user', 1);

-- 插入基础权限
INSERT INTO permissions (permission_name, permission_code, resource_type, action_type) VALUES 
('用户管理-查看', 'user:view', 'user', 'view'),
('用户管理-创建', 'user:create', 'user', 'create'),
('用户管理-编辑', 'user:edit', 'user', 'edit'),
('用户管理-删除', 'user:delete', 'user', 'delete'),
('角色管理-查看', 'role:view', 'role', 'view'),
('角色管理-创建', 'role:create', 'role', 'create'),
('角色管理-编辑', 'role:edit', 'role', 'edit'),
('角色管理-删除', 'role:delete', 'role', 'delete'),
('权限管理-查看', 'permission:view', 'permission', 'view'),
('系统设置-查看', 'system:view', 'system', 'view'),
('系统设置-编辑', 'system:edit', 'system', 'edit');

-- 设置外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 优化数据库设计完成
-- =====================================================
