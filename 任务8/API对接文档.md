# 任务8：前端开发 - API对接文档

## 📋 API对接概述

**后端API地址**：http://localhost:8000  
**API文档地址**：http://localhost:8000/docs  
**认证方式**：JWT Bearer Token  
**数据格式**：JSON  

## 🔐 认证机制

### JWT令牌认证
```javascript
// 请求头格式
headers: {
  'Authorization': 'Bearer ' + accessToken,
  'Content-Type': 'application/json'
}
```

### 令牌管理
- **访问令牌**：有效期15分钟
- **刷新令牌**：有效期7天
- **自动刷新**：访问令牌过期时自动刷新
- **登出清理**：清除所有令牌信息

## 📊 API接口清单

### 🔐 认证管理接口 (5个)

#### 1. 用户登录
```javascript
// POST /api/v1/auth/login
const loginAPI = {
  method: 'POST',
  url: '/api/v1/auth/login',
  data: {
    username: 'admin',
    password: 'admin123',
    remember_me: true
  }
}

// 响应数据
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

#### 2. 用户登出
```javascript
// POST /api/v1/auth/logout
const logoutAPI = {
  method: 'POST',
  url: '/api/v1/auth/logout',
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 3. 刷新令牌
```javascript
// POST /api/v1/auth/refresh
const refreshAPI = {
  method: 'POST',
  url: '/api/v1/auth/refresh',
  data: {
    refresh_token: refreshToken
  }
}
```

#### 4. 获取当前用户信息
```javascript
// GET /api/v1/auth/me
const getCurrentUserAPI = {
  method: 'GET',
  url: '/api/v1/auth/me',
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 5. 修改密码
```javascript
// PUT /api/v1/auth/password
const changePasswordAPI = {
  method: 'PUT',
  url: '/api/v1/auth/password',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    old_password: 'oldpass123',
    new_password: 'newpass123'
  }
}
```

### 👥 用户管理接口 (5个)

#### 1. 创建用户
```javascript
// POST /api/v1/users
const createUserAPI = {
  method: 'POST',
  url: '/api/v1/users',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    username: 'newuser',
    email: 'newuser@example.com',
    password: 'password123',
    nickname: '新用户',
    phone: '13800138000'
  }
}
```

#### 2. 获取用户详情
```javascript
// GET /api/v1/users/{id}
const getUserAPI = {
  method: 'GET',
  url: '/api/v1/users/1',
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 3. 更新用户信息
```javascript
// PUT /api/v1/users/{id}
const updateUserAPI = {
  method: 'PUT',
  url: '/api/v1/users/1',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    nickname: '更新的昵称',
    phone: '13900139000'
  }
}
```

#### 4. 删除用户
```javascript
// DELETE /api/v1/users/{id}
const deleteUserAPI = {
  method: 'DELETE',
  url: '/api/v1/users/1',
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 5. 获取用户列表
```javascript
// GET /api/v1/users
const getUsersAPI = {
  method: 'GET',
  url: '/api/v1/users',
  params: {
    page: 1,
    size: 20,
    search: 'admin',
    status: 1
  },
  headers: {
    'Authorization': 'Bearer ' + token
  }
}

// 响应数据格式
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
        "created_at": "2025-07-22T10:00:00Z"
      }
    ],
    "pagination": {
      "total": 100,
      "page": 1,
      "size": 20,
      "pages": 5
    }
  }
}
```

### 🎭 角色管理接口 (4个)

#### 1. 创建角色
```javascript
// POST /api/v1/roles
const createRoleAPI = {
  method: 'POST',
  url: '/api/v1/roles',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    role_name: '管理员',
    role_code: 'admin',
    description: '系统管理员角色'
  }
}
```

#### 2. 获取角色列表
```javascript
// GET /api/v1/roles
const getRolesAPI = {
  method: 'GET',
  url: '/api/v1/roles',
  params: {
    page: 1,
    size: 20,
    search: 'admin',
    status: 1
  },
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 3. 获取角色详情
```javascript
// GET /api/v1/roles/{id}
const getRoleAPI = {
  method: 'GET',
  url: '/api/v1/roles/1',
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 4. 分配权限给角色
```javascript
// POST /api/v1/roles/{id}/permissions
const assignPermissionsAPI = {
  method: 'POST',
  url: '/api/v1/roles/1/permissions',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    permission_ids: [1, 2, 3, 4]
  }
}
```

### 🔑 权限管理接口 (4个)

#### 1. 获取权限树结构
```javascript
// GET /api/v1/permissions/tree
const getPermissionTreeAPI = {
  method: 'GET',
  url: '/api/v1/permissions/tree',
  params: {
    resource_type: 'user'
  },
  headers: {
    'Authorization': 'Bearer ' + token
  }
}

// 响应数据格式
{
  "success": true,
  "message": "获取权限树成功",
  "data": [
    {
      "id": 1,
      "permission_name": "用户管理",
      "permission_code": "user",
      "resource_type": "user",
      "children": [
        {
          "id": 2,
          "permission_name": "创建用户",
          "permission_code": "user:create",
          "resource_type": "user",
          "children": []
        }
      ]
    }
  ]
}
```

#### 2. 获取权限列表
```javascript
// GET /api/v1/permissions
const getPermissionsAPI = {
  method: 'GET',
  url: '/api/v1/permissions',
  params: {
    page: 1,
    size: 20,
    search: 'user',
    resource_type: 'user',
    status: 1
  },
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 3. 获取资源类型列表
```javascript
// GET /api/v1/permissions/resource-types
const getResourceTypesAPI = {
  method: 'GET',
  url: '/api/v1/permissions/resource-types',
  headers: {
    'Authorization': 'Bearer ' + token
  }
}
```

#### 4. 检查用户权限
```javascript
// POST /api/v1/permissions/check
const checkPermissionsAPI = {
  method: 'POST',
  url: '/api/v1/permissions/check',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    permission_codes: ['user:create', 'user:read', 'user:update']
  }
}
```

## 🛠️ API封装实现

### 1. HTTP客户端配置
```javascript
// api/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import router from '@/router'

const request = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    const token = userStore.token
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const { data } = response
    
    if (data.success) {
      return data
    } else {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
  },
  async error => {
    const { response } = error
    
    if (response?.status === 401) {
      // 令牌过期，尝试刷新
      const userStore = useUserStore()
      try {
        await userStore.refreshToken()
        // 重新发送原请求
        return request(error.config)
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        userStore.logout()
        router.push('/login')
      }
    } else {
      ElMessage.error(response?.data?.message || '请求失败')
    }
    
    return Promise.reject(error)
  }
)

export default request
```

### 2. API模块封装
```javascript
// api/auth.js
import request from './request'

export const authAPI = {
  // 用户登录
  login(data) {
    return request.post('/api/v1/auth/login', data)
  },
  
  // 用户登出
  logout() {
    return request.post('/api/v1/auth/logout')
  },
  
  // 刷新令牌
  refreshToken(data) {
    return request.post('/api/v1/auth/refresh', data)
  },
  
  // 获取当前用户信息
  getCurrentUser() {
    return request.get('/api/v1/auth/me')
  },
  
  // 修改密码
  changePassword(data) {
    return request.put('/api/v1/auth/password', data)
  }
}
```

```javascript
// api/user.js
import request from './request'

export const userAPI = {
  // 获取用户列表
  getUsers(params) {
    return request.get('/api/v1/users', { params })
  },
  
  // 获取用户详情
  getUser(id) {
    return request.get(`/api/v1/users/${id}`)
  },
  
  // 创建用户
  createUser(data) {
    return request.post('/api/v1/users', data)
  },
  
  // 更新用户
  updateUser(id, data) {
    return request.put(`/api/v1/users/${id}`, data)
  },
  
  // 删除用户
  deleteUser(id) {
    return request.delete(`/api/v1/users/${id}`)
  }
}
```

## 🔄 错误处理

### 1. HTTP状态码处理
- **200**: 请求成功
- **201**: 创建成功
- **400**: 请求参数错误
- **401**: 未授权（令牌无效）
- **403**: 权限不足
- **404**: 资源不存在
- **422**: 数据验证失败
- **500**: 服务器内部错误

### 2. 业务错误处理
```javascript
// 统一错误处理
const handleError = (error) => {
  if (error.response) {
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        ElMessage.error(data.message || '请求参数错误')
        break
      case 401:
        ElMessage.error('登录已过期，请重新登录')
        // 跳转到登录页
        break
      case 403:
        ElMessage.error('权限不足')
        break
      case 404:
        ElMessage.error('资源不存在')
        break
      case 422:
        ElMessage.error(data.message || '数据验证失败')
        break
      default:
        ElMessage.error('请求失败')
    }
  } else {
    ElMessage.error('网络错误')
  }
}
```

## 📝 使用示例

### 1. 在组件中使用API
```vue
<script setup>
import { ref, onMounted } from 'vue'
import { userAPI } from '@/api/user'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await userAPI.getUsers({
      page: 1,
      size: 20
    })
    users.value = response.data.items
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>
```

### 2. 在Store中使用API
```javascript
// store/user.js
import { defineStore } from 'pinia'
import { authAPI } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token')
  }),
  
  actions: {
    async login(credentials) {
      try {
        const response = await authAPI.login(credentials)
        const { access_token, refresh_token, user } = response.data
        
        this.token = access_token
        this.refreshToken = refresh_token
        this.user = user
        
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        
        return response
      } catch (error) {
        throw error
      }
    }
  }
})
```

---

**文档创建时间**：2025-07-22  
**API版本**：v1.0.0  
**后端服务**：RBAC权限管理系统  
**维护团队**：RBAC Frontend Development Team
