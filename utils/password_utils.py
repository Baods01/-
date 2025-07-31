#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码加密工具类
使用bcrypt进行密码加密和验证
禁用MD5/SHA1等弱加密算法

作者：RBAC权限系统
创建时间：2025-07-17
"""

import bcrypt
import secrets
import string
import re
from typing import Optional, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PasswordUtils:
    """密码加密和验证工具类"""
    
    # bcrypt加密轮数，推荐12-15轮
    DEFAULT_ROUNDS = 12
    MIN_ROUNDS = 10
    MAX_ROUNDS = 15
    
    # 密码强度要求
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    def __init__(self, rounds: int = DEFAULT_ROUNDS):
        """
        初始化密码工具类
        
        Args:
            rounds: bcrypt加密轮数，默认12轮
        """
        if not self.MIN_ROUNDS <= rounds <= self.MAX_ROUNDS:
            raise ValueError(f"加密轮数必须在{self.MIN_ROUNDS}-{self.MAX_ROUNDS}之间")
        
        self.rounds = rounds
        logger.info(f"密码工具类初始化完成，使用{rounds}轮bcrypt加密")
    
    def hash_password(self, password: str) -> str:
        """
        使用bcrypt加密密码
        
        Args:
            password: 明文密码
            
        Returns:
            str: 加密后的密码哈希值
            
        Raises:
            ValueError: 密码格式不符合要求
            Exception: 加密过程中出现错误
        """
        try:
            # 验证密码格式
            self._validate_password(password)
            
            # 将密码转换为字节
            password_bytes = password.encode('utf-8')
            
            # 生成盐值并加密
            salt = bcrypt.gensalt(rounds=self.rounds)
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # 返回字符串格式的哈希值
            hash_str = hashed.decode('utf-8')
            logger.debug(f"密码加密成功，哈希长度：{len(hash_str)}")
            
            return hash_str
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"密码加密失败：{str(e)}")
            raise Exception(f"密码加密失败：{str(e)}")
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        验证密码是否正确
        
        Args:
            password: 明文密码
            hashed_password: 存储的密码哈希值
            
        Returns:
            bool: 密码是否正确
            
        Raises:
            ValueError: 参数格式错误
            Exception: 验证过程中出现错误
        """
        try:
            if not password or not hashed_password:
                raise ValueError("密码和哈希值不能为空")
            
            # 将字符串转换为字节
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # 验证密码
            result = bcrypt.checkpw(password_bytes, hashed_bytes)
            
            logger.debug(f"密码验证结果：{'成功' if result else '失败'}")
            return result
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"密码验证失败：{str(e)}")
            raise Exception(f"密码验证失败：{str(e)}")
    
    def generate_random_password(self, length: int = 12) -> str:
        """
        生成随机密码
        
        Args:
            length: 密码长度，默认12位
            
        Returns:
            str: 随机生成的密码
            
        Raises:
            ValueError: 密码长度不符合要求
        """
        if not self.MIN_PASSWORD_LENGTH <= length <= self.MAX_PASSWORD_LENGTH:
            raise ValueError(f"密码长度必须在{self.MIN_PASSWORD_LENGTH}-{self.MAX_PASSWORD_LENGTH}之间")
        
        # 定义字符集
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # 确保密码包含各种字符类型
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special_chars)
        ]
        
        # 填充剩余长度
        all_chars = lowercase + uppercase + digits + special_chars
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # 打乱顺序
        secrets.SystemRandom().shuffle(password)
        
        result = ''.join(password)
        logger.info(f"生成随机密码，长度：{length}")
        
        return result
    
    def check_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        检查密码强度
        
        Args:
            password: 待检查的密码
            
        Returns:
            Tuple[bool, str]: (是否符合要求, 详细说明)
        """
        if not password:
            return False, "密码不能为空"
        
        # 长度检查
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"密码长度不能少于{self.MIN_PASSWORD_LENGTH}位"
        
        if len(password) > self.MAX_PASSWORD_LENGTH:
            return False, f"密码长度不能超过{self.MAX_PASSWORD_LENGTH}位"
        
        # 字符类型检查
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
        
        missing_types = []
        if not has_lower:
            missing_types.append("小写字母")
        if not has_upper:
            missing_types.append("大写字母")
        if not has_digit:
            missing_types.append("数字")
        if not has_special:
            missing_types.append("特殊字符")
        
        if missing_types:
            return False, f"密码必须包含：{', '.join(missing_types)}"
        
        # 常见弱密码检查
        weak_patterns = [
            r'^123456',
            r'^password$',
            r'^admin$',
            r'^qwerty',
            r'(.)\1{3,}',  # 连续4个或更多相同字符
        ]

        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                return False, "密码过于简单，请使用更复杂的密码"
        
        return True, "密码强度符合要求"
    
    def _validate_password(self, password: str) -> None:
        """
        验证密码格式
        
        Args:
            password: 待验证的密码
            
        Raises:
            ValueError: 密码格式不符合要求
        """
        if not password:
            raise ValueError("密码不能为空")
        
        if not isinstance(password, str):
            raise ValueError("密码必须是字符串类型")
        
        # 检查密码强度
        is_strong, message = self.check_password_strength(password)
        if not is_strong:
            raise ValueError(f"密码强度不符合要求：{message}")
    
    @staticmethod
    def is_bcrypt_hash(hash_string: str) -> bool:
        """
        检查字符串是否为有效的bcrypt哈希值
        
        Args:
            hash_string: 待检查的哈希字符串
            
        Returns:
            bool: 是否为有效的bcrypt哈希值
        """
        if not hash_string or not isinstance(hash_string, str):
            return False
        
        # bcrypt哈希值格式：$2b$rounds$salt+hash
        bcrypt_pattern = r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$'
        return bool(re.match(bcrypt_pattern, hash_string))


# 创建默认实例
default_password_utils = PasswordUtils()

# 便捷函数
def hash_password(password: str, rounds: int = PasswordUtils.DEFAULT_ROUNDS) -> str:
    """便捷函数：加密密码"""
    utils = PasswordUtils(rounds)
    return utils.hash_password(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """便捷函数：验证密码"""
    return default_password_utils.verify_password(password, hashed_password)

def generate_password(length: int = 12) -> str:
    """便捷函数：生成随机密码"""
    return default_password_utils.generate_random_password(length)

def check_password_strength(password: str) -> Tuple[bool, str]:
    """便捷函数：检查密码强度"""
    return default_password_utils.check_password_strength(password)


if __name__ == "__main__":
    # 测试代码
    print("=== 密码工具类测试 ===")
    
    # 测试密码加密和验证
    test_password = "TestPassword123!"
    print(f"原始密码: {test_password}")
    
    # 加密密码
    hashed = hash_password(test_password)
    print(f"加密后: {hashed}")
    
    # 验证密码
    is_valid = verify_password(test_password, hashed)
    print(f"验证结果: {is_valid}")
    
    # 测试错误密码
    wrong_password = "WrongPassword"
    is_valid_wrong = verify_password(wrong_password, hashed)
    print(f"错误密码验证: {is_valid_wrong}")
    
    # 生成随机密码
    random_pwd = generate_password(16)
    print(f"随机密码: {random_pwd}")
    
    # 检查密码强度
    strength_ok, strength_msg = check_password_strength(test_password)
    print(f"密码强度: {strength_ok} - {strength_msg}")
    
    print("=== 测试完成 ===")
