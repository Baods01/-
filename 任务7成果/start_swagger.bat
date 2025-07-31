@echo off
echo ========================================
echo RBAC权限管理系统 - Swagger文档启动器
echo ========================================
echo.

echo 正在启动Swagger文档演示应用...
echo.

echo 📍 应用地址: http://localhost:8000
echo 📚 Swagger文档: http://localhost:8000/docs
echo 📖 ReDoc文档: http://localhost:8000/redoc
echo 🔧 OpenAPI JSON: http://localhost:8000/openapi.json
echo.

echo 💡 启动后请在浏览器中访问上述地址获取API文档
echo 💡 按 Ctrl+C 可以停止服务
echo.

echo ========================================
echo 正在启动服务...
echo ========================================

python swagger_demo_app.py

pause
