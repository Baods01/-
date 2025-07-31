#!/usr/bin/env python3
"""
RBAC权限管理系统 - Swagger文档演示应用

用于生成完整的API文档，方便获取Swagger文档截图。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, Path, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 安全认证
security = HTTPBearer()

# 创建FastAPI应用
app = FastAPI(
    title="RBAC权限管理系统",
    description="""
    ## 基于角色的访问控制(RBAC)权限管理系统

    这是一个完整的企业级权限管理系统，提供以下核心功能：

    ### 🔐 认证管理
    - 用户登录和登出
    - JWT令牌管理
    - 密码修改
    - 会话管理

    ### 👥 用户管理
    - 用户注册和管理
    - 用户信息维护
    - 用户状态控制
    - 用户角色分配

    ### 🎭 角色管理
    - 角色定义和管理
    - 角色权限分配
    - 角色层级关系
    - 角色继承机制

    ### 🔑 权限管理
    - 权限定义和分类
    - 权限树形结构
    - 动态权限检查
    - 权限继承和传递

    ### 🛡️ 安全特性
    - JWT令牌认证
    - 细粒度权限控制
    - SQL注入防护
    - XSS攻击防护
    - 输入验证和清理

    ### 📊 技术特性
    - 异步高性能架构
    - RESTful API设计
    - 统一响应格式
    - 完整的错误处理
    - 自动API文档生成
    """,
    version="1.0.0",
    contact={
        "name": "RBAC System Development Team",
        "email": "support@rbac-system.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ==================== 数据模型定义 ====================

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., description="用户名", example="admin")
    email: str = Field(..., description="邮箱地址", example="admin@example.com")
    nickname: str = Field(..., description="昵称", example="系统管理员")
    phone: Optional[str] = Field(None, description="手机号", example="13800138000")

class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., description="密码", example="password123")

class UserUpdate(BaseModel):
    """更新用户请求"""
    nickname: Optional[str] = Field(None, description="昵称", example="新昵称")
    phone: Optional[str] = Field(None, description="手机号", example="13900139000")
    status: Optional[int] = Field(None, description="状态 (0=禁用, 1=启用)", example=1)

class UserResponse(UserBase):
    """用户响应信息"""
    id: int = Field(..., description="用户ID", example=1)
    status: int = Field(..., description="状态 (0=禁用, 1=启用)", example=1)
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名", example="admin")
    password: str = Field(..., description="密码", example="admin123")
    remember_me: bool = Field(False, description="记住登录状态", example=True)

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)", example=900)
    user: UserResponse = Field(..., description="用户信息")

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")

class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码", example="oldpass123")
    new_password: str = Field(..., description="新密码", example="newpass123")

class RoleBase(BaseModel):
    """角色基础信息"""
    role_name: str = Field(..., description="角色名称", example="管理员")
    role_code: str = Field(..., description="角色代码", example="admin")
    description: Optional[str] = Field(None, description="角色描述", example="系统管理员角色")

class RoleCreate(RoleBase):
    """创建角色请求"""
    pass

class RoleResponse(RoleBase):
    """角色响应信息"""
    id: int = Field(..., description="角色ID", example=1)
    status: int = Field(..., description="状态 (0=禁用, 1=启用)", example=1)
    user_count: int = Field(0, description="用户数量", example=5)
    permission_count: int = Field(0, description="权限数量", example=10)
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class PermissionAssignRequest(BaseModel):
    """权限分配请求"""
    permission_ids: List[int] = Field(..., description="权限ID列表", example=[1, 2, 3, 4])

class PermissionBase(BaseModel):
    """权限基础信息"""
    permission_name: str = Field(..., description="权限名称", example="用户管理")
    permission_code: str = Field(..., description="权限代码", example="user:manage")
    resource_type: str = Field(..., description="资源类型", example="user")
    description: Optional[str] = Field(None, description="权限描述", example="用户管理相关权限")

class PermissionResponse(PermissionBase):
    """权限响应信息"""
    id: int = Field(..., description="权限ID", example=1)
    parent_id: Optional[int] = Field(None, description="父权限ID", example=None)
    status: int = Field(..., description="状态 (0=禁用, 1=启用)", example=1)
    children: List['PermissionResponse'] = Field([], description="子权限列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    permission_codes: List[str] = Field(..., description="权限代码列表", example=["user:create", "user:read"])

class PermissionCheckResponse(BaseModel):
    """权限检查响应"""
    permission_code: str = Field(..., description="权限代码", example="user:create")
    has_permission: bool = Field(..., description="是否有权限", example=True)
    source: str = Field(..., description="权限来源", example="role:admin")

class ResourceTypeResponse(BaseModel):
    """资源类型响应"""
    resource_type: str = Field(..., description="资源类型", example="user")
    description: str = Field(..., description="类型描述", example="用户管理")
    permission_count: int = Field(..., description="权限数量", example=5)

class PaginationResponse(BaseModel):
    """分页响应"""
    total: int = Field(..., description="总记录数", example=100)
    page: int = Field(..., description="当前页码", example=1)
    size: int = Field(..., description="每页大小", example=20)
    pages: int = Field(..., description="总页数", example=5)

class SuccessResponse(BaseModel):
    """成功响应格式"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="响应消息", example="操作成功")
    data: Optional[dict] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

# 更新前向引用
PermissionResponse.model_rebuild()

# ==================== 认证管理接口 ====================

@app.post(
    "/api/v1/auth/login",
    response_model=SuccessResponse,
    summary="用户登录",
    description="用户通过用户名和密码进行登录认证，成功后返回JWT访问令牌和刷新令牌",
    tags=["认证管理"],
    responses={
        200: {"description": "登录成功", "model": SuccessResponse},
        400: {"description": "请求参数错误"},
        401: {"description": "用户名或密码错误"},
        422: {"description": "数据验证失败"}
    }
)
async def login(login_data: LoginRequest):
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    - **remember_me**: 是否记住登录状态
    
    返回JWT访问令牌和刷新令牌，用于后续API调用的身份验证。
    """
    # 模拟登录逻辑
    if login_data.username == "admin" and login_data.password == "admin123":
        return {
            "success": True,
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
                    "nickname": "系统管理员",
                    "phone": "13800138000",
                    "status": 1,
                    "created_at": "2025-07-22T10:00:00Z",
                    "updated_at": "2025-07-22T10:00:00Z"
                }
            }
        }
    else:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

@app.post(
    "/api/v1/auth/logout",
    response_model=SuccessResponse,
    summary="用户登出",
    description="用户登出，撤销当前访问令牌",
    tags=["认证管理"],
    dependencies=[Depends(security)]
)
async def logout():
    """
    用户登出接口
    
    撤销当前用户的访问令牌，清理会话信息。
    需要在请求头中提供有效的Bearer令牌。
    """
    return {
        "success": True,
        "message": "登出成功",
        "data": None
    }

@app.post(
    "/api/v1/auth/refresh",
    response_model=SuccessResponse,
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌",
    tags=["认证管理"]
)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    刷新令牌接口
    
    - **refresh_token**: 刷新令牌
    
    使用有效的刷新令牌获取新的访问令牌，延长用户会话时间。
    """
    return {
        "success": True,
        "message": "令牌刷新成功",
        "data": {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "expires_in": 900
        }
    }

@app.get(
    "/api/v1/auth/me",
    response_model=SuccessResponse,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
    tags=["认证管理"],
    dependencies=[Depends(security)]
)
async def get_current_user():
    """
    获取当前用户信息接口
    
    返回当前登录用户的详细信息，包括用户基本信息、角色和权限。
    需要在请求头中提供有效的Bearer令牌。
    """
    return {
        "success": True,
        "message": "获取用户信息成功",
        "data": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "nickname": "系统管理员",
            "phone": "13800138000",
            "status": 1,
            "roles": ["admin", "user"],
            "permissions": ["user:create", "user:read", "user:update", "user:delete"],
            "last_login_at": "2025-07-22T10:00:00Z",
            "created_at": "2025-07-22T09:00:00Z",
            "updated_at": "2025-07-22T10:00:00Z"
        }
    }

@app.put(
    "/api/v1/auth/password",
    response_model=SuccessResponse,
    summary="修改密码",
    description="修改当前用户的登录密码",
    tags=["认证管理"],
    dependencies=[Depends(security)]
)
async def change_password(password_data: PasswordChangeRequest):
    """
    修改密码接口
    
    - **old_password**: 原密码
    - **new_password**: 新密码
    
    修改当前用户的登录密码，需要验证原密码的正确性。
    需要在请求头中提供有效的Bearer令牌。
    """
    return {
        "success": True,
        "message": "密码修改成功",
        "data": None
    }

# ==================== 用户管理接口 ====================

@app.post(
    "/api/v1/users",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户账户",
    tags=["用户管理"],
    dependencies=[Depends(security)]
)
async def create_user(user_data: UserCreate):
    """
    创建用户接口
    
    - **username**: 用户名（必须唯一）
    - **email**: 邮箱地址（必须唯一）
    - **password**: 登录密码
    - **nickname**: 用户昵称
    - **phone**: 手机号码（可选）
    
    创建新的用户账户，用户名和邮箱必须唯一。
    """
    return {
        "success": True,
        "message": "用户创建成功",
        "data": {
            "id": 2,
            "username": user_data.username,
            "email": user_data.email,
            "nickname": user_data.nickname,
            "phone": user_data.phone,
            "status": 1,
            "created_at": "2025-07-22T12:00:00Z",
            "updated_at": "2025-07-22T12:00:00Z"
        }
    }

@app.get(
    "/api/v1/users/{user_id}",
    response_model=SuccessResponse,
    summary="获取用户详情",
    description="根据用户ID获取用户详细信息",
    tags=["用户管理"],
    dependencies=[Depends(security)]
)
async def get_user(user_id: int = Path(..., description="用户ID", example=1)):
    """
    获取用户详情接口
    
    根据用户ID获取用户的详细信息，包括基本信息、角色和权限。
    """
    if user_id == 1:
        return {
            "success": True,
            "message": "获取用户详情成功",
            "data": {
                "id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "nickname": "系统管理员",
                "phone": "13800138000",
                "status": 1,
                "roles": [
                    {"id": 1, "role_name": "管理员", "role_code": "admin"}
                ],
                "permissions": [
                    {"id": 1, "permission_name": "用户管理", "permission_code": "user:manage"}
                ],
                "last_login_at": "2025-07-22T10:00:00Z",
                "created_at": "2025-07-22T09:00:00Z",
                "updated_at": "2025-07-22T10:00:00Z"
            }
        }
    else:
        raise HTTPException(status_code=404, detail="用户不存在")

@app.put(
    "/api/v1/users/{user_id}",
    response_model=SuccessResponse,
    summary="更新用户信息",
    description="更新指定用户的信息",
    tags=["用户管理"],
    dependencies=[Depends(security)]
)
async def update_user(user_id: int = Path(..., description="用户ID", example=1), user_data: UserUpdate = ...):
    """
    更新用户信息接口
    
    - **nickname**: 用户昵称（可选）
    - **phone**: 手机号码（可选）
    - **status**: 用户状态（可选，0=禁用，1=启用）
    
    更新指定用户的信息，支持部分更新。
    """
    return {
        "success": True,
        "message": "用户信息更新成功",
        "data": {
            "id": user_id,
            "nickname": user_data.nickname or "系统管理员",
            "phone": user_data.phone or "13800138000",
            "status": user_data.status or 1,
            "updated_at": "2025-07-22T12:30:00Z"
        }
    }

@app.delete(
    "/api/v1/users/{user_id}",
    response_model=SuccessResponse,
    summary="删除用户",
    description="删除指定的用户账户",
    tags=["用户管理"],
    dependencies=[Depends(security)]
)
async def delete_user(user_id: int = Path(..., description="用户ID", example=2)):
    """
    删除用户接口
    
    删除指定的用户账户，同时清理相关的角色分配和权限信息。
    注意：管理员用户不能删除自己。
    """
    if user_id == 1:
        raise HTTPException(status_code=400, detail="不能删除管理员用户")
    
    return {
        "success": True,
        "message": "用户删除成功",
        "data": None
    }

@app.get(
    "/api/v1/users",
    response_model=SuccessResponse,
    summary="获取用户列表",
    description="获取用户列表，支持分页、搜索和过滤",
    tags=["用户管理"],
    dependencies=[Depends(security)]
)
async def get_users(
    page: int = Query(1, ge=1, description="页码", example=1),
    size: int = Query(20, ge=1, le=100, description="每页数量", example=20),
    search: Optional[str] = Query(None, description="搜索关键词（用户名、邮箱、昵称）", example="admin"),
    status: Optional[int] = Query(None, description="用户状态（0=禁用，1=启用）", example=1)
):
    """
    获取用户列表接口
    
    - **page**: 页码（从1开始）
    - **size**: 每页数量（1-100）
    - **search**: 搜索关键词，支持用户名、邮箱、昵称模糊搜索
    - **status**: 用户状态过滤（0=禁用，1=启用）
    
    返回分页的用户列表，包含分页信息。
    """
    return {
        "success": True,
        "message": "获取用户列表成功",
        "data": {
            "items": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com",
                    "nickname": "系统管理员",
                    "phone": "13800138000",
                    "status": 1,
                    "role_count": 1,
                    "last_login_at": "2025-07-22T10:00:00Z",
                    "created_at": "2025-07-22T09:00:00Z"
                }
            ],
            "pagination": {
                "total": 1,
                "page": page,
                "size": size,
                "pages": 1
            }
        }
    }

# ==================== 角色管理接口 ====================

@app.post(
    "/api/v1/roles",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建角色",
    description="创建新的角色",
    tags=["角色管理"],
    dependencies=[Depends(security)]
)
async def create_role(role_data: RoleCreate):
    """
    创建角色接口

    - **role_name**: 角色名称
    - **role_code**: 角色代码（必须唯一）
    - **description**: 角色描述（可选）

    创建新的角色，角色代码必须唯一。
    """
    return {
        "success": True,
        "message": "角色创建成功",
        "data": {
            "id": 2,
            "role_name": role_data.role_name,
            "role_code": role_data.role_code,
            "description": role_data.description,
            "status": 1,
            "user_count": 0,
            "permission_count": 0,
            "created_at": "2025-07-22T12:00:00Z",
            "updated_at": "2025-07-22T12:00:00Z"
        }
    }

@app.get(
    "/api/v1/roles",
    response_model=SuccessResponse,
    summary="获取角色列表",
    description="获取角色列表，支持分页、搜索和过滤",
    tags=["角色管理"],
    dependencies=[Depends(security)]
)
async def get_roles(
    page: int = Query(1, ge=1, description="页码", example=1),
    size: int = Query(20, ge=1, le=100, description="每页数量", example=20),
    search: Optional[str] = Query(None, description="搜索关键词（角色名称、代码）", example="admin"),
    status: Optional[int] = Query(None, description="角色状态（0=禁用，1=启用）", example=1)
):
    """
    获取角色列表接口

    - **page**: 页码（从1开始）
    - **size**: 每页数量（1-100）
    - **search**: 搜索关键词，支持角色名称、代码模糊搜索
    - **status**: 角色状态过滤（0=禁用，1=启用）

    返回分页的角色列表，包含用户数量和权限数量统计。
    """
    return {
        "success": True,
        "message": "获取角色列表成功",
        "data": {
            "items": [
                {
                    "id": 1,
                    "role_name": "管理员",
                    "role_code": "admin",
                    "description": "系统管理员角色",
                    "status": 1,
                    "user_count": 1,
                    "permission_count": 10,
                    "created_at": "2025-07-22T09:00:00Z",
                    "updated_at": "2025-07-22T09:00:00Z"
                }
            ],
            "pagination": {
                "total": 1,
                "page": page,
                "size": size,
                "pages": 1
            }
        }
    }

@app.get(
    "/api/v1/roles/{role_id}",
    response_model=SuccessResponse,
    summary="获取角色详情",
    description="根据角色ID获取角色详细信息",
    tags=["角色管理"],
    dependencies=[Depends(security)]
)
async def get_role(role_id: int = Path(..., description="角色ID", example=1)):
    """
    获取角色详情接口

    根据角色ID获取角色的详细信息，包括基本信息、关联的权限和用户。
    """
    if role_id == 1:
        return {
            "success": True,
            "message": "获取角色详情成功",
            "data": {
                "id": 1,
                "role_name": "管理员",
                "role_code": "admin",
                "description": "系统管理员角色",
                "status": 1,
                "permissions": [
                    {"id": 1, "permission_name": "用户管理", "permission_code": "user:manage"},
                    {"id": 2, "permission_name": "角色管理", "permission_code": "role:manage"}
                ],
                "users": [
                    {"id": 1, "username": "admin", "nickname": "系统管理员"}
                ],
                "user_count": 1,
                "permission_count": 2,
                "created_at": "2025-07-22T09:00:00Z",
                "updated_at": "2025-07-22T09:00:00Z"
            }
        }
    else:
        raise HTTPException(status_code=404, detail="角色不存在")

@app.post(
    "/api/v1/roles/{role_id}/permissions",
    response_model=SuccessResponse,
    summary="分配权限给角色",
    description="为指定角色分配权限",
    tags=["角色管理"],
    dependencies=[Depends(security)]
)
async def assign_permissions(
    role_id: int = Path(..., description="角色ID", example=1),
    permission_data: PermissionAssignRequest = ...
):
    """
    分配权限给角色接口

    - **permission_ids**: 权限ID列表

    为指定角色分配一组权限，支持批量分配。
    """
    return {
        "success": True,
        "message": "权限分配成功",
        "data": {
            "role_id": role_id,
            "assigned_permissions": len(permission_data.permission_ids),
            "permission_ids": permission_data.permission_ids,
            "assigned_at": "2025-07-22T12:30:00Z"
        }
    }

# ==================== 权限管理接口 ====================

@app.get(
    "/api/v1/permissions/tree",
    response_model=SuccessResponse,
    summary="获取权限树结构",
    description="获取层级化的权限树结构",
    tags=["权限管理"],
    dependencies=[Depends(security)]
)
async def get_permission_tree(
    resource_type: Optional[str] = Query(None, description="资源类型过滤", example="user")
):
    """
    获取权限树结构接口

    - **resource_type**: 资源类型过滤（可选）

    返回层级化的权限树结构，支持按资源类型过滤。
    """
    return {
        "success": True,
        "message": "获取权限树成功",
        "data": [
            {
                "id": 1,
                "permission_name": "用户管理",
                "permission_code": "user",
                "resource_type": "user",
                "description": "用户管理相关权限",
                "status": 1,
                "children": [
                    {
                        "id": 2,
                        "permission_name": "创建用户",
                        "permission_code": "user:create",
                        "resource_type": "user",
                        "description": "创建新用户",
                        "status": 1,
                        "children": []
                    },
                    {
                        "id": 3,
                        "permission_name": "查看用户",
                        "permission_code": "user:read",
                        "resource_type": "user",
                        "description": "查看用户信息",
                        "status": 1,
                        "children": []
                    }
                ]
            }
        ]
    }

@app.get(
    "/api/v1/permissions",
    response_model=SuccessResponse,
    summary="获取权限列表",
    description="获取权限列表，支持分页、搜索和过滤",
    tags=["权限管理"],
    dependencies=[Depends(security)]
)
async def get_permissions(
    page: int = Query(1, ge=1, description="页码", example=1),
    size: int = Query(20, ge=1, le=100, description="每页数量", example=20),
    search: Optional[str] = Query(None, description="搜索关键词（权限名称、代码）", example="user"),
    resource_type: Optional[str] = Query(None, description="资源类型过滤", example="user"),
    status: Optional[int] = Query(None, description="权限状态（0=禁用，1=启用）", example=1)
):
    """
    获取权限列表接口

    - **page**: 页码（从1开始）
    - **size**: 每页数量（1-100）
    - **search**: 搜索关键词，支持权限名称、代码模糊搜索
    - **resource_type**: 资源类型过滤
    - **status**: 权限状态过滤（0=禁用，1=启用）

    返回分页的权限列表。
    """
    return {
        "success": True,
        "message": "获取权限列表成功",
        "data": {
            "items": [
                {
                    "id": 1,
                    "permission_name": "用户管理",
                    "permission_code": "user:manage",
                    "resource_type": "user",
                    "description": "用户管理相关权限",
                    "parent_id": None,
                    "status": 1,
                    "created_at": "2025-07-22T09:00:00Z",
                    "updated_at": "2025-07-22T09:00:00Z"
                }
            ],
            "pagination": {
                "total": 1,
                "page": page,
                "size": size,
                "pages": 1
            }
        }
    }

@app.get(
    "/api/v1/permissions/resource-types",
    response_model=SuccessResponse,
    summary="获取资源类型列表",
    description="获取所有资源类型及其权限数量统计",
    tags=["权限管理"],
    dependencies=[Depends(security)]
)
async def get_resource_types():
    """
    获取资源类型列表接口

    返回所有资源类型及其权限数量统计。
    """
    return {
        "success": True,
        "message": "获取资源类型列表成功",
        "data": [
            {
                "resource_type": "user",
                "description": "用户管理",
                "permission_count": 5
            },
            {
                "resource_type": "role",
                "description": "角色管理",
                "permission_count": 4
            },
            {
                "resource_type": "permission",
                "description": "权限管理",
                "permission_count": 3
            }
        ]
    }

@app.post(
    "/api/v1/permissions/check",
    response_model=SuccessResponse,
    summary="检查用户权限",
    description="批量检查当前用户是否具有指定权限",
    tags=["权限管理"],
    dependencies=[Depends(security)]
)
async def check_permissions(permission_data: PermissionCheckRequest):
    """
    检查用户权限接口

    - **permission_codes**: 权限代码列表

    批量检查当前用户是否具有指定的权限，返回每个权限的检查结果。
    """
    results = []
    for code in permission_data.permission_codes:
        results.append({
            "permission_code": code,
            "has_permission": True,  # 模拟检查结果
            "source": "role:admin"
        })

    return {
        "success": True,
        "message": "权限检查完成",
        "data": {
            "results": results,
            "checked_count": len(permission_data.permission_codes),
            "granted_count": len(results)
        }
    }

# ==================== 系统信息接口 ====================

@app.get(
    "/",
    summary="系统首页",
    description="返回系统基本信息",
    tags=["系统信息"]
)
async def root():
    """系统首页"""
    return {
        "message": "RBAC权限管理系统",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }

@app.get(
    "/health",
    summary="健康检查",
    description="系统健康状态检查",
    tags=["系统信息"]
)
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "message": "RBAC权限管理系统运行正常",
        "timestamp": datetime.now()
    }

@app.get(
    "/api/info",
    summary="API信息",
    description="获取API详细信息",
    tags=["系统信息"]
)
async def api_info():
    """API信息端点"""
    return {
        "api_name": "RBAC权限管理系统API",
        "version": "1.0.0",
        "description": "基于角色的访问控制权限管理系统",
        "controllers": {
            "auth": {
                "name": "认证管理",
                "endpoints": 5,
                "prefix": "/api/v1/auth"
            },
            "users": {
                "name": "用户管理",
                "endpoints": 5,
                "prefix": "/api/v1/users"
            },
            "roles": {
                "name": "角色管理",
                "endpoints": 4,
                "prefix": "/api/v1/roles"
            },
            "permissions": {
                "name": "权限管理",
                "endpoints": 4,
                "prefix": "/api/v1/permissions"
            }
        },
        "total_endpoints": 18,
        "features": [
            "JWT令牌认证",
            "基于角色的访问控制",
            "细粒度权限管理",
            "RESTful API设计",
            "自动API文档生成",
            "统一响应格式",
            "完整的错误处理"
        ]
    }

# ==================== 启动配置 ====================

if __name__ == "__main__":
    print("🚀 启动RBAC权限管理系统Swagger文档演示应用")
    print("=" * 60)
    print("📍 应用地址: http://localhost:8000")
    print("📚 Swagger文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("🔧 OpenAPI JSON: http://localhost:8000/openapi.json")
    print("💡 按 Ctrl+C 停止服务")
    print("-" * 60)

    uvicorn.run(
        "swagger_demo_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
