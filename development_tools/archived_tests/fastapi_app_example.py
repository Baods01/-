#!/usr/bin/env python3
"""
FastAPI应用示例

展示如何使用第10轮开发的API控制器创建完整的FastAPI应用。

Author: RBAC System Development Team
Created: 2025-07-22
Version: 1.0.0
"""

import sys
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例
    
    Returns:
        FastAPI: 配置好的FastAPI应用
    """
    # 创建FastAPI应用
    app = FastAPI(
        title="RBAC权限管理系统",
        description="基于角色的访问控制系统API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册API路由
    try:
        from api.controllers import api_router
        app.include_router(api_router)
        print("✅ API控制器路由注册成功")
    except Exception as e:
        print(f"❌ API控制器路由注册失败: {str(e)}")
        # 在开发环境中，我们可以继续运行，但会显示错误
    
    # 添加根路径处理
    @app.get("/")
    async def root():
        """根路径，返回API信息"""
        return {
            "message": "RBAC权限管理系统API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    
    # 添加健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "message": "RBAC权限管理系统运行正常"
        }
    
    # 添加API信息端点
    @app.get("/api/info")
    async def api_info():
        """API信息端点"""
        return {
            "api_name": "RBAC权限管理系统API",
            "version": "1.0.0",
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
                "完整的CRUD操作",
                "统一的响应格式",
                "完善的权限控制",
                "详细的参数验证",
                "统一的错误处理",
                "完整的API文档"
            ]
        }
    
    # 全局异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器"""
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "服务器内部错误",
                "error": str(exc),
                "path": str(request.url)
            }
        )
    
    return app


def main():
    """主函数，用于测试应用创建"""
    print("🚀 创建FastAPI应用示例")
    print("=" * 50)
    
    try:
        # 创建应用
        app = create_app()
        print("✅ FastAPI应用创建成功")
        
        # 显示应用信息
        print(f"📋 应用信息:")
        print(f"  - 标题: {app.title}")
        print(f"  - 描述: {app.description}")
        print(f"  - 版本: {app.version}")
        print(f"  - 文档地址: {app.docs_url}")
        print(f"  - ReDoc地址: {app.redoc_url}")
        
        # 显示路由信息
        routes = app.routes
        print(f"  - 注册路由数: {len(routes)}")
        
        # 显示部分路由
        api_routes = [route for route in routes if hasattr(route, 'path') and route.path.startswith('/api/v1')]
        if api_routes:
            print(f"  - API路由数: {len(api_routes)}")
            print("  - API路由示例:")
            for route in api_routes[:5]:  # 只显示前5个
                if hasattr(route, 'methods'):
                    methods = list(route.methods) if route.methods else ['GET']
                    print(f"    {methods[0]} {route.path}")
            if len(api_routes) > 5:
                print(f"    ... 还有 {len(api_routes) - 5} 个API路由")
        
        print("\n🎯 FastAPI应用示例创建完成！")
        print("💡 使用方法:")
        print("  1. 运行: python development_tools/fastapi_app_example.py --run")
        print("  2. 访问: http://localhost:8000")
        print("  3. 文档: http://localhost:8000/docs")
        print("  4. ReDoc: http://localhost:8000/redoc")
        
        return app
        
    except Exception as e:
        print(f"❌ FastAPI应用创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def run_server():
    """运行开发服务器"""
    print("🚀 启动FastAPI开发服务器")
    print("=" * 50)
    
    app = create_app()
    if app:
        print("✅ 应用创建成功，启动服务器...")
        print("📍 服务器地址: http://localhost:8000")
        print("📚 API文档: http://localhost:8000/docs")
        print("📖 ReDoc文档: http://localhost:8000/redoc")
        print("💡 按 Ctrl+C 停止服务器")
        print("-" * 50)
        
        # 启动服务器
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    else:
        print("❌ 应用创建失败，无法启动服务器")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        # 运行服务器
        run_server()
    else:
        # 测试应用创建
        main()
