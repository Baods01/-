# RBAC系统实体关系映射设计

## 📋 映射概述

**设计目标**：为RBAC系统ORM层定义清晰的实体关系映射策略  
**映射框架**：SQLAlchemy ORM  
**关系类型**：一对多、多对多、自引用关系  
**设计时间**：2025-07-19

## 🔗 实体关系分析

### 核心实体识别

| 实体名称 | 对应表名 | 实体类型 | 说明 |
|----------|----------|----------|------|
| User | users | 主实体 | 用户实体，系统的核心用户对象 |
| Role | roles | 主实体 | 角色实体，权限的载体 |
| Permission | permissions | 主实体 | 权限实体，系统操作的最小单元 |
| UserRole | user_roles | 关联实体 | 用户角色关联，多对多关系的中间表 |
| RolePermission | role_permissions | 关联实体 | 角色权限关联，多对多关系的中间表 |

### 关系类型分析

#### 1. User ↔ Role 多对多关系
- **关系描述**：一个用户可以拥有多个角色，一个角色可以分配给多个用户
- **中间表**：user_roles
- **关系特点**：包含审计信息（分配时间、分配人、状态）
- **级联规则**：删除用户或角色时，级联删除关联关系

#### 2. Role ↔ Permission 多对多关系
- **关系描述**：一个角色可以拥有多个权限，一个权限可以分配给多个角色
- **中间表**：role_permissions
- **关系特点**：包含审计信息（授权时间、授权人、状态）
- **级联规则**：删除角色或权限时，级联删除关联关系

#### 3. User → User 自引用关系
- **关系描述**：用户可以作为操作人分配角色或授权权限
- **关系字段**：assigned_by, granted_by
- **关系特点**：可选关系，支持NULL值
- **级联规则**：删除操作人时，设置为NULL

## 🏗️ SQLAlchemy关系映射配置

### 1. User实体关系映射

```python
class User(Base):
    __tablename__ = 'users'
    
    # 基础字段
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), nullable=False, unique=True)
    email = Column(String(64), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系映射
    # 1. 用户的角色关联（一对多）
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    
    # 2. 用户的角色（多对多，通过UserRole）
    roles = relationship("Role", secondary="user_roles", back_populates="users", 
                        primaryjoin="User.id == UserRole.user_id",
                        secondaryjoin="Role.id == UserRole.role_id")
    
    # 3. 用户分配的角色关联（自引用，一对多）
    assigned_user_roles = relationship("UserRole", foreign_keys="UserRole.assigned_by", 
                                     back_populates="assigner")
    
    # 4. 用户授权的权限关联（自引用，一对多）
    granted_role_permissions = relationship("RolePermission", foreign_keys="RolePermission.granted_by", 
                                          back_populates="granter")
```

### 2. Role实体关系映射

```python
class Role(Base):
    __tablename__ = 'roles'
    
    # 基础字段
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    role_name = Column(String(32), nullable=False)
    role_code = Column(String(32), nullable=False, unique=True)
    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系映射
    # 1. 角色的用户关联（一对多）
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    # 2. 角色的用户（多对多，通过UserRole）
    users = relationship("User", secondary="user_roles", back_populates="roles",
                        primaryjoin="Role.id == UserRole.role_id",
                        secondaryjoin="User.id == UserRole.user_id")
    
    # 3. 角色的权限关联（一对多）
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    
    # 4. 角色的权限（多对多，通过RolePermission）
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles",
                             primaryjoin="Role.id == RolePermission.role_id",
                             secondaryjoin="Permission.id == RolePermission.permission_id")
```

### 3. Permission实体关系映射

```python
class Permission(Base):
    __tablename__ = 'permissions'
    
    # 基础字段
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    permission_name = Column(String(64), nullable=False)
    permission_code = Column(String(64), nullable=False, unique=True)
    resource_type = Column(String(32), nullable=False)
    action_type = Column(String(16), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关系映射
    # 1. 权限的角色关联（一对多）
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    
    # 2. 权限的角色（多对多，通过RolePermission）
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions",
                        primaryjoin="Permission.id == RolePermission.permission_id",
                        secondaryjoin="Role.id == RolePermission.role_id")
```

### 4. UserRole关联实体映射

```python
class UserRole(Base):
    __tablename__ = 'user_roles'
    
    # 复合主键
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(SmallInteger, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    
    # 审计字段
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = Column(Integer, nullable=False, default=1)
    
    # 关系映射
    # 1. 关联的用户（多对一）
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    
    # 2. 关联的角色（多对一）
    role = relationship("Role", foreign_keys=[role_id], back_populates="user_roles")
    
    # 3. 分配人（多对一，自引用）
    assigner = relationship("User", foreign_keys=[assigned_by], back_populates="assigned_user_roles")
```

### 5. RolePermission关联实体映射

```python
class RolePermission(Base):
    __tablename__ = 'role_permissions'
    
    # 复合主键
    role_id = Column(SmallInteger, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id = Column(SmallInteger, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
    
    # 审计字段
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = Column(Integer, nullable=False, default=1)
    
    # 关系映射
    # 1. 关联的角色（多对一）
    role = relationship("Role", foreign_keys=[role_id], back_populates="role_permissions")
    
    # 2. 关联的权限（多对一）
    permission = relationship("Permission", foreign_keys=[permission_id], back_populates="role_permissions")
    
    # 3. 授权人（多对一，自引用）
    granter = relationship("User", foreign_keys=[granted_by], back_populates="granted_role_permissions")
```

## 🔄 关系查询策略

### 懒加载vs急加载策略

#### 1. 懒加载（Lazy Loading）- 默认策略
```python
# 适用场景：不总是需要关联数据的情况
user_roles = relationship("UserRole", lazy="select")  # 默认懒加载
```

#### 2. 急加载（Eager Loading）- 性能优化
```python
# 适用场景：总是需要关联数据的情况
user_roles = relationship("UserRole", lazy="joined")  # JOIN查询
user_roles = relationship("UserRole", lazy="subquery")  # 子查询
```

#### 3. 动态加载（Dynamic Loading）- 大数据集
```python
# 适用场景：关联数据量很大的情况
user_roles = relationship("UserRole", lazy="dynamic")  # 返回Query对象
```

### 查询优化建议

#### 1. 避免N+1查询问题
```python
# 错误方式：会产生N+1查询
users = session.query(User).all()
for user in users:
    print(user.roles)  # 每次都会查询数据库

# 正确方式：使用joinedload
users = session.query(User).options(joinedload(User.roles)).all()
for user in users:
    print(user.roles)  # 不会额外查询数据库
```

#### 2. 复杂关系查询
```python
# 查询用户的所有权限（通过角色）
user_permissions = session.query(Permission)\
    .join(RolePermission)\
    .join(Role)\
    .join(UserRole)\
    .filter(UserRole.user_id == user_id)\
    .filter(UserRole.status == 1)\
    .filter(RolePermission.status == 1)\
    .all()
```

## ⚡ 性能优化考虑

### 1. 索引优化
- **复合索引**：为常用的查询组合建立复合索引
- **外键索引**：确保所有外键都有对应的索引
- **状态索引**：为status字段建立索引支持软删除查询

### 2. 查询优化
- **批量加载**：使用joinedload或subqueryload避免N+1问题
- **分页查询**：对大数据集使用分页避免内存溢出
- **缓存策略**：对不经常变化的权限数据使用缓存

### 3. 关系设计优化
- **级联规则**：合理设置CASCADE和SET NULL规则
- **软删除**：通过status字段实现软删除，保留审计信息
- **审计字段**：记录操作时间和操作人，支持审计需求

## 🎯 关系映射最佳实践

### 1. 命名规范
- **关系属性**：使用复数形式表示一对多关系（如users, roles）
- **反向引用**：使用back_populates明确双向关系
- **外键字段**：使用foreign_keys明确指定外键字段

### 2. 级联配置
- **删除级联**：主实体删除时，级联删除关联关系
- **孤儿删除**：使用delete-orphan清理孤儿记录
- **NULL设置**：审计字段在引用删除时设置为NULL

### 3. 查询优化
- **预加载**：根据使用场景选择合适的加载策略
- **索引利用**：确保查询能够有效利用数据库索引
- **批量操作**：使用bulk操作提高大数据量处理性能

---

**映射设计完成时间**：2025-07-19  
**下一步**：制定代码生成规范
