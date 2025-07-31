-- =====================================================
-- RBAC权限系统安全功能表设计
-- 包含操作日志表和用户会话表
-- 数据库：MySQL 8.0+
-- 字符集：utf8mb4
-- 创建时间：2025-07-17
-- =====================================================

-- 设置数据库字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

USE rbac_system;

-- =====================================================
-- 6. 操作日志表 (audit_logs)
-- 记录用户的所有敏感操作
-- =====================================================
DROP TABLE IF EXISTS audit_logs;
CREATE TABLE audit_logs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    user_id INT UNSIGNED COMMENT '用户ID',
    action_type VARCHAR(32) NOT NULL COMMENT '操作类型',
    resource_type VARCHAR(32) NOT NULL COMMENT '操作对象类型',
    resource_id VARCHAR(64) COMMENT '操作对象ID',
    action_result TINYINT UNSIGNED NOT NULL COMMENT '操作结果：1=成功，0=失败',
    ip_address VARCHAR(45) NOT NULL COMMENT 'IP地址(支持IPv6)',
    user_agent TEXT COMMENT '用户代理信息',
    request_data JSON COMMENT '请求数据(JSON格式)',
    response_data JSON COMMENT '响应数据(JSON格式)',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    
    PRIMARY KEY (id),
    KEY idx_user_id (user_id),
    KEY idx_action_type (action_type),
    KEY idx_resource_type (resource_type),
    KEY idx_action_result (action_result),
    KEY idx_ip_address (ip_address),
    KEY idx_created_at (created_at),
    KEY idx_user_action_time (user_id, action_type, created_at),
    
    CONSTRAINT fk_audit_logs_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- =====================================================
-- 7. 用户会话表 (user_sessions)
-- 管理用户登录会话
-- =====================================================
DROP TABLE IF EXISTS user_sessions;
CREATE TABLE user_sessions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '会话ID',
    user_id INT UNSIGNED NOT NULL COMMENT '用户ID',
    session_token VARCHAR(128) NOT NULL COMMENT '会话令牌',
    refresh_token VARCHAR(128) COMMENT '刷新令牌',
    ip_address VARCHAR(45) NOT NULL COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理信息',
    is_active TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '是否活跃：1=活跃，0=已失效',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活动时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_session_token (session_token),
    UNIQUE KEY uk_refresh_token (refresh_token),
    KEY idx_user_id (user_id),
    KEY idx_is_active (is_active),
    KEY idx_expires_at (expires_at),
    KEY idx_user_active (user_id, is_active, expires_at),
    KEY idx_last_activity (last_activity_at),
    
    CONSTRAINT fk_user_sessions_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会话表';

-- =====================================================
-- 8. 密码重置表 (password_resets)
-- 管理密码重置请求
-- =====================================================
DROP TABLE IF EXISTS password_resets;
CREATE TABLE password_resets (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '重置ID',
    user_id INT UNSIGNED NOT NULL COMMENT '用户ID',
    reset_token VARCHAR(128) NOT NULL COMMENT '重置令牌',
    ip_address VARCHAR(45) NOT NULL COMMENT 'IP地址',
    is_used TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '是否已使用：1=已使用，0=未使用',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    used_at TIMESTAMP NULL COMMENT '使用时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_reset_token (reset_token),
    KEY idx_user_id (user_id),
    KEY idx_is_used (is_used),
    KEY idx_expires_at (expires_at),
    KEY idx_user_used (user_id, is_used, expires_at),
    
    CONSTRAINT fk_password_resets_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='密码重置表';

-- =====================================================
-- 9. 登录失败记录表 (login_failures)
-- 记录登录失败次数，用于账户锁定
-- =====================================================
DROP TABLE IF EXISTS login_failures;
CREATE TABLE login_failures (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    username VARCHAR(32) NOT NULL COMMENT '用户名',
    ip_address VARCHAR(45) NOT NULL COMMENT 'IP地址',
    failure_reason VARCHAR(64) NOT NULL COMMENT '失败原因',
    user_agent TEXT COMMENT '用户代理信息',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '失败时间',
    
    PRIMARY KEY (id),
    KEY idx_username (username),
    KEY idx_ip_address (ip_address),
    KEY idx_created_at (created_at),
    KEY idx_username_ip_time (username, ip_address, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录失败记录表';

-- =====================================================
-- 创建视图：用户权限视图
-- 方便查询用户的所有权限
-- =====================================================
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    r.id as role_id,
    r.role_name,
    r.role_code,
    p.id as permission_id,
    p.permission_name,
    p.permission_code,
    p.resource_type,
    p.action_type,
    ur.status as user_role_status,
    rp.status as role_permission_status
FROM users u
JOIN user_roles ur ON u.id = ur.user_id AND ur.status = 1
JOIN roles r ON ur.role_id = r.id AND r.status = 1
JOIN role_permissions rp ON r.id = rp.role_id AND rp.status = 1
JOIN permissions p ON rp.permission_id = p.id
WHERE u.status = 1;

-- =====================================================
-- 创建存储过程：清理过期会话
-- =====================================================
DELIMITER //
CREATE PROCEDURE CleanExpiredSessions()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 标记过期会话为非活跃状态
    UPDATE user_sessions 
    SET is_active = 0 
    WHERE expires_at < NOW() AND is_active = 1;
    
    -- 删除超过30天的非活跃会话记录
    DELETE FROM user_sessions 
    WHERE is_active = 0 AND expires_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    COMMIT;
END //
DELIMITER ;

-- =====================================================
-- 创建存储过程：清理过期的密码重置记录
-- =====================================================
DELIMITER //
CREATE PROCEDURE CleanExpiredPasswordResets()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 删除过期的密码重置记录
    DELETE FROM password_resets 
    WHERE expires_at < NOW();
    
    COMMIT;
END //
DELIMITER ;

-- =====================================================
-- 创建事件调度器：自动清理过期数据
-- =====================================================
SET GLOBAL event_scheduler = ON;

-- 每小时清理过期会话
CREATE EVENT IF NOT EXISTS evt_clean_expired_sessions
ON SCHEDULE EVERY 1 HOUR
DO
  CALL CleanExpiredSessions();

-- 每天清理过期的密码重置记录
CREATE EVENT IF NOT EXISTS evt_clean_expired_password_resets
ON SCHEDULE EVERY 1 DAY
DO
  CALL CleanExpiredPasswordResets();

-- 设置外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 安全功能表设计完成
-- =====================================================
