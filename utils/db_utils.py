#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和操作工具类
支持连接池、事务管理、SQL执行等功能

作者：RBAC权限系统
创建时间：2025-07-17
"""

import pymysql
import pymysql.cursors
from pymysql.connections import Connection
from pymysql.cursors import Cursor
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import threading
import time
from queue import Queue, Empty
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 3306,
                 user: str = 'root',
                 password: str = '',
                 database: str = 'rbac_system',
                 charset: str = 'utf8mb4',
                 **kwargs):
        """
        初始化数据库配置
        
        Args:
            host: 数据库主机地址
            port: 数据库端口
            user: 用户名
            password: 密码
            database: 数据库名
            charset: 字符集
            **kwargs: 其他连接参数
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.extra_params = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        config = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'autocommit': False,
            'cursorclass': pymysql.cursors.DictCursor
        }
        config.update(self.extra_params)
        return config


class ConnectionPool:
    """数据库连接池"""
    
    def __init__(self, config: DatabaseConfig, 
                 min_connections: int = 5,
                 max_connections: int = 20,
                 max_idle_time: int = 3600):
        """
        初始化连接池
        
        Args:
            config: 数据库配置
            min_connections: 最小连接数
            max_connections: 最大连接数
            max_idle_time: 最大空闲时间(秒)
        """
        self.config = config
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        
        self._pool = Queue(maxsize=max_connections)
        self._active_connections = 0
        self._lock = threading.Lock()
        self._closed = False
        
        # 初始化最小连接数
        self._initialize_pool()
        
        logger.info(f"连接池初始化完成，最小连接数：{min_connections}，最大连接数：{max_connections}")
    
    def _initialize_pool(self):
        """初始化连接池"""
        for _ in range(self.min_connections):
            try:
                conn = self._create_connection()
                self._pool.put((conn, time.time()))
                self._active_connections += 1
            except Exception as e:
                logger.error(f"初始化连接池失败：{str(e)}")
                raise
    
    def _create_connection(self) -> Connection:
        """创建新的数据库连接"""
        try:
            conn = pymysql.connect(**self.config.to_dict())
            logger.debug("创建新的数据库连接")
            return conn
        except Exception as e:
            logger.error(f"创建数据库连接失败：{str(e)}")
            raise
    
    def get_connection(self, timeout: int = 30) -> Connection:
        """
        从连接池获取连接
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            Connection: 数据库连接
            
        Raises:
            Exception: 获取连接失败
        """
        if self._closed:
            raise Exception("连接池已关闭")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 尝试从池中获取连接
                conn, last_used = self._pool.get_nowait()
                
                # 检查连接是否有效
                if self._is_connection_valid(conn):
                    logger.debug("从连接池获取连接")
                    return conn
                else:
                    # 连接无效，创建新连接
                    with self._lock:
                        self._active_connections -= 1
                    conn = self._create_connection()
                    with self._lock:
                        self._active_connections += 1
                    return conn
                    
            except Empty:
                # 池中没有可用连接，尝试创建新连接
                with self._lock:
                    if self._active_connections < self.max_connections:
                        conn = self._create_connection()
                        self._active_connections += 1
                        logger.debug("创建新连接")
                        return conn
                
                # 等待一段时间后重试
                time.sleep(0.1)
        
        raise Exception(f"获取数据库连接超时({timeout}秒)")
    
    def return_connection(self, conn: Connection):
        """
        将连接返回到连接池
        
        Args:
            conn: 数据库连接
        """
        if self._closed:
            conn.close()
            return
        
        try:
            if self._is_connection_valid(conn):
                # 重置连接状态
                conn.rollback()
                self._pool.put((conn, time.time()))
                logger.debug("连接返回到连接池")
            else:
                # 连接无效，关闭并减少计数
                conn.close()
                with self._lock:
                    self._active_connections -= 1
                logger.debug("无效连接已关闭")
        except Exception as e:
            logger.error(f"返回连接到池失败：{str(e)}")
            conn.close()
            with self._lock:
                self._active_connections -= 1
    
    def _is_connection_valid(self, conn: Connection) -> bool:
        """检查连接是否有效"""
        try:
            conn.ping(reconnect=False)
            return True
        except:
            return False
    
    def close(self):
        """关闭连接池"""
        self._closed = True
        
        while not self._pool.empty():
            try:
                conn, _ = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        
        logger.info("连接池已关闭")
    
    def get_stats(self) -> Dict[str, int]:
        """获取连接池统计信息"""
        return {
            'active_connections': self._active_connections,
            'pool_size': self._pool.qsize(),
            'max_connections': self.max_connections,
            'min_connections': self.min_connections
        }


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: DatabaseConfig, 
                 min_connections: int = 5,
                 max_connections: int = 20):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置
            min_connections: 最小连接数
            max_connections: 最大连接数
        """
        self.config = config
        self.pool = ConnectionPool(config, min_connections, max_connections)
        logger.info("数据库管理器初始化完成")
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = self.pool.get_connection()
            yield conn
        finally:
            if conn:
                self.pool.return_connection(conn)
    
    @contextmanager
    def get_cursor(self, connection: Optional[Connection] = None):
        """获取游标的上下文管理器"""
        if connection:
            cursor = connection.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
        else:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    yield cursor
                finally:
                    cursor.close()
    
    def execute_query(self, sql: str, params: Optional[Union[Tuple, Dict]] = None) -> List[Dict[str, Any]]:
        """
        执行查询SQL
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            List[Dict]: 查询结果
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    cursor.execute(sql, params)
                    result = cursor.fetchall()
                    logger.debug(f"查询执行成功，返回{len(result)}条记录")
                    return result
        except Exception as e:
            logger.error(f"查询执行失败：{str(e)}")
            raise
    
    def execute_update(self, sql: str, params: Optional[Union[Tuple, Dict]] = None) -> int:
        """
        执行更新SQL（INSERT、UPDATE、DELETE）
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            int: 影响的行数
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    affected_rows = cursor.execute(sql, params)
                    conn.commit()
                    logger.debug(f"更新执行成功，影响{affected_rows}行")
                    return affected_rows
        except Exception as e:
            logger.error(f"更新执行失败：{str(e)}")
            raise
    
    def execute_batch(self, sql: str, params_list: List[Union[Tuple, Dict]]) -> int:
        """
        批量执行SQL
        
        Args:
            sql: SQL语句
            params_list: 参数列表
            
        Returns:
            int: 影响的总行数
        """
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    affected_rows = cursor.executemany(sql, params_list)
                    conn.commit()
                    logger.debug(f"批量执行成功，影响{affected_rows}行")
                    return affected_rows
        except Exception as e:
            logger.error(f"批量执行失败：{str(e)}")
            raise
    
    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = None
        try:
            conn = self.pool.get_connection()
            conn.begin()
            yield conn
            conn.commit()
            logger.debug("事务提交成功")
        except Exception as e:
            if conn:
                conn.rollback()
                logger.error(f"事务回滚：{str(e)}")
            raise
        finally:
            if conn:
                self.pool.return_connection(conn)
    
    def close(self):
        """关闭数据库管理器"""
        self.pool.close()
        logger.info("数据库管理器已关闭")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库管理器统计信息"""
        return {
            'pool_stats': self.pool.get_stats(),
            'config': {
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database
            }
        }


# 创建默认数据库管理器实例（延迟初始化）
default_config = DatabaseConfig()
db_manager = None

def get_default_manager():
    """获取默认数据库管理器，延迟初始化"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(default_config)
    return db_manager


# 便捷函数
def execute_query(sql: str, params: Optional[Union[Tuple, Dict]] = None) -> List[Dict[str, Any]]:
    """便捷函数：执行查询"""
    return get_default_manager().execute_query(sql, params)

def execute_update(sql: str, params: Optional[Union[Tuple, Dict]] = None) -> int:
    """便捷函数：执行更新"""
    return get_default_manager().execute_update(sql, params)

def execute_batch(sql: str, params_list: List[Union[Tuple, Dict]]) -> int:
    """便捷函数：批量执行"""
    return get_default_manager().execute_batch(sql, params_list)


if __name__ == "__main__":
    # 测试代码
    print("=== 数据库工具类测试 ===")
    
    try:
        # 测试连接
        config = DatabaseConfig(
            host='localhost',
            user='root',
            password='',
            database='rbac_system'
        )
        
        manager = DatabaseManager(config, min_connections=2, max_connections=5)
        
        # 测试查询
        result = manager.execute_query("SELECT 1 as test")
        print(f"测试查询结果: {result}")
        
        # 获取统计信息
        stats = manager.get_stats()
        print(f"连接池统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        # 关闭管理器
        manager.close()
        
        print("=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        print("请确保MySQL服务已启动并配置正确的连接参数")
