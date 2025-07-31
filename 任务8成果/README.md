# RBAC权限管理系统前端

## 📋 项目介绍

RBAC权限管理系统前端是一个基于Vue 3和Element Plus构建的现代化权限管理系统，采用基于角色的访问控制(RBAC)模型，为企业提供完整的用户权限管理解决方案。

### 🎯 核心功能特性

#### 用户管理
- ✅ 用户注册、登录、登出
- ✅ 用户信息管理（增删改查）
- ✅ 用户状态管理（启用/禁用）
- ✅ 批量用户操作
- ✅ 用户搜索和过滤

#### 角色管理
- ✅ 角色创建和管理
- ✅ 角色权限分配
- ✅ 角色用户关联
- ✅ 角色状态管理
- ✅ 角色搜索和过滤

#### 权限管理
- ✅ 权限树形结构展示
- ✅ 权限详情查看
- ✅ 权限搜索和过滤
- ✅ 权限状态管理
- ✅ 权限关联角色查看

#### 系统功能
- ✅ 仪表板数据统计
- ✅ 个人中心管理
- ✅ 密码修改功能
- ✅ 操作日志记录
- ✅ 系统设置管理

#### 用户体验
- ✅ 响应式设计，支持多设备
- ✅ 暗色主题支持
- ✅ 国际化支持
- ✅ 无障碍访问支持
- ✅ 离线功能支持

## 🛠️ 技术栈

### 前端框架
- **Vue 3.4+** - 渐进式JavaScript框架
- **Vue Router 4.2+** - 官方路由管理器
- **Pinia 2.1+** - 状态管理库

### UI组件库
- **Element Plus 2.4+** - Vue 3组件库
- **@element-plus/icons-vue 2.3+** - Element Plus图标库

### 开发工具
- **Vite 5.0+** - 现代化构建工具
- **Vitest** - 单元测试框架
- **Sass 1.69+** - CSS预处理器

### 工具库
- **Axios 1.6+** - HTTP客户端
- **Lodash 4.17+** - JavaScript工具库
- **Day.js 1.11+** - 日期处理库

### 开发依赖
- **@vitejs/plugin-vue 4.5+** - Vue插件
- **@vue/test-utils 2.4+** - Vue测试工具
- **jsdom 23.0+** - DOM环境模拟

## 📦 安装和运行

### 环境要求
- **Node.js**: 18.0+ 或 20.0+
- **npm**: 9.0+ 或 **yarn**: 1.22+ 或 **pnpm**: 8.0+
- **现代浏览器**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd rbac-frontend
```

2. **安装依赖**
```bash
# 使用npm
npm install

# 或使用yarn
yarn install

# 或使用pnpm
pnpm install
```

3. **启动开发服务器**
```bash
# 使用npm
npm run dev

# 或使用yarn
yarn dev

# 或使用pnpm
pnpm dev
```

4. **访问应用**
打开浏览器访问 `http://localhost:5173`

### 构建生产版本

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 运行测试

```bash
# 运行单元测试
npm run test

# 运行测试并生成覆盖率报告
npm run test:coverage

# 运行测试UI界面
npm run test:ui
```

## 📁 项目结构

```
rbac-frontend/
├── public/                 # 静态资源
│   ├── favicon.ico
│   └── index.html
├── src/                    # 源代码
│   ├── api/               # API接口
│   │   ├── auth.js        # 认证接口
│   │   ├── user.js        # 用户接口
│   │   ├── role.js        # 角色接口
│   │   ├── permission.js  # 权限接口
│   │   └── request.js     # 请求拦截器
│   ├── assets/            # 静态资源
│   │   ├── images/        # 图片资源
│   │   └── icons/         # 图标资源
│   ├── components/        # 公共组件
│   │   ├── common/        # 通用组件
│   │   ├── layout/        # 布局组件
│   │   └── index.js       # 组件导出
│   ├── directives/        # 自定义指令
│   │   ├── permission.js  # 权限指令
│   │   └── index.js       # 指令导出
│   ├── router/            # 路由配置
│   │   ├── index.js       # 路由主文件
│   │   └── guards.js      # 路由守卫
│   ├── store/             # 状态管理
│   │   ├── modules/       # 状态模块
│   │   │   ├── auth.js    # 认证状态
│   │   │   ├── user.js    # 用户状态
│   │   │   └── app.js     # 应用状态
│   │   └── index.js       # 状态导出
│   ├── styles/            # 样式文件
│   │   ├── common.scss    # 公共样式
│   │   ├── variables.scss # 变量定义
│   │   └── themes/        # 主题样式
│   ├── utils/             # 工具函数
│   │   ├── auth.js        # 认证工具
│   │   ├── date.js        # 日期工具
│   │   ├── errorHandler.js # 错误处理
│   │   ├── performance.js  # 性能监控
│   │   ├── compatibility.js # 兼容性处理
│   │   └── index.js       # 工具导出
│   ├── views/             # 页面组件
│   │   ├── auth/          # 认证页面
│   │   │   ├── Login.vue  # 登录页面
│   │   │   └── ChangePassword.vue # 密码修改
│   │   ├── dashboard/     # 仪表板
│   │   │   └── Dashboard.vue
│   │   ├── user/          # 用户管理
│   │   │   ├── UserList.vue
│   │   │   └── UserEdit.vue
│   │   ├── role/          # 角色管理
│   │   │   ├── RoleList.vue
│   │   │   └── RoleEdit.vue
│   │   ├── permission/    # 权限管理
│   │   │   ├── PermissionTree.vue
│   │   │   └── PermissionList.vue
│   │   └── profile/       # 个人中心
│   │       └── Profile.vue
│   ├── App.vue            # 根组件
│   └── main.js            # 入口文件
├── tests/                 # 测试文件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── reports/           # 测试报告
├── docs/                  # 文档
├── .env.example           # 环境变量示例
├── .gitignore             # Git忽略文件
├── index.html             # HTML模板
├── package.json           # 项目配置
├── vite.config.js         # Vite配置
└── vitest.config.js       # 测试配置
```

## 🔧 配置说明

### 环境变量

创建 `.env.local` 文件配置环境变量：

```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 应用标题
VITE_APP_TITLE=RBAC权限管理系统

# 是否启用Mock数据
VITE_USE_MOCK=false

# 是否启用调试模式
VITE_DEBUG=true
```

### API配置

在 `src/api/request.js` 中配置API请求：

```javascript
// 配置API基础URL
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 配置请求超时时间
const timeout = 10000
```

## 🎨 主题定制

### 自定义主题色彩

在 `src/styles/variables.scss` 中定义主题变量：

```scss
// 主色调
$primary-color: #409eff;
$success-color: #67c23a;
$warning-color: #e6a23c;
$danger-color: #f56c6c;

// 背景色
$bg-color: #ffffff;
$bg-color-dark: #1d1e1f;
```

### 暗色主题

系统支持自动暗色主题切换，可在个人设置中手动切换。

## 📱 浏览器支持

| 浏览器 | 版本要求 | 支持状态 |
|--------|----------|----------|
| Chrome | 90+ | ✅ 完全支持 |
| Firefox | 88+ | ✅ 完全支持 |
| Safari | 14+ | ✅ 完全支持 |
| Edge | 90+ | ✅ 完全支持 |
| IE | 不支持 | ❌ 不支持 |

## 🔒 安全特性

- ✅ JWT Token认证
- ✅ 路由权限控制
- ✅ 按钮级权限控制
- ✅ XSS攻击防护
- ✅ CSRF攻击防护
- ✅ 敏感信息加密存储

## 📈 性能特性

- ✅ 代码分割和懒加载
- ✅ 图片懒加载
- ✅ 缓存优化
- ✅ 压缩优化
- ✅ CDN加速支持

## 🌐 国际化

系统支持多语言，当前支持：
- 🇨🇳 简体中文
- 🇺🇸 English（计划中）

## 📞 技术支持

如有问题，请通过以下方式联系：

- 📧 邮箱：support@rbac-system.com
- 📱 电话：400-123-4567
- 💬 在线客服：https://support.rbac-system.com

## 📄 许可证

本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。

---

**开发团队**：RBAC Frontend Development Team  
**版本**：v1.0.0  
**最后更新**：2025-07-25
