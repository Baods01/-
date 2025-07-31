# RBAC权限管理系统前端开发指南

## 📋 开发指南概述

本文档为RBAC权限管理系统前端的开发指南，包含开发环境搭建、代码规范、贡献指南和API使用说明，帮助开发者快速上手项目开发。

## 🛠️ 开发环境搭建

### 1. 系统要求

#### 开发环境
- **操作系统**: Windows 10+, macOS 12+, Linux (Ubuntu 20.04+)
- **Node.js**: 18.0+ 或 20.0+ (推荐使用LTS版本)
- **包管理器**: npm 9.0+ / yarn 1.22+ / pnpm 8.0+
- **编辑器**: VS Code (推荐) / WebStorm / Vim

#### 推荐工具
- **Git**: 版本控制
- **Chrome DevTools**: 调试工具
- **Vue DevTools**: Vue调试扩展
- **Postman**: API测试工具

### 2. 环境安装

#### 2.1 安装Node.js
```bash
# 使用nvm管理Node.js版本 (推荐)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# 或直接下载安装
# https://nodejs.org/
```

#### 2.2 安装包管理器
```bash
# 安装yarn (可选)
npm install -g yarn

# 安装pnpm (可选)
npm install -g pnpm
```

#### 2.3 安装开发工具
```bash
# 全局安装开发工具
npm install -g @vue/cli
npm install -g vite
npm install -g vitest
```

### 3. 项目设置

#### 3.1 克隆项目
```bash
git clone <repository-url>
cd rbac-frontend
```

#### 3.2 安装依赖
```bash
npm install
```

#### 3.3 配置环境变量
```bash
# 复制环境配置
cp .env.example .env.local

# 编辑本地配置
vim .env.local
```

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=RBAC权限管理系统
VITE_USE_MOCK=true
VITE_DEBUG=true
```

#### 3.4 启动开发服务器
```bash
npm run dev
```

访问 `http://localhost:5173` 查看应用。

### 4. VS Code配置

#### 4.1 推荐扩展
```json
{
  "recommendations": [
    "vue.volar",
    "vue.vscode-typescript-vue-plugin",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-json",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense"
  ]
}
```

#### 4.2 工作区设置
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "vue.codeActions.enabled": true
}
```

## 📝 代码规范

### 1. 命名规范

#### 1.1 文件命名
```bash
# 组件文件 - PascalCase
UserList.vue
UserEdit.vue
DataTable.vue

# 工具文件 - camelCase
auth.js
dateUtils.js
errorHandler.js

# 页面文件 - PascalCase
Dashboard.vue
Login.vue
```

#### 1.2 变量命名
```javascript
// 变量和函数 - camelCase
const userName = 'admin'
const getUserInfo = () => {}

// 常量 - UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8000'
const MAX_RETRY_COUNT = 3

// 组件名 - PascalCase
const UserList = defineComponent({})
```

#### 1.3 CSS类命名
```scss
// BEM命名规范
.user-list {}
.user-list__item {}
.user-list__item--active {}
.user-list__button {}
.user-list__button--disabled {}
```

### 2. Vue组件规范

#### 2.1 组件结构
```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup>
// 导入
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// Props定义
const props = defineProps({
  title: {
    type: String,
    required: true
  }
})

// Emits定义
const emit = defineEmits(['update', 'delete'])

// 响应式数据
const loading = ref(false)

// 计算属性
const displayTitle = computed(() => {
  return props.title.toUpperCase()
})

// 方法
const handleClick = () => {
  emit('update')
}

// 生命周期
onMounted(() => {
  // 初始化逻辑
})

// 暴露给模板
defineExpose({
  handleClick
})
</script>

<style scoped>
/* 组件样式 */
</style>
```

#### 2.2 Props规范
```javascript
// 完整的Props定义
const props = defineProps({
  // 基础类型
  title: String,
  count: Number,
  isActive: Boolean,
  
  // 带默认值
  size: {
    type: String,
    default: 'medium'
  },
  
  // 必需属性
  id: {
    type: [String, Number],
    required: true
  },
  
  // 自定义验证
  status: {
    type: String,
    validator: (value) => ['active', 'inactive'].includes(value)
  },
  
  // 对象类型
  user: {
    type: Object,
    default: () => ({})
  },
  
  // 数组类型
  items: {
    type: Array,
    default: () => []
  }
})
```

### 3. JavaScript规范

#### 3.1 ES6+特性使用
```javascript
// 使用const/let，避免var
const apiUrl = 'http://localhost:8000'
let currentUser = null

// 使用箭头函数
const getUserList = async () => {
  try {
    const response = await api.get('/users')
    return response.data
  } catch (error) {
    console.error('获取用户列表失败:', error)
    throw error
  }
}

// 使用解构赋值
const { name, email } = user
const [first, ...rest] = items

// 使用模板字符串
const message = `欢迎 ${user.name}！`

// 使用可选链
const userName = user?.profile?.name ?? '未知用户'
```

#### 3.2 异步处理
```javascript
// 使用async/await
const fetchUserData = async (userId) => {
  try {
    const user = await userAPI.getUser(userId)
    const roles = await roleAPI.getUserRoles(userId)
    return { user, roles }
  } catch (error) {
    handleError(error)
    throw error
  }
}

// 错误处理
const handleError = (error) => {
  if (error.response?.status === 401) {
    // 处理认证错误
    router.push('/login')
  } else {
    // 显示错误消息
    ElMessage.error(error.message)
  }
}
```

### 4. CSS/SCSS规范

#### 4.1 样式组织
```scss
// 变量定义
$primary-color: #409eff;
$border-radius: 4px;

// 混入定义
@mixin flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

// 组件样式
.user-list {
  padding: 20px;
  
  &__header {
    @include flex-center;
    margin-bottom: 16px;
  }
  
  &__item {
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: $border-radius;
    
    &:hover {
      background-color: #f5f5f5;
    }
    
    &--active {
      border-color: $primary-color;
    }
  }
}
```

#### 4.2 响应式设计
```scss
// 断点定义
$breakpoints: (
  mobile: 768px,
  tablet: 1024px,
  desktop: 1200px
);

// 响应式混入
@mixin respond-to($breakpoint) {
  @media (max-width: map-get($breakpoints, $breakpoint)) {
    @content;
  }
}

// 使用示例
.user-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  
  @include respond-to(tablet) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @include respond-to(mobile) {
    grid-template-columns: 1fr;
  }
}
```

## 🔧 开发工具配置

### 1. ESLint配置

```javascript
// .eslintrc.js
module.exports = {
  extends: [
    '@vue/eslint-config-typescript',
    'plugin:vue/vue3-recommended'
  ],
  rules: {
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'warn',
    '@typescript-eslint/no-unused-vars': 'error',
    'prefer-const': 'error',
    'no-var': 'error'
  }
}
```

### 2. Prettier配置

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "none",
  "printWidth": 100,
  "endOfLine": "lf"
}
```

### 3. Git Hooks配置

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged",
      "commit-msg": "commitlint -E HUSKY_GIT_PARAMS"
    }
  },
  "lint-staged": {
    "*.{js,vue,ts}": ["eslint --fix", "prettier --write"],
    "*.{css,scss,vue}": ["prettier --write"]
  }
}
```

## 📚 API使用说明

### 1. API接口规范

#### 1.1 请求格式
```javascript
// GET请求
const getUserList = (params) => {
  return request({
    url: '/api/v1/users',
    method: 'GET',
    params
  })
}

// POST请求
const createUser = (data) => {
  return request({
    url: '/api/v1/users',
    method: 'POST',
    data
  })
}

// PUT请求
const updateUser = (id, data) => {
  return request({
    url: `/api/v1/users/${id}`,
    method: 'PUT',
    data
  })
}

// DELETE请求
const deleteUser = (id) => {
  return request({
    url: `/api/v1/users/${id}`,
    method: 'DELETE'
  })
}
```

#### 1.2 响应格式
```javascript
// 成功响应
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 响应数据
  },
  "timestamp": "2025-07-25T10:00:00Z"
}

// 错误响应
{
  "code": 400,
  "message": "请求参数错误",
  "error": {
    "field": "username",
    "message": "用户名不能为空"
  },
  "timestamp": "2025-07-25T10:00:00Z"
}
```

### 2. 状态管理

#### 2.1 Pinia Store使用
```javascript
// stores/user.js
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
  // 状态
  const currentUser = ref(null)
  const userList = ref([])
  const loading = ref(false)
  
  // 计算属性
  const isLoggedIn = computed(() => !!currentUser.value)
  
  // 方法
  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await authAPI.login(credentials)
      currentUser.value = response.data.user
      return response
    } finally {
      loading.value = false
    }
  }
  
  const logout = () => {
    currentUser.value = null
    router.push('/login')
  }
  
  return {
    currentUser,
    userList,
    loading,
    isLoggedIn,
    login,
    logout
  }
})
```

#### 2.2 在组件中使用
```vue
<script setup>
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 使用状态
const { currentUser, isLoggedIn } = storeToRefs(userStore)

// 调用方法
const handleLogin = async () => {
  await userStore.login(credentials)
}
</script>
```

### 3. 路由配置

#### 3.1 路由定义
```javascript
// router/index.js
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/Dashboard.vue'),
    meta: {
      title: '仪表板',
      requiresAuth: true,
      permissions: ['dashboard:view']
    }
  }
]
```

#### 3.2 路由守卫
```javascript
// router/guards.js
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 检查认证
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
    return
  }
  
  // 检查权限
  if (to.meta.permissions) {
    const hasPermission = await checkPermissions(to.meta.permissions)
    if (!hasPermission) {
      next('/403')
      return
    }
  }
  
  next()
})
```

## 🧪 测试指南

### 1. 单元测试

#### 1.1 组件测试
```javascript
// tests/unit/components/UserList.test.js
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import UserList from '@/components/UserList.vue'

describe('UserList', () => {
  it('应该渲染用户列表', () => {
    const users = [
      { id: 1, name: '张三', email: 'zhangsan@example.com' }
    ]
    
    const wrapper = mount(UserList, {
      props: { users }
    })
    
    expect(wrapper.find('.user-item').exists()).toBe(true)
    expect(wrapper.text()).toContain('张三')
  })
  
  it('应该触发删除事件', async () => {
    const wrapper = mount(UserList, {
      props: { users: [] }
    })
    
    await wrapper.find('.delete-btn').trigger('click')
    
    expect(wrapper.emitted('delete')).toBeTruthy()
  })
})
```

#### 1.2 工具函数测试
```javascript
// tests/unit/utils/auth.test.js
import { describe, it, expect } from 'vitest'
import { validatePassword, formatUserName } from '@/utils/auth'

describe('auth utils', () => {
  describe('validatePassword', () => {
    it('应该验证强密码', () => {
      expect(validatePassword('Password123!')).toBe(true)
    })
    
    it('应该拒绝弱密码', () => {
      expect(validatePassword('123456')).toBe(false)
    })
  })
})
```

### 2. 集成测试

```javascript
// tests/integration/login.test.js
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import Login from '@/views/auth/Login.vue'

describe('Login Integration', () => {
  it('应该完成登录流程', async () => {
    // Mock API
    vi.mock('@/api/auth', () => ({
      login: vi.fn().mockResolvedValue({
        data: { user: { name: '张三' }, token: 'mock-token' }
      })
    }))
    
    const wrapper = mount(Login)
    
    // 填写表单
    await wrapper.find('input[name="username"]').setValue('admin')
    await wrapper.find('input[name="password"]').setValue('password')
    
    // 提交表单
    await wrapper.find('form').trigger('submit')
    
    // 验证结果
    expect(wrapper.emitted('login-success')).toBeTruthy()
  })
})
```

## 🤝 贡献指南

### 1. 贡献流程

#### 1.1 Fork项目
```bash
# 1. Fork项目到个人仓库
# 2. 克隆个人仓库
git clone https://github.com/yourusername/rbac-frontend.git
cd rbac-frontend

# 3. 添加上游仓库
git remote add upstream https://github.com/original/rbac-frontend.git
```

#### 1.2 创建功能分支
```bash
# 创建并切换到功能分支
git checkout -b feature/user-management

# 或修复分支
git checkout -b fix/login-issue
```

#### 1.3 提交代码
```bash
# 添加文件
git add .

# 提交代码 (遵循提交规范)
git commit -m "feat: 添加用户管理功能"

# 推送到个人仓库
git push origin feature/user-management
```

#### 1.4 创建Pull Request
1. 在GitHub上创建Pull Request
2. 填写详细的PR描述
3. 等待代码审查
4. 根据反馈修改代码

### 2. 提交规范

#### 2.1 提交消息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 2.2 类型说明
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建工具或辅助工具的变动

#### 2.3 示例
```bash
feat(user): 添加用户搜索功能

- 添加搜索输入框
- 实现实时搜索
- 添加搜索结果高亮

Closes #123
```

### 3. 代码审查

#### 3.1 审查要点
- [ ] 代码符合项目规范
- [ ] 功能实现正确
- [ ] 测试覆盖充分
- [ ] 文档更新完整
- [ ] 性能影响评估

#### 3.2 审查流程
1. 自动化检查通过
2. 至少一位维护者审查
3. 所有讨论解决
4. 合并到主分支

## 📞 开发支持

### 技术交流
- 💬 开发者群：123456789
- 📧 邮箱：dev@rbac-system.com
- 📖 文档：https://docs.rbac-system.com
- 🐛 问题反馈：https://github.com/rbac-system/issues

### 学习资源
- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Vite 文档](https://vitejs.dev/)
- [Pinia 文档](https://pinia.vuejs.org/)

---

**开发团队**：RBAC Frontend Development Team  
**文档版本**：v1.0.0  
**最后更新**：2025-07-25
