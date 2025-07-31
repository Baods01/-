# RBAC系统ORM代码生成规范

## 📋 规范概述

**制定目标**：为RBAC系统ORM层代码生成建立统一的编码规范和质量标准  
**适用范围**：Model类、DAO接口、测试类的代码生成  
**遵循标准**：PEP 8、PEP 257、Python类型注解规范  
**制定时间**：2025-07-19

## 🏷️ 命名约定规范

### 1. 类命名规范

| 类型 | 命名规则 | 示例 | 说明 |
|------|----------|------|------|
| Model类 | PascalCase | User, Role, Permission | 实体模型类 |
| DAO接口类 | PascalCase + Dao后缀 | UserDao, RoleDao | 数据访问对象 |
| DAO实现类 | PascalCase + DaoImpl后缀 | UserDaoImpl, RoleDaoImpl | DAO接口实现 |
| 测试类 | Test前缀 + PascalCase | TestUserDao, TestRoleDao | 单元测试类 |
| 异常类 | PascalCase + Exception后缀 | UserNotFoundException | 自定义异常类 |

### 2. 方法命名规范

| 方法类型 | 命名规则 | 示例 | 说明 |
|----------|----------|------|------|
| CRUD方法 | snake_case | create, find_by_id, update, delete_by_id | 基础增删改查 |
| 查询方法 | find_by_xxx | find_by_username, find_by_email | 条件查询 |
| 业务方法 | 动词_名词 | activate_user, assign_role | 业务操作 |
| 验证方法 | validate_xxx | validate_email, validate_username | 数据验证 |
| 转换方法 | to_xxx, from_xxx | to_dict, from_dict | 数据转换 |
| 检查方法 | is_xxx, has_xxx | is_active, has_permission | 状态检查 |

### 3. 变量命名规范

| 变量类型 | 命名规则 | 示例 | 说明 |
|----------|----------|------|------|
| 实例变量 | snake_case | user_id, role_name | 对象属性 |
| 类变量 | snake_case | table_name | 类级别变量 |
| 常量 | UPPER_SNAKE_CASE | DEFAULT_STATUS, MAX_USERNAME_LENGTH | 常量定义 |
| 私有变量 | _snake_case | _session, _logger | 私有属性 |
| 临时变量 | snake_case | temp_user, result_list | 临时变量 |

### 4. 文件命名规范

| 文件类型 | 命名规则 | 示例 | 说明 |
|----------|----------|------|------|
| Model文件 | snake_case.py | user.py, role.py | 模型类文件 |
| DAO文件 | snake_case_dao.py | user_dao.py, role_dao.py | DAO接口文件 |
| 测试文件 | test_snake_case.py | test_user_dao.py | 测试文件 |
| 配置文件 | snake_case_config.py | orm_config.py | 配置文件 |
| 工具文件 | snake_case_utils.py | db_utils.py | 工具类文件 |

## 📁 文件结构规范

### 1. 项目目录结构
```
sql_database/
├── models/                    # 模型层
│   ├── __init__.py           # 模块初始化
│   ├── base_model.py         # 基础模型类
│   ├── user.py               # 用户模型
│   ├── role.py               # 角色模型
│   ├── permission.py         # 权限模型
│   ├── user_role.py          # 用户角色关联模型
│   └── role_permission.py    # 角色权限关联模型
├── dao/                      # 数据访问层
│   ├── __init__.py           # 模块初始化
│   ├── base_dao.py           # 基础DAO类
│   ├── user_dao.py           # 用户DAO接口
│   ├── role_dao.py           # 角色DAO接口
│   ├── permission_dao.py     # 权限DAO接口
│   ├── user_role_dao.py      # 用户角色DAO接口
│   └── role_permission_dao.py # 角色权限DAO接口
├── tests/                    # 测试层
│   ├── __init__.py           # 模块初始化
│   ├── conftest.py           # pytest配置
│   ├── test_user_dao.py      # 用户DAO测试
│   ├── test_role_dao.py      # 角色DAO测试
│   ├── test_permission_dao.py # 权限DAO测试
│   ├── test_user_role_dao.py # 用户角色DAO测试
│   └── test_role_permission_dao.py # 角色权限DAO测试
└── config/                   # 配置层
    ├── __init__.py           # 模块初始化
    └── orm_config.py         # ORM配置
```

### 2. 文件内容结构规范

#### Model类文件结构
```python
"""
模块文档字符串
描述模块的用途和主要功能
"""

# 1. 标准库导入
from datetime import datetime
from typing import Optional, List

# 2. 第三方库导入
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# 3. 本地模块导入
from .base_model import BaseModel

# 4. 常量定义
MAX_USERNAME_LENGTH = 32
DEFAULT_STATUS = 1

# 5. 类定义
class User(BaseModel):
    """用户模型类文档字符串"""
    
    # 5.1 表配置
    __tablename__ = 'users'
    
    # 5.2 字段定义
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    username: str = Column(String(32), nullable=False, unique=True)
    
    # 5.3 关系定义
    user_roles = relationship("UserRole", back_populates="user")
    
    # 5.4 类方法
    def __init__(self, **kwargs):
        """构造方法"""
        super().__init__(**kwargs)
    
    # 5.5 实例方法
    def to_dict(self) -> dict:
        """转换为字典"""
        pass
    
    # 5.6 特殊方法
    def __str__(self) -> str:
        """字符串表示"""
        return f"User(id={self.id}, username='{self.username}')"
    
    def __repr__(self) -> str:
        """开发者表示"""
        return self.__str__()
```

## 📝 注释和文档规范

### 1. 文档字符串规范（遵循PEP 257）

#### 模块文档字符串
```python
"""
RBAC系统用户模型模块

本模块定义了用户实体的ORM模型类，包含用户的基本信息字段、
关系映射、业务方法等。

Classes:
    User: 用户模型类

Author: AI Assistant
Created: 2025-07-19
"""
```

#### 类文档字符串
```python
class User(BaseModel):
    """
    用户模型类
    
    用于表示系统中的用户实体，包含用户的基本信息如用户名、邮箱、
    密码哈希等，以及与角色的关联关系。
    
    Attributes:
        id (int): 用户唯一标识
        username (str): 用户名，用于登录
        email (str): 邮箱地址，用于登录和通知
        password_hash (str): 密码哈希值
        status (int): 用户状态，1=启用，0=禁用
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
        
    Relationships:
        user_roles: 用户的角色关联列表
        roles: 用户拥有的角色列表
    
    Example:
        >>> user = User(username="admin", email="admin@example.com")
        >>> user.is_active()
        True
    """
```

#### 方法文档字符串
```python
def find_by_username(self, username: str) -> Optional['User']:
    """
    根据用户名查找用户
    
    Args:
        username (str): 要查找的用户名
        
    Returns:
        Optional[User]: 找到的用户对象，如果不存在则返回None
        
    Raises:
        ValueError: 当用户名为空或格式不正确时
        DatabaseError: 当数据库操作失败时
        
    Example:
        >>> dao = UserDao()
        >>> user = dao.find_by_username("admin")
        >>> print(user.email if user else "用户不存在")
    """
```

### 2. 行内注释规范

```python
class User(BaseModel):
    # 基础字段定义
    id: int = Column(Integer, primary_key=True, autoincrement=True)  # 主键，自增
    username: str = Column(String(32), nullable=False, unique=True)  # 用户名，唯一
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        # 使用正则表达式验证邮箱格式
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
```

## 🔧 类型注解规范

### 1. 基础类型注解
```python
from typing import Optional, List, Dict, Union, Any
from datetime import datetime

class User(BaseModel):
    # 字段类型注解
    id: int
    username: str
    email: str
    status: int
    created_at: datetime
    updated_at: datetime
    
    # 方法参数和返回值注解
    def find_by_id(self, user_id: int) -> Optional['User']:
        """根据ID查找用户"""
        pass
    
    def find_all(self) -> List['User']:
        """查找所有用户"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        pass
```

### 2. 复杂类型注解
```python
from typing import TypeVar, Generic, Protocol

# 泛型类型变量
T = TypeVar('T', bound=BaseModel)

class BaseDao(Generic[T]):
    """基础DAO泛型类"""
    
    def create(self, entity: T) -> T:
        """创建实体"""
        pass
    
    def find_by_id(self, entity_id: int) -> Optional[T]:
        """根据ID查找实体"""
        pass
```

## ✅ 代码质量标准

### 1. PEP 8 规范要求
- **行长度**：每行不超过88字符（Black格式化工具标准）
- **缩进**：使用4个空格，不使用Tab
- **空行**：类定义前后2个空行，方法定义前后1个空行
- **导入**：按标准库、第三方库、本地模块的顺序分组导入
- **命名**：严格遵循命名约定规范

### 2. 代码复杂度要求
- **圈复杂度**：单个方法的圈复杂度不超过10
- **方法长度**：单个方法不超过50行
- **类长度**：单个类不超过500行
- **参数数量**：方法参数不超过5个

### 3. 测试覆盖率要求
- **整体覆盖率**：≥90%
- **分支覆盖率**：≥85%
- **方法覆盖率**：100%（所有公共方法都要有测试）

### 4. 错误处理标准
```python
class UserDao:
    def find_by_id(self, user_id: int) -> Optional[User]:
        """根据ID查找用户"""
        try:
            # 参数验证
            if user_id <= 0:
                raise ValueError("用户ID必须大于0")
            
            # 数据库操作
            user = self.session.query(User).filter(User.id == user_id).first()
            return user
            
        except SQLAlchemyError as e:
            # 记录错误日志
            self.logger.error(f"查询用户失败: user_id={user_id}, error={str(e)}")
            # 抛出业务异常
            raise DatabaseError(f"查询用户失败: {str(e)}") from e
        except Exception as e:
            # 记录未知错误
            self.logger.error(f"未知错误: {str(e)}")
            raise
```

## 🧪 测试代码规范

### 1. 测试类结构
```python
class TestUserDao:
    """用户DAO测试类"""
    
    @pytest.fixture
    def user_dao(self):
        """创建UserDao实例"""
        return UserDao()
    
    @pytest.fixture
    def sample_user(self):
        """创建示例用户"""
        return User(username="test", email="test@example.com")
    
    def test_create_user_success(self, user_dao, sample_user):
        """测试创建用户成功"""
        # Given - 准备测试数据
        
        # When - 执行测试操作
        
        # Then - 验证测试结果
        pass
```

### 2. 测试方法命名
- **成功场景**：test_方法名_success
- **失败场景**：test_方法名_failure
- **异常场景**：test_方法名_异常类型
- **边界场景**：test_方法名_boundary

### 3. 断言规范
```python
def test_find_by_id_success(self, user_dao):
    """测试根据ID查找用户成功"""
    # 使用具体的断言方法
    assert result is not None
    assert result.id == 1
    assert result.username == "test"
    
    # 使用pytest的断言消息
    assert result.status == 1, f"期望状态为1，实际为{result.status}"
```

## 📊 代码生成模板

### 1. Model类模板
```python
"""
{module_name}模型模块

{module_description}
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from .base_model import BaseModel


class {class_name}(BaseModel):
    """
    {class_description}
    
    Attributes:
        {attributes_doc}
    """
    
    __tablename__ = '{table_name}'
    
    # 字段定义
    {field_definitions}
    
    # 关系定义
    {relationship_definitions}
    
    def __init__(self, **kwargs):
        """构造方法"""
        super().__init__(**kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        {to_dict_implementation}
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{class_name}(id={self.id})"
    
    def __repr__(self) -> str:
        """开发者表示"""
        return self.__str__()
```

---

**编码规范制定完成时间**：2025-07-19  
**下一步**：开始Model类代码生成
