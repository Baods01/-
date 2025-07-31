# RBAC权限管理系统 - Swagger API文档

## 📋 文档说明

本文档提供了完整的RBAC权限管理系统API文档演示应用，用于生成和查看Swagger文档。

## 🚀 快速启动

### 方法一：直接运行Python文件

```bash
# 进入任务7成果目录
cd 任务7成果

# 运行Swagger演示应用
python swagger_demo_app.py
```

### 方法二：使用uvicorn启动

```bash
# 进入任务7成果目录
cd 任务7成果

# 使用uvicorn启动
uvicorn swagger_demo_app:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 访问文档

启动成功后，可以通过以下地址访问API文档：

### Swagger UI (推荐用于截图)
```
http://localhost:8000/docs
```
- 交互式API文档
- 支持在线测试API
- 完整的接口描述和示例
- 美观的界面设计

### ReDoc文档
```
http://localhost:8000/redoc
```
- 更加详细的文档展示
- 适合阅读和打印
- 清晰的层级结构

### OpenAPI JSON
```
http://localhost:8000/openapi.json
```
- 原始的OpenAPI规范文件
- 可用于生成其他格式的文档

### 系统信息
```
http://localhost:8000/api/info
```
- API系统信息
- 接口统计数据

## 📊 API接口概览

### 🔐 认证管理 (5个接口)
- **POST** `/api/v1/auth/login` - 用户登录
- **POST** `/api/v1/auth/logout` - 用户登出
- **POST** `/api/v1/auth/refresh` - 刷新令牌
- **GET** `/api/v1/auth/me` - 获取当前用户信息
- **PUT** `/api/v1/auth/password` - 修改密码

### 👥 用户管理 (5个接口)
- **POST** `/api/v1/users` - 创建用户
- **GET** `/api/v1/users/{id}` - 获取用户详情
- **PUT** `/api/v1/users/{id}` - 更新用户信息
- **DELETE** `/api/v1/users/{id}` - 删除用户
- **GET** `/api/v1/users` - 获取用户列表

### 🎭 角色管理 (4个接口)
- **POST** `/api/v1/roles` - 创建角色
- **GET** `/api/v1/roles` - 获取角色列表
- **GET** `/api/v1/roles/{id}` - 获取角色详情
- **POST** `/api/v1/roles/{id}/permissions` - 分配权限给角色

### 🔑 权限管理 (4个接口)
- **GET** `/api/v1/permissions/tree` - 获取权限树结构
- **GET** `/api/v1/permissions` - 获取权限列表
- **GET** `/api/v1/permissions/resource-types` - 获取资源类型
- **POST** `/api/v1/permissions/check` - 检查用户权限

**总计：18个API接口**

## 🎯 文档特性

### 完整的接口描述
- ✅ 详细的接口功能说明
- ✅ 完整的参数描述和示例
- ✅ 标准的响应格式说明
- ✅ HTTP状态码说明
- ✅ 错误响应示例

### 数据模型定义
- ✅ 完整的请求模型定义
- ✅ 详细的响应模型定义
- ✅ 字段类型和验证规则
- ✅ 示例数据展示

### 安全认证
- ✅ JWT Bearer令牌认证
- ✅ 安全接口标识
- ✅ 认证流程说明

### 接口分组
- ✅ 按功能模块分组
- ✅ 清晰的标签分类
- ✅ 便于查找和使用

## 📸 截图指南

### 推荐截图内容

#### 1. 系统概览截图
- 访问：`http://localhost:8000/docs`
- 截图内容：整个Swagger UI界面
- 展示：系统标题、描述、接口分组

#### 2. 认证管理接口截图
- 展开：认证管理标签
- 截图内容：5个认证相关接口
- 重点：登录接口的详细信息

#### 3. 用户管理接口截图
- 展开：用户管理标签
- 截图内容：5个用户管理接口
- 重点：创建用户接口的参数定义

#### 4. 角色管理接口截图
- 展开：角色管理标签
- 截图内容：4个角色管理接口
- 重点：权限分配接口

#### 5. 权限管理接口截图
- 展开：权限管理标签
- 截图内容：4个权限管理接口
- 重点：权限树结构接口

#### 6. 数据模型截图
- 滚动到页面底部
- 截图内容：Schemas部分
- 展示：完整的数据模型定义

#### 7. 接口详情截图
- 点击任意接口展开
- 截图内容：接口详细信息
- 包含：参数、响应、示例

### 截图技巧
1. **浏览器设置**：使用Chrome或Firefox，设置合适的窗口大小
2. **界面展示**：确保接口分组都能看到，适当滚动页面
3. **高清截图**：使用高分辨率截图，确保文字清晰
4. **完整展示**：尽量在一个截图中展示完整的功能模块

## 🔧 自定义配置

### 修改端口
如果8000端口被占用，可以修改启动端口：

```python
# 在swagger_demo_app.py文件末尾修改
uvicorn.run(
    "swagger_demo_app:app",
    host="0.0.0.0",
    port=8080,  # 修改为其他端口
    reload=True,
    log_level="info"
)
```

### 修改文档信息
可以在文件开头的FastAPI应用配置中修改：

```python
app = FastAPI(
    title="您的系统名称",
    description="您的系统描述",
    version="您的版本号",
    # ... 其他配置
)
```

## 🚨 注意事项

### 演示应用说明
- 这是一个**演示应用**，仅用于生成API文档
- 所有接口都返回**模拟数据**，不连接真实数据库
- 认证检查是**模拟的**，实际不验证令牌

### 生产环境使用
- 生产环境请使用完整的RBAC系统代码
- 本演示应用仅用于文档展示和截图
- 不要在生产环境中使用此演示应用

### 依赖要求
确保安装了以下Python包：
```bash
pip install fastapi uvicorn pydantic
```

## 📞 技术支持

如果在启动或使用过程中遇到问题：

1. **检查Python版本**：确保使用Python 3.9+
2. **检查依赖安装**：确保安装了必要的包
3. **检查端口占用**：确保8000端口未被占用
4. **查看错误日志**：注意控制台的错误信息

---

**文档创建时间**：2025-07-22  
**适用版本**：RBAC权限管理系统 v1.0.0  
**维护团队**：RBAC System Development Team
