# RBAC权限系统安全功能设计文档

## 概述
本文档详细描述了RBAC权限系统的安全功能设计，包括密码安全、会话管理、操作审计、登录防护等核心安全机制。

## 设计原则
- **纵深防御**：多层安全防护机制
- **最小权限**：用户只获得必要的最小权限
- **安全默认**：默认配置采用最安全的选项
- **审计追踪**：所有操作都有完整的审计记录
- **数据保护**：敏感数据加密存储和传输

## 安全功能架构

### 1. 密码安全系统

#### 1.1 密码加密存储
**技术选择**：bcrypt算法
- **算法强度**：12轮salt（可配置10-15轮）
- **存储格式**：`$2b$12$salt+hash`（60字符）
- **禁用算法**：MD5、SHA1、SHA256等快速哈希算法

**实现特性**：
```python
# 密码加密
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

# 密码验证
is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
```

#### 1.2 密码强度要求
**基本要求**：
- 最小长度：8字符
- 最大长度：128字符
- 必须包含：大写字母、小写字母、数字、特殊字符

**弱密码检测**：
- 常见密码：123456、password、admin、qwerty
- 连续字符：避免4个或更多相同字符
- 字典攻击：检测常见单词组合

#### 1.3 随机密码生成
**生成策略**：
- 使用`secrets`模块确保密码学安全
- 字符集包含：大小写字母、数字、特殊符号
- 确保各类字符均匀分布
- 随机打乱字符顺序

### 2. 会话管理系统

#### 2.1 会话表设计
```sql
CREATE TABLE user_sessions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    session_token VARCHAR(128) NOT NULL,      -- 会话令牌
    refresh_token VARCHAR(128),               -- 刷新令牌
    ip_address VARCHAR(45) NOT NULL,          -- 支持IPv6
    user_agent TEXT,                          -- 浏览器信息
    is_active TINYINT UNSIGNED NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,            -- 过期时间
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### 2.2 会话安全特性
**令牌生成**：
- 使用密码学安全的随机数生成器
- 令牌长度：128字符（Base64编码）
- 每次登录生成新的唯一令牌

**过期控制**：
- 默认会话时长：24小时
- 支持"记住我"功能（30天）
- 空闲超时：2小时无活动自动过期
- 绝对超时：最长7天强制重新登录

**多设备管理**：
- 支持同一用户多设备登录
- 可配置最大并发会话数
- 支持远程注销其他设备

#### 2.3 自动清理机制
**存储过程**：
```sql
-- 每小时执行：清理过期会话
CREATE PROCEDURE CleanExpiredSessions()
BEGIN
    UPDATE user_sessions SET is_active = 0 WHERE expires_at < NOW();
    DELETE FROM user_sessions WHERE is_active = 0 AND expires_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
END
```

### 3. 操作审计系统

#### 3.1 审计日志表设计
```sql
CREATE TABLE audit_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED,                     -- 操作用户
    action_type VARCHAR(32) NOT NULL,         -- 操作类型
    resource_type VARCHAR(32) NOT NULL,       -- 资源类型
    resource_id VARCHAR(64),                  -- 资源ID
    action_result TINYINT UNSIGNED NOT NULL,  -- 操作结果
    ip_address VARCHAR(45) NOT NULL,          -- IP地址
    user_agent TEXT,                          -- 用户代理
    request_data JSON,                        -- 请求数据
    response_data JSON,                       -- 响应数据
    error_message TEXT,                       -- 错误信息
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.2 审计范围
**记录的操作类型**：
- 用户管理：创建、修改、删除、启用、禁用
- 角色管理：分配、撤销、修改权限
- 权限管理：授权、撤销、修改
- 系统操作：登录、注销、密码修改
- 敏感查询：权限检查、用户信息查询

**审计数据格式**：
```json
{
  "action_type": "user:create",
  "resource_type": "user",
  "resource_id": "12345",
  "request_data": {
    "username": "newuser",
    "email": "user@example.com",
    "roles": ["user"]
  },
  "response_data": {
    "user_id": 12345,
    "status": "success"
  }
}
```

#### 3.3 审计查询优化
**索引设计**：
```sql
KEY idx_user_action_time (user_id, action_type, created_at),
KEY idx_resource_type (resource_type),
KEY idx_action_result (action_result),
KEY idx_ip_address (ip_address)
```

### 4. 登录安全防护

#### 4.1 登录失败记录
```sql
CREATE TABLE login_failures (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(32) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    failure_reason VARCHAR(64) NOT NULL,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.2 防护策略
**账户锁定**：
- 5次失败后锁定账户15分钟
- 10次失败后锁定账户1小时
- 20次失败后锁定账户24小时

**IP限制**：
- 同一IP 10次失败后限制1小时
- 支持IP白名单和黑名单
- 地理位置异常检测

**验证码机制**：
- 3次失败后要求验证码
- 支持图形验证码和短信验证码
- 验证码有效期5分钟

### 5. 密码重置安全

#### 5.1 重置流程设计
```sql
CREATE TABLE password_resets (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id INT UNSIGNED NOT NULL,
    reset_token VARCHAR(128) NOT NULL,        -- 重置令牌
    ip_address VARCHAR(45) NOT NULL,
    is_used TINYINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,            -- 15分钟过期
    used_at TIMESTAMP NULL
);
```

#### 5.2 安全特性
**令牌安全**：
- 一次性使用令牌
- 15分钟有效期
- 使用后立即失效
- 密码学安全的随机生成

**验证机制**：
- 邮箱验证：发送重置链接到注册邮箱
- 短信验证：发送验证码到绑定手机
- 安全问题：预设安全问题验证

**操作限制**：
- 同一用户1小时内最多3次重置请求
- 同一IP 1小时内最多10次重置请求
- 重置成功后强制注销所有会话

### 6. 权限验证安全

#### 6.1 权限检查流程
```python
def check_permission(user_id: int, permission_code: str) -> bool:
    """检查用户权限"""
    # 1. 检查用户状态
    if not is_user_active(user_id):
        return False
    
    # 2. 获取用户角色
    user_roles = get_user_roles(user_id)
    if not user_roles:
        return False
    
    # 3. 检查角色权限
    for role in user_roles:
        if has_role_permission(role.id, permission_code):
            return True
    
    return False
```

#### 6.2 缓存策略
**权限缓存**：
- Redis缓存用户权限列表
- 缓存时间：30分钟
- 权限变更时立即清除缓存

**会话缓存**：
- 内存缓存活跃会话信息
- 减少数据库查询压力
- 支持分布式缓存

### 7. 数据传输安全

#### 7.1 HTTPS强制
- 所有API接口强制HTTPS
- HTTP自动重定向到HTTPS
- HSTS头部设置

#### 7.2 API安全
**请求签名**：
- HMAC-SHA256签名验证
- 时间戳防重放攻击
- Nonce防重复请求

**速率限制**：
- 用户级别：100请求/分钟
- IP级别：1000请求/分钟
- API级别：不同接口不同限制

### 8. 安全配置建议

#### 8.1 生产环境配置
```python
SECURITY_CONFIG = {
    'password': {
        'bcrypt_rounds': 12,
        'min_length': 8,
        'max_length': 128,
        'require_complexity': True
    },
    'session': {
        'timeout': 24 * 3600,  # 24小时
        'idle_timeout': 2 * 3600,  # 2小时
        'max_sessions_per_user': 5
    },
    'login': {
        'max_failures': 5,
        'lockout_duration': 15 * 60,  # 15分钟
        'require_captcha_after': 3
    },
    'audit': {
        'log_all_operations': True,
        'retention_days': 90,
        'sensitive_data_mask': True
    }
}
```

#### 8.2 监控告警
**安全事件监控**：
- 异常登录检测
- 权限提升监控
- 批量操作告警
- 系统异常监控

**告警阈值**：
- 5分钟内超过10次登录失败
- 单用户1小时内权限检查超过1000次
- 系统错误率超过1%
- 数据库连接异常

## 安全测试建议

### 1. 渗透测试
- SQL注入测试
- XSS攻击测试
- CSRF攻击测试
- 权限绕过测试

### 2. 性能测试
- 并发登录测试
- 权限检查性能测试
- 会话管理压力测试
- 审计日志写入性能测试

### 3. 安全审计
- 代码安全审计
- 配置安全检查
- 依赖库漏洞扫描
- 数据库安全配置检查

## 合规性考虑

### 1. 数据保护法规
- GDPR合规性
- 个人信息保护
- 数据最小化原则
- 用户同意机制

### 2. 行业标准
- ISO 27001信息安全管理
- NIST网络安全框架
- OWASP安全开发指南
- SOC 2合规性

---

*本安全设计文档将随着安全威胁的变化持续更新*
