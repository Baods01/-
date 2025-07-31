# RBAC系统数据库表结构详细分析

## 📋 分析概述

**分析目标**：为ORM代码生成提供详细的数据库表结构分析  
**分析范围**：5个核心表（users, roles, permissions, user_roles, role_permissions）  
**参考版本**：优化版数据库设计（sql/02_optimized_schema.sql）  
**分析时间**：2025-07-19

## 🗄️ 表结构详细分析

### 1. 用户表 (users)

#### 基本信息
- **表名**：users
- **用途**：存储用户基本信息和认证数据
- **引擎**：InnoDB
- **字符集**：utf8mb4_unicode_ci
- **注释**：用户表

#### 字段结构分析

| 字段名 | 数据类型 | 长度限制 | 约束条件 | 默认值 | 说明 |
|--------|----------|----------|----------|--------|------|
| id | INT UNSIGNED | 4字节 | PRIMARY KEY, AUTO_INCREMENT, NOT NULL | 自增 | 用户唯一标识 |
| username | VARCHAR(32) | 32字符 | NOT NULL, UNIQUE | 无 | 用户名，登录凭证 |
| email | VARCHAR(64) | 64字符 | NOT NULL, UNIQUE | 无 | 邮箱地址，登录凭证 |
| password_hash | VARCHAR(255) | 255字符 | NOT NULL | 无 | 密码哈希值(bcrypt) |
| status | TINYINT UNSIGNED | 1字节 | NOT NULL | 1 | 状态：1=启用，0=禁用 |
| created_at | TIMESTAMP | 时间戳 | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 时间戳 | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 索引设计

| 索引名 | 索引类型 | 字段 | 用途 |
|--------|----------|------|------|
| PRIMARY | 主键索引 | id | 主键唯一标识 |
| uk_username | 唯一索引 | username | 用户名唯一性约束 |
| uk_email | 唯一索引 | email | 邮箱唯一性约束 |
| idx_status_created | 复合索引 | status, created_at | 按状态和创建时间查询优化 |

#### ORM映射要点
- **主键**：id (自增整型)
- **唯一字段**：username, email
- **状态字段**：status (布尔型映射)
- **时间字段**：created_at, updated_at (自动维护)
- **敏感字段**：password_hash (序列化时需排除)

### 2. 角色表 (roles)

#### 基本信息
- **表名**：roles
- **用途**：定义系统角色
- **引擎**：InnoDB
- **字符集**：utf8mb4_unicode_ci
- **注释**：角色表

#### 字段结构分析

| 字段名 | 数据类型 | 长度限制 | 约束条件 | 默认值 | 说明 |
|--------|----------|----------|----------|--------|------|
| id | SMALLINT UNSIGNED | 2字节 | PRIMARY KEY, AUTO_INCREMENT, NOT NULL | 自增 | 角色唯一标识 |
| role_name | VARCHAR(32) | 32字符 | NOT NULL | 无 | 角色显示名称 |
| role_code | VARCHAR(32) | 32字符 | NOT NULL, UNIQUE | 无 | 角色代码，程序中使用 |
| status | TINYINT UNSIGNED | 1字节 | NOT NULL | 1 | 状态：1=启用，0=禁用 |
| created_at | TIMESTAMP | 时间戳 | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 时间戳 | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

#### 索引设计

| 索引名 | 索引类型 | 字段 | 用途 |
|--------|----------|------|------|
| PRIMARY | 主键索引 | id | 主键唯一标识 |
| uk_role_code | 唯一索引 | role_code | 角色代码唯一性约束 |
| idx_status | 普通索引 | status | 按状态查询优化 |

#### ORM映射要点
- **主键**：id (小整型，适合角色数量不多的场景)
- **唯一字段**：role_code
- **状态字段**：status (布尔型映射)
- **时间字段**：created_at, updated_at (自动维护)

### 3. 权限表 (permissions)

#### 基本信息
- **表名**：permissions
- **用途**：定义系统权限
- **引擎**：InnoDB
- **字符集**：utf8mb4_unicode_ci
- **注释**：权限表

#### 字段结构分析

| 字段名 | 数据类型 | 长度限制 | 约束条件 | 默认值 | 说明 |
|--------|----------|----------|----------|--------|------|
| id | SMALLINT UNSIGNED | 2字节 | PRIMARY KEY, AUTO_INCREMENT, NOT NULL | 自增 | 权限唯一标识 |
| permission_name | VARCHAR(64) | 64字符 | NOT NULL | 无 | 权限显示名称 |
| permission_code | VARCHAR(64) | 64字符 | NOT NULL, UNIQUE | 无 | 权限代码，程序中使用 |
| resource_type | VARCHAR(32) | 32字符 | NOT NULL | 无 | 资源类型 |
| action_type | VARCHAR(16) | 16字符 | NOT NULL | 无 | 操作类型 |
| created_at | TIMESTAMP | 时间戳 | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |

#### 索引设计

| 索引名 | 索引类型 | 字段 | 用途 |
|--------|----------|------|------|
| PRIMARY | 主键索引 | id | 主键唯一标识 |
| uk_permission_code | 唯一索引 | permission_code | 权限代码唯一性约束 |
| idx_resource_action | 复合索引 | resource_type, action_type | 按资源和操作类型查询优化 |

#### ORM映射要点
- **主键**：id (小整型)
- **唯一字段**：permission_code
- **分类字段**：resource_type, action_type (枚举型映射)
- **时间字段**：created_at (只有创建时间，无更新时间)

### 4. 用户角色关联表 (user_roles)

#### 基本信息
- **表名**：user_roles
- **用途**：用户与角色的多对多关系
- **引擎**：InnoDB
- **字符集**：utf8mb4_unicode_ci
- **注释**：用户角色关联表

#### 字段结构分析

| 字段名 | 数据类型 | 长度限制 | 约束条件 | 默认值 | 说明 |
|--------|----------|----------|----------|--------|------|
| user_id | INT UNSIGNED | 4字节 | NOT NULL, FOREIGN KEY | 无 | 用户ID，关联users.id |
| role_id | SMALLINT UNSIGNED | 2字节 | NOT NULL, FOREIGN KEY | 无 | 角色ID，关联roles.id |
| assigned_at | TIMESTAMP | 时间戳 | NOT NULL | CURRENT_TIMESTAMP | 分配时间 |
| assigned_by | INT UNSIGNED | 4字节 | FOREIGN KEY | NULL | 分配人ID，关联users.id |
| status | TINYINT UNSIGNED | 1字节 | NOT NULL | 1 | 状态：1=启用，0=禁用 |

#### 索引设计

| 索引名 | 索引类型 | 字段 | 用途 |
|--------|----------|------|------|
| PRIMARY | 复合主键 | user_id, role_id | 复合主键，确保唯一性 |
| idx_role_id | 普通索引 | role_id | 按角色查询用户优化 |
| idx_assigned_by | 普通索引 | assigned_by | 按分配人查询优化 |
| idx_status_assigned | 复合索引 | status, assigned_at | 按状态和分配时间查询优化 |

#### 外键约束

| 约束名 | 外键字段 | 引用表.字段 | 删除规则 | 更新规则 |
|--------|----------|-------------|----------|----------|
| fk_user_roles_user_id | user_id | users.id | CASCADE | CASCADE |
| fk_user_roles_role_id | role_id | roles.id | CASCADE | CASCADE |
| fk_user_roles_assigned_by | assigned_by | users.id | SET NULL | CASCADE |

#### ORM映射要点
- **复合主键**：(user_id, role_id)
- **外键关系**：多对一关系到users和roles表
- **审计字段**：assigned_at, assigned_by
- **状态字段**：status (软删除支持)

### 5. 角色权限关联表 (role_permissions)

#### 基本信息
- **表名**：role_permissions
- **用途**：角色与权限的多对多关系
- **引擎**：InnoDB
- **字符集**：utf8mb4_unicode_ci
- **注释**：角色权限关联表

#### 字段结构分析

| 字段名 | 数据类型 | 长度限制 | 约束条件 | 默认值 | 说明 |
|--------|----------|----------|----------|--------|------|
| role_id | SMALLINT UNSIGNED | 2字节 | NOT NULL, FOREIGN KEY | 无 | 角色ID，关联roles.id |
| permission_id | SMALLINT UNSIGNED | 2字节 | NOT NULL, FOREIGN KEY | 无 | 权限ID，关联permissions.id |
| granted_at | TIMESTAMP | 时间戳 | NOT NULL | CURRENT_TIMESTAMP | 授权时间 |
| granted_by | INT UNSIGNED | 4字节 | FOREIGN KEY | NULL | 授权人ID，关联users.id |
| status | TINYINT UNSIGNED | 1字节 | NOT NULL | 1 | 状态：1=启用，0=禁用 |

#### 索引设计

| 索引名 | 索引类型 | 字段 | 用途 |
|--------|----------|------|------|
| PRIMARY | 复合主键 | role_id, permission_id | 复合主键，确保唯一性 |
| idx_permission_id | 普通索引 | permission_id | 按权限查询角色优化 |
| idx_granted_by | 普通索引 | granted_by | 按授权人查询优化 |
| idx_status_granted | 复合索引 | status, granted_at | 按状态和授权时间查询优化 |

#### 外键约束

| 约束名 | 外键字段 | 引用表.字段 | 删除规则 | 更新规则 |
|--------|----------|-------------|----------|----------|
| fk_role_permissions_role_id | role_id | roles.id | CASCADE | CASCADE |
| fk_role_permissions_permission_id | permission_id | permissions.id | CASCADE | CASCADE |
| fk_role_permissions_granted_by | granted_by | users.id | SET NULL | CASCADE |

#### ORM映射要点
- **复合主键**：(role_id, permission_id)
- **外键关系**：多对一关系到roles和permissions表
- **审计字段**：granted_at, granted_by
- **状态字段**：status (软删除支持)

## 🔗 表关系映射总结

### 实体关系图
```
users (用户表)
  ↓ 1:N (一个用户可以有多个角色)
user_roles (用户角色关联表)
  ↓ N:1 (多个用户角色关联对应一个角色)
roles (角色表)
  ↓ 1:N (一个角色可以有多个权限)
role_permissions (角色权限关联表)
  ↓ N:1 (多个角色权限关联对应一个权限)
permissions (权限表)
```

### 关系类型总结
1. **User ↔ Role**：多对多关系（通过user_roles表）
2. **Role ↔ Permission**：多对多关系（通过role_permissions表）
3. **User → User**：自引用关系（assigned_by, granted_by字段）

## 📊 字段映射清单

### Python数据类型映射

| MySQL类型 | Python类型 | SQLAlchemy类型 | 说明 |
|-----------|-------------|----------------|------|
| INT UNSIGNED | int | Integer | 32位无符号整数 |
| SMALLINT UNSIGNED | int | SmallInteger | 16位无符号整数 |
| TINYINT UNSIGNED | int/bool | Boolean/Integer | 8位无符号整数，可映射为布尔型 |
| VARCHAR(n) | str | String(n) | 变长字符串 |
| TIMESTAMP | datetime | DateTime | 时间戳 |

### 约束条件映射

| MySQL约束 | SQLAlchemy约束 | 说明 |
|-----------|----------------|------|
| PRIMARY KEY | primary_key=True | 主键约束 |
| AUTO_INCREMENT | autoincrement=True | 自增约束 |
| NOT NULL | nullable=False | 非空约束 |
| UNIQUE | unique=True | 唯一约束 |
| FOREIGN KEY | ForeignKey() | 外键约束 |
| DEFAULT | default= | 默认值约束 |

## ⚠️ 关键约束条件

### 数据完整性约束
1. **主键约束**：所有表都有明确的主键定义
2. **外键约束**：关联表使用CASCADE删除，审计字段使用SET NULL
3. **唯一约束**：用户名、邮箱、角色代码、权限代码必须唯一
4. **非空约束**：核心业务字段不允许为空

### 业务逻辑约束
1. **状态约束**：status字段统一使用1=启用，0=禁用
2. **时间约束**：创建时间自动设置，更新时间自动维护
3. **审计约束**：关联操作记录操作人和操作时间
4. **软删除**：通过status字段实现软删除，不物理删除数据

### 性能优化约束
1. **索引约束**：为常用查询字段建立合适的索引
2. **数据类型约束**：使用合适的数据类型节省存储空间
3. **字符集约束**：统一使用utf8mb4支持完整Unicode
4. **引擎约束**：统一使用InnoDB支持事务和外键

---

**分析完成时间**：2025-07-19  
**下一步**：基于此分析进行实体关系映射设计
