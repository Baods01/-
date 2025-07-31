"""
RBAC权限系统 - 业务异常模块

本模块定义了业务逻辑层使用的自定义异常类，
用于处理各种业务场景下的异常情况。

异常类层次结构：
- BusinessLogicError: 业务逻辑异常基类
- AuthenticationError: 认证异常
- AuthorizationError: 授权异常
- DataValidationError: 数据验证异常
- ResourceNotFoundError: 资源不存在异常
- DuplicateResourceError: 资源重复异常

作者: RBAC System Development Team
创建时间: 2025-07-21
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "RBAC System Development Team"


class BusinessLogicError(Exception):
    """业务逻辑异常基类"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "BUSINESS_ERROR"
        self.details = details or {}


class AuthenticationError(BusinessLogicError):
    """认证异常 - 用户身份验证失败"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class AuthorizationError(BusinessLogicError):
    """授权异常 - 用户权限不足"""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(message, error_code="PERMISSION_ERROR", **kwargs)


class DataValidationError(BusinessLogicError):
    """数据验证异常 - 输入数据不符合要求"""

    def __init__(self, message: str = "Data validation failed", **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class ResourceNotFoundError(BusinessLogicError):
    """资源不存在异常"""
    
    def __init__(self, resource_type: str, resource_id: str = None, **kwargs):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND", **kwargs)


class DuplicateResourceError(BusinessLogicError):
    """资源重复异常"""

    def __init__(self, resource_type: str, field_name: str, field_value: str, message: str = None, **kwargs):
        if message is None:
            message = f"{resource_type} with {field_name} '{field_value}' already exists"
        super().__init__(message, error_code="DUPLICATE_RESOURCE", **kwargs)


class DatabaseConnectionError(BusinessLogicError):
    """数据库连接错误"""
    def __init__(self, message: str = "数据库连接失败"):
        super().__init__(message, "DATABASE_CONNECTION_ERROR")


def sanitize_error_message(error: Exception) -> str:
    """清理错误信息，避免敏感信息泄露"""
    error_str = str(error)

    # 移除SQL查询详情
    if "SQL:" in error_str:
        parts = error_str.split("SQL:")
        return parts[0].strip()

    # 移除数据库连接字符串
    if "sqlite:///" in error_str:
        return "数据库操作失败"

    # 移除文件路径信息
    if "\\cursor_task\\sql_database\\" in error_str:
        return "系统内部错误"

    # 对于包含敏感信息的错误，返回通用消息
    sensitive_keywords = ["password", "token", "secret", "key", "hash"]
    if any(keyword in error_str.lower() for keyword in sensitive_keywords):
        return "操作失败，请联系管理员"

    return error_str


# 导出所有异常类
__all__ = [
    "BusinessLogicError",
    "AuthenticationError",
    "AuthorizationError",
    "DataValidationError",
    "ResourceNotFoundError",
    "DuplicateResourceError",
    "DatabaseConnectionError",
    "sanitize_error_message"
]
