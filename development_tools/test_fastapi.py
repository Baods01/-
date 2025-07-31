#!/usr/bin/env python3
"""
RBAC权限系统 - FastAPI测试应用

验证FastAPI和相关依赖是否正常工作的简单测试应用。

作者: RBAC System Development Team
创建时间: 2025-07-21
版本: 1.0.0
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

# 导入配置
from config.api_config import config
from config.jwt_config import jwt_config

# 创建FastAPI应用
app = FastAPI(
    title=config.app_name,
    description=config.app_description,
    version=config.app_version,
    docs_url=config.docs_url,
    redoc_url=config.redoc_url
)


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    message: str
    details: Dict[str, Any]


@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
        "message": "RBAC权限系统API",
        "status": "running",
        "version": config.app_version
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        # 测试配置加载
        api_config_status = "OK" if config.app_name else "ERROR"
        jwt_config_status = "OK" if jwt_config.algorithm else "ERROR"
        
        # 测试基础组件导入
        try:
            from dao.user_dao import UserDao
            dao_status = "OK"
        except Exception:
            dao_status = "ERROR"
        
        try:
            from models.user import User
            model_status = "OK"
        except Exception:
            model_status = "ERROR"
        
        try:
            from utils.password_utils import PasswordUtils
            utils_status = "OK"
        except Exception:
            utils_status = "ERROR"
        
        try:
            from services.exceptions import BusinessLogicError
            exceptions_status = "OK"
        except Exception:
            exceptions_status = "ERROR"
        
        details = {
            "api_config": api_config_status,
            "jwt_config": jwt_config_status,
            "dao_layer": dao_status,
            "model_layer": model_status,
            "utils_layer": utils_status,
            "exceptions": exceptions_status,
            "environment": config.environment,
            "debug_mode": config.debug
        }
        
        # 检查是否所有组件都正常
        all_ok = all(status == "OK" for status in details.values() if isinstance(status, str))
        
        return HealthResponse(
            status="healthy" if all_ok else "degraded",
            message="所有组件正常" if all_ok else "部分组件异常",
            details=details
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"健康检查失败: {str(e)}"
        )


@app.get("/config", response_model=Dict[str, Any])
async def get_config():
    """获取配置信息（开发环境专用）"""
    if config.environment != "development":
        raise HTTPException(
            status_code=403,
            detail="配置信息仅在开发环境可访问"
        )
    
    return {
        "api_config": {
            "app_name": config.app_name,
            "version": config.app_version,
            "environment": config.environment,
            "debug": config.debug,
            "host": config.host,
            "port": config.port
        },
        "jwt_config": {
            "algorithm": jwt_config.algorithm,
            "access_token_expire_minutes": jwt_config.access_token_expire_minutes,
            "refresh_token_expire_days": jwt_config.refresh_token_expire_days,
            "issuer": jwt_config.issuer,
            "audience": jwt_config.audience
        }
    }


if __name__ == "__main__":
    print("🚀 启动RBAC权限系统测试应用...")
    print(f"📍 应用名称: {config.app_name}")
    print(f"🌍 运行环境: {config.environment}")
    print(f"🔧 调试模式: {config.debug}")
    print(f"📖 API文档: http://{config.host}:{config.port}{config.docs_url}")
    print(f"🏥 健康检查: http://{config.host}:{config.port}/health")
    
    uvicorn.run(
        "test_fastapi:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level=config.log_level.lower()
    )
