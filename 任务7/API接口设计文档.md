# RBAC权限系统 API接口设计文档

## 📋 API概览

基于已完成的业务服务层，设计RESTful API接口规范。

### API基础信息
- **Base URL**: `http://localhost:5000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 🔐 认证接口 (Auth API)

### 1. 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123",
  "remember_me": true
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 2592000,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "nickname": "管理员",
      "roles": ["admin", "user"],
      "permissions": ["user:view", "user:create", "role:manage"]
    }
  }
}
```

### 2. 刷新令牌
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. 用户登出
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. 验证令牌
```http
GET /api/v1/auth/verify
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 👥 用户管理接口 (User API)

### 1. 获取用户列表
```http
GET /api/v1/users?page=1&size=20&keyword=admin&status=1
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "nickname": "管理员",
        "status": 1,
        "created_at": "2025-07-21T10:00:00Z",
        "last_login_at": "2025-07-21T15:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

### 2. 创建用户
```http
POST /api/v1/users
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "nickname": "新用户",
  "phone": "13800138000"
}
```

### 3. 获取用户详情
```http
GET /api/v1/users/{user_id}
Authorization: Bearer {token}
```

### 4. 更新用户信息
```http
PUT /api/v1/users/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "nickname": "更新的昵称",
  "phone": "13900139000"
}
```

### 5. 删除用户
```http
DELETE /api/v1/users/{user_id}
Authorization: Bearer {token}
```

### 6. 分配用户角色
```http
POST /api/v1/users/{user_id}/roles
Authorization: Bearer {token}
Content-Type: application/json

{
  "role_ids": [1, 2, 3]
}
```

### 7. 获取用户角色
```http
GET /api/v1/users/{user_id}/roles
Authorization: Bearer {token}
```

## 🎭 角色管理接口 (Role API)

### 1. 获取角色列表
```http
GET /api/v1/roles?page=1&size=20&keyword=管理
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "roles": [
      {
        "id": 1,
        "role_name": "系统管理员",
        "role_code": "admin",
        "description": "系统管理员角色",
        "status": 1,
        "user_count": 2,
        "permission_count": 15,
        "created_at": "2025-07-21T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

### 2. 创建角色
```http
POST /api/v1/roles
Authorization: Bearer {token}
Content-Type: application/json

{
  "role_name": "编辑者",
  "role_code": "editor",
  "description": "内容编辑者角色"
}
```

### 3. 更新角色
```http
PUT /api/v1/roles/{role_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "description": "更新后的角色描述"
}
```

### 4. 删除角色
```http
DELETE /api/v1/roles/{role_id}?force=false
Authorization: Bearer {token}
```

### 5. 分配角色权限
```http
POST /api/v1/roles/{role_id}/permissions
Authorization: Bearer {token}
Content-Type: application/json

{
  "permission_ids": [1, 2, 3, 4, 5]
}
```

### 6. 获取角色权限
```http
GET /api/v1/roles/{role_id}/permissions
Authorization: Bearer {token}
```

### 7. 获取角色用户
```http
GET /api/v1/roles/{role_id}/users?page=1&size=20
Authorization: Bearer {token}
```

## 🔑 权限管理接口 (Permission API)

### 1. 获取权限树
```http
GET /api/v1/permissions/tree?resource_type=user
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user": {
      "resource_name": "用户管理",
      "resource_type": "user",
      "permissions": [
        {
          "id": 1,
          "name": "查看用户",
          "code": "user:view",
          "action": "view",
          "description": "查看用户信息的权限"
        },
        {
          "id": 2,
          "name": "创建用户",
          "code": "user:create",
          "action": "create",
          "description": "创建新用户的权限"
        }
      ]
    }
  }
}
```

### 2. 获取权限列表
```http
GET /api/v1/permissions?page=1&size=20&keyword=用户&resource_type=user
Authorization: Bearer {token}
```

### 3. 创建权限
```http
POST /api/v1/permissions
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "导出用户",
  "code": "user:export",
  "resource_type": "user",
  "action_type": "export",
  "description": "导出用户数据的权限"
}
```

### 4. 更新权限
```http
PUT /api/v1/permissions/{permission_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "description": "更新后的权限描述"
}
```

### 5. 删除权限
```http
DELETE /api/v1/permissions/{permission_id}?force=false
Authorization: Bearer {token}
```

### 6. 检查用户权限
```http
GET /api/v1/permissions/check?user_id=1&permission_code=user:view
Authorization: Bearer {token}
```

### 7. 获取权限统计
```http
GET /api/v1/permissions/statistics
Authorization: Bearer {token}
```

## 📊 系统管理接口 (System API)

### 1. 获取系统统计
```http
GET /api/v1/system/statistics
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_count": 150,
    "role_count": 8,
    "permission_count": 45,
    "active_sessions": 23,
    "today_logins": 67,
    "system_uptime": "15天3小时"
  }
}
```

### 2. 获取操作日志
```http
GET /api/v1/system/logs?page=1&size=50&operation=create_user&start_date=2025-07-20
Authorization: Bearer {token}
```

### 3. 获取在线用户
```http
GET /api/v1/system/online-users
Authorization: Bearer {token}
```

## 🔄 批量操作接口

### 1. 批量创建用户
```http
POST /api/v1/users/batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "users": [
    {
      "username": "user1",
      "email": "user1@example.com",
      "password": "password123"
    },
    {
      "username": "user2",
      "email": "user2@example.com",
      "password": "password123"
    }
  ]
}
```

### 2. 批量分配权限
```http
POST /api/v1/roles/batch-permissions
Authorization: Bearer {token}
Content-Type: application/json

{
  "assignments": [
    {
      "role_id": 1,
      "permission_ids": [1, 2, 3]
    },
    {
      "role_id": 2,
      "permission_ids": [2, 3, 4]
    }
  ]
}
```

## 📝 通用响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... },
  "timestamp": "2025-07-21T15:30:00Z"
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "请求参数错误",
  "error": {
    "type": "VALIDATION_ERROR",
    "details": "用户名长度必须在3-50字符之间"
  },
  "timestamp": "2025-07-21T15:30:00Z"
}
```

### HTTP状态码
- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未认证
- `403` - 权限不足
- `404` - 资源不存在
- `409` - 资源冲突
- `500` - 服务器内部错误

## 🔒 权限控制

每个API接口都需要相应的权限：

```
用户管理接口：
- GET /users → user:view
- POST /users → user:create
- PUT /users → user:edit
- DELETE /users → user:delete

角色管理接口：
- GET /roles → role:view
- POST /roles → role:create
- PUT /roles → role:edit
- DELETE /roles → role:delete

权限管理接口：
- GET /permissions → permission:view
- POST /permissions → permission:create
- PUT /permissions → permission:edit
- DELETE /permissions → permission:delete
```

---

**文档版本**：1.0.0  
**更新时间**：2025-07-21  
**基于服务**：UserService, RoleService, PermissionService, AuthService
