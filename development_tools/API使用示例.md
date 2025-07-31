# RBAC权限管理系统 API使用示例

## 📋 概述

本文档提供RBAC权限管理系统API的完整使用示例，包括认证、用户管理、角色管理和权限管理的所有接口。

## 🚀 快速开始

### 启动API服务器

```bash
# 方法1：使用示例应用
python development_tools/fastapi_app_example.py --run

# 方法2：直接使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 访问API文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔐 认证管理API

### 1. 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "remember_me": true
  }'
```

**响应示例**：
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "nickname": "管理员"
    }
  }
}
```

### 2. 获取当前用户信息

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 刷新令牌

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### 4. 修改密码

```bash
curl -X PUT "http://localhost:8000/api/v1/auth/password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "oldpass123",
    "new_password": "newpass123"
  }'
```

### 5. 用户登出

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 👥 用户管理API

### 1. 创建用户

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123",
    "nickname": "新用户",
    "phone": "13800138000"
  }'
```

### 2. 获取用户列表（分页、搜索、过滤）

```bash
# 基本分页查询
curl -X GET "http://localhost:8000/api/v1/users?page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 搜索用户
curl -X GET "http://localhost:8000/api/v1/users?search=admin&page=1&size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 按状态过滤
curl -X GET "http://localhost:8000/api/v1/users?status=1&page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应示例**：
```json
{
  "success": true,
  "message": "获取用户列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "nickname": "管理员",
        "status": 1,
        "created_at": "2025-07-22T10:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20,
    "pages": 1
  }
}
```

### 3. 获取用户详情

```bash
curl -X GET "http://localhost:8000/api/v1/users/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. 更新用户信息

```bash
curl -X PUT "http://localhost:8000/api/v1/users/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "系统管理员",
    "phone": "13900139000"
  }'
```

### 5. 删除用户

```bash
curl -X DELETE "http://localhost:8000/api/v1/users/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🎭 角色管理API

### 1. 创建角色

```bash
curl -X POST "http://localhost:8000/api/v1/roles" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_name": "管理员",
    "role_code": "admin",
    "description": "系统管理员角色"
  }'
```

### 2. 获取角色列表

```bash
# 基本查询
curl -X GET "http://localhost:8000/api/v1/roles?page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 搜索角色
curl -X GET "http://localhost:8000/api/v1/roles?search=admin" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 获取角色详情

```bash
curl -X GET "http://localhost:8000/api/v1/roles/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. 为角色分配权限

```bash
curl -X POST "http://localhost:8000/api/v1/roles/1/permissions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permission_ids": [1, 2, 3, 4]
  }'
```

## 🔑 权限管理API

### 1. 获取权限树结构

```bash
# 获取所有权限树
curl -X GET "http://localhost:8000/api/v1/permissions/tree" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 按资源类型过滤
curl -X GET "http://localhost:8000/api/v1/permissions/tree?resource_type=user" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应示例**：
```json
{
  "success": true,
  "message": "获取权限树成功",
  "data": [
    {
      "id": 1,
      "permission_name": "用户管理",
      "permission_code": "user",
      "resource_type": "user",
      "description": "用户管理相关权限",
      "children": [
        {
          "id": 2,
          "permission_name": "创建用户",
          "permission_code": "user:create",
          "resource_type": "user",
          "description": "创建新用户",
          "children": []
        }
      ]
    }
  ]
}
```

### 2. 获取权限列表

```bash
# 基本查询
curl -X GET "http://localhost:8000/api/v1/permissions?page=1&size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 按资源类型过滤
curl -X GET "http://localhost:8000/api/v1/permissions?resource_type=user" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 获取资源类型列表

```bash
curl -X GET "http://localhost:8000/api/v1/permissions/resource-types" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. 检查用户权限

```bash
curl -X POST "http://localhost:8000/api/v1/permissions/check" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "permission_codes": ["user:create", "user:read", "user:update"]
  }'
```

## 📊 响应格式说明

### 成功响应格式

```json
{
  "success": true,
  "message": "操作成功描述",
  "data": {
    // 具体的响应数据
  },
  "timestamp": "2025-07-22T12:00:00"
}
```

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": {
    // 错误详情
  },
  "timestamp": "2025-07-22T12:00:00"
}
```

### 分页响应格式

```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "items": [
      // 数据列表
    ],
    "total": 100,      // 总记录数
    "page": 1,         // 当前页码
    "size": 20,        // 每页大小
    "pages": 5         // 总页数
  }
}
```

## 🚨 错误码说明

| HTTP状态码 | 说明 | 示例场景 |
|-----------|------|----------|
| 200 | 请求成功 | 正常的GET、PUT请求 |
| 201 | 创建成功 | POST创建资源成功 |
| 400 | 请求参数错误 | 业务逻辑错误 |
| 401 | 未授权 | 令牌无效或过期 |
| 403 | 权限不足 | 没有操作权限 |
| 404 | 资源不存在 | 用户、角色不存在 |
| 409 | 资源冲突 | 用户名、邮箱重复 |
| 422 | 数据验证失败 | 参数格式错误 |
| 500 | 服务器内部错误 | 系统异常 |

## 💡 使用建议

### 1. 认证流程
1. 使用 `/api/v1/auth/login` 登录获取令牌
2. 在后续请求中使用 `Authorization: Bearer TOKEN` 头
3. 令牌过期时使用 `/api/v1/auth/refresh` 刷新
4. 登出时调用 `/api/v1/auth/logout` 撤销令牌

### 2. 分页查询
- 使用 `page` 和 `size` 参数进行分页
- `page` 从1开始，`size` 建议不超过100
- 响应中包含完整的分页信息

### 3. 搜索过滤
- 使用 `search` 参数进行关键词搜索
- 使用具体字段参数进行精确过滤
- 多个过滤条件可以组合使用

### 4. 错误处理
- 检查响应的 `success` 字段判断请求是否成功
- 根据HTTP状态码和错误信息进行相应处理
- 401错误时需要重新登录或刷新令牌

---

**文档版本**: 1.0.0  
**最后更新**: 2025-07-22  
**维护团队**: RBAC System Development Team
