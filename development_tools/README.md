# 开发工具目录

本目录包含RBAC权限系统开发过程中使用的各种工具和测试文件。

## 📁 文件说明

### 验证工具
- `verify_environment.py` - 环境验证脚本，用于检查第一轮任务完成情况
- `test_fastapi.py` - FastAPI测试应用，用于验证新增依赖是否正常工作

### 文档报告
- `第一轮任务完成报告.md` - 第一轮任务的详细完成报告

## 🚀 使用方法

### 环境验证
```bash
python development_tools/verify_environment.py
```

### FastAPI测试
```bash
python development_tools/test_fastapi.py
# 然后访问 http://127.0.0.1:8000/docs 查看API文档
```

## 📋 说明

这些文件主要用于开发过程中的验证和测试，不是项目的核心功能代码。
将它们放在单独的目录中有助于保持项目结构的清晰性。
