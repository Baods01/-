# RBAC权限系统数据库设计文档

## 概述
本文档描述了基于角色的访问控制（RBAC）权限系统的数据库设计。该设计遵循RBAC标准模型，包含用户、角色、权限三个核心实体及其关联关系。

## 设计原则
- **标准化**：遵循RBAC标准模型设计
- **可扩展性**：支持未来功能扩展
- **性能优化**：合理的索引设计
- **数据完整性**：完善的约束和外键关系
- **审计追踪**：包含时间戳和操作人信息

## 技术规范
- **数据库**：MySQL 8.0+
- **字符集**：utf8mb4_unicode_ci
- **存储引擎**：InnoDB
- **主键策略**：BIGINT UNSIGNED AUTO_INCREMENT
- **时间戳**：TIMESTAMP类型，自动维护

## 数据表设计

### 1. 用户表 (users)
**用途**：存储系统用户的基本信息

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY, AUTO_INCREMENT | 用户唯一标识 |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名，登录凭证 |
| email | VARCHAR(100) | NOT NULL, UNIQUE | 邮箱地址，登录凭证 |
| status | TINYINT | NOT NULL, DEFAULT 1 | 用户状态：1=启用，0=禁用 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- 主键索引：id
- 唯一索引：username, email
- 普通索引：status, created_at

### 2. 角色表 (roles)
**用途**：定义系统中的各种角色

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY, AUTO_INCREMENT | 角色唯一标识 |
| role_name | VARCHAR(50) | NOT NULL | 角色显示名称 |
| role_code | VARCHAR(50) | NOT NULL, UNIQUE | 角色代码，程序中使用 |
| status | TINYINT | NOT NULL, DEFAULT 1 | 角色状态：1=启用，0=禁用 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引设计**：
- 主键索引：id
- 唯一索引：role_code
- 普通索引：role_name, status, created_at

### 3. 权限表 (permissions)
**用途**：定义系统中的各种权限

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY, AUTO_INCREMENT | 权限唯一标识 |
| permission_name | VARCHAR(100) | NOT NULL | 权限显示名称 |
| permission_code | VARCHAR(100) | NOT NULL, UNIQUE | 权限代码，程序中使用 |
| resource_type | VARCHAR(50) | NOT NULL | 资源类型（如：user, role, order等） |
| action_type | VARCHAR(50) | NOT NULL | 操作类型（如：view, create, edit, delete） |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引设计**：
- 主键索引：id
- 唯一索引：permission_code
- 普通索引：permission_name, resource_type, action_type
- 复合索引：(resource_type, action_type)

### 4. 用户角色关联表 (user_roles)
**用途**：建立用户与角色的多对多关系

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY, AUTO_INCREMENT | 关联记录唯一标识 |
| user_id | BIGINT UNSIGNED | NOT NULL, FOREIGN KEY | 用户ID，关联users表 |
| role_id | BIGINT UNSIGNED | NOT NULL, FOREIGN KEY | 角色ID，关联roles表 |
| assigned_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 分配时间 |
| assigned_by | BIGINT UNSIGNED | FOREIGN KEY | 分配人ID，关联users表 |
| status | TINYINT | NOT NULL, DEFAULT 1 | 关联状态：1=启用，0=禁用 |

**索引设计**：
- 主键索引：id
- 唯一索引：(user_id, role_id)
- 普通索引：user_id, role_id, assigned_by, status, assigned_at

**外键约束**：
- user_id → users(id) ON DELETE CASCADE
- role_id → roles(id) ON DELETE CASCADE
- assigned_by → users(id) ON DELETE SET NULL

### 5. 角色权限关联表 (role_permissions)
**用途**：建立角色与权限的多对多关系

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY, AUTO_INCREMENT | 关联记录唯一标识 |
| role_id | BIGINT UNSIGNED | NOT NULL, FOREIGN KEY | 角色ID，关联roles表 |
| permission_id | BIGINT UNSIGNED | NOT NULL, FOREIGN KEY | 权限ID，关联permissions表 |
| granted_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 授权时间 |
| granted_by | BIGINT UNSIGNED | FOREIGN KEY | 授权人ID，关联users表 |
| status | TINYINT | NOT NULL, DEFAULT 1 | 授权状态：1=启用，0=禁用 |

**索引设计**：
- 主键索引：id
- 唯一索引：(role_id, permission_id)
- 普通索引：role_id, permission_id, granted_by, status, granted_at

**外键约束**：
- role_id → roles(id) ON DELETE CASCADE
- permission_id → permissions(id) ON DELETE CASCADE
- granted_by → users(id) ON DELETE SET NULL

## 数据关系图

```
users (用户表)
  ↓ 1:N
user_roles (用户角色关联表)
  ↓ N:1
roles (角色表)
  ↓ 1:N
role_permissions (角色权限关联表)
  ↓ N:1
permissions (权限表)
```

## 权限验证流程

1. **用户登录**：通过username/email验证用户身份
2. **获取用户角色**：查询user_roles表获取用户的所有角色
3. **获取角色权限**：查询role_permissions表获取角色的所有权限
4. **权限验证**：检查用户是否具有特定的权限代码

## 初始数据

系统包含以下初始数据：

**用户**：
- admin (admin@system.com) - 系统管理员
- system (system@system.com) - 系统用户

**角色**：
- super_admin - 超级管理员
- admin - 系统管理员  
- user - 普通用户

**权限**：
- 用户管理权限：user:view, user:create, user:edit, user:delete
- 角色管理权限：role:view, role:create, role:edit, role:delete

## 性能考虑

1. **索引优化**：为常用查询字段添加索引
2. **外键约束**：使用CASCADE删除保证数据一致性
3. **状态字段**：使用TINYINT节省存储空间
4. **时间戳**：使用TIMESTAMP自动维护时间信息
5. **字符集**：使用utf8mb4支持完整的Unicode字符

## 扩展性设计

1. **权限粒度**：通过resource_type和action_type支持细粒度权限控制
2. **审计追踪**：记录分配人和授权人信息
3. **软删除**：通过status字段支持软删除
4. **时间追踪**：记录创建和更新时间

## 安全考虑

1. **外键约束**：防止数据不一致
2. **唯一约束**：防止重复数据
3. **状态控制**：支持禁用用户和角色
4. **审计日志**：记录操作时间和操作人

---

*本设计文档将随着系统发展持续更新和完善*
