# RBAC权限系统

基于角色的访问控制（Role-Based Access Control）权限系统，包含完整的数据库设计、安全功能和测试工具。

## 项目状态

✅ **第一阶段完成** - 基础RBAC数据库设计
✅ **第二阶段完成** - 数据库优化与安全增强
✅ **第三阶段完成** - 测试数据生成与性能测试

🎉 **项目已完成** - 所有功能模块开发完毕，系统可投入使用

## 项目结构

```
sql_database/
├── sql/                          # SQL脚本
│   ├── 01_basic_rbac_schema.sql     # 基础RBAC建表语句
│   ├── 02_optimized_schema.sql      # 优化后的数据库结构
│   └── 03_security_features.sql     # 安全功能表结构
├── utils/                        # Python工具包
│   ├── __init__.py                  # 包初始化
│   ├── password_utils.py            # 密码加密工具
│   └── db_utils.py                  # 数据库连接工具
├── docs/                         # 项目文档
│   ├── 01_database_design.md        # 数据库设计文档
│   ├── 02_optimization_report.md    # 优化报告
│   └── 03_security_design.md        # 安全设计文档
├── scripts/                      # 脚本目录
│   ├── data_generator.py            # 测试数据生成器
│   ├── performance_test.py           # 性能测试脚本
│   └── report_generator.py           # 测试报告生成器
├── config/                       # 配置文件目录
│   └── test_config.py                # 测试配置文件
├── tests/                        # 测试目录
├── reports/                      # 报告输出目录
├── logs/                         # 日志目录
├── requirements.txt              # Python依赖
├── main.py                       # 主执行入口
├── .gitignore                    # Git忽略文件
├── verify_project.py             # 项目结构验证脚本
├── RBAC权限系统设计框架.md        # 项目框架文档
└── README.md                     # 项目说明文档
```

## 核心功能

### 🗄️ 数据库设计
- **5张核心表**：用户、角色、权限、用户角色关联、角色权限关联
- **4张安全表**：操作日志、用户会话、密码重置、登录失败记录
- **优化特性**：复合索引、存储空间优化、查询性能提升

### 🛡️ 安全功能
- **密码安全**：bcrypt加密（12轮salt）、密码强度验证
- **会话管理**：令牌机制、自动过期、多设备支持
- **操作审计**：完整日志记录、JSON数据存储
- **登录防护**：失败记录、账户锁定、IP限制

### 🔧 Python工具
- **密码工具**：加密、验证、强度检查、随机生成
- **数据库工具**：连接池、事务管理、批量操作

### 🧪 测试系统
- **数据生成器**：生成10万用户、1000角色、5000权限的测试数据
- **性能测试**：登录认证、权限查询、数据操作、压力测试
- **报告生成**：HTML和JSON格式的详细测试报告

## 快速开始

### 1. 环境准备
```bash
# 安装Python依赖
pip install -r requirements.txt

# 确保MySQL 8.0+已安装并运行
```

### 2. 数据库初始化
```bash
# 执行SQL脚本（按顺序）
mysql -u root -p < sql/01_basic_rbac_schema.sql
mysql -u root -p < sql/02_optimized_schema.sql  
mysql -u root -p < sql/03_security_features.sql
```

### 3. 验证项目结构
```bash
python verify_project.py
```

### 4. 使用Python工具
```python
from utils import hash_password, verify_password, DatabaseManager

# 密码加密
hashed = hash_password("MyPassword123!")
is_valid = verify_password("MyPassword123!", hashed)

# 数据库操作
from utils import DatabaseConfig
config = DatabaseConfig(host='localhost', database='rbac_system')
manager = DatabaseManager(config)
```

### 5. 运行测试系统
```bash
# 查看帮助
python main.py --help

# 运行快速测试（小数据量）
python main.py --scenario quick_test

# 运行标准测试（中等数据量）
python main.py --scenario standard_test

# 运行完整测试（大数据量）
python main.py --scenario full_test

# 只生成测试数据
python main.py --data-only --cleanup

# 只运行性能测试
python main.py --test-only

# 只生成报告
python main.py --report-only --test-results results.json
```

## 技术规范

### 数据库
- **MySQL**: 8.0+
- **字符集**: utf8mb4_unicode_ci
- **存储引擎**: InnoDB
- **连接池**: 5-20个连接

### Python
- **版本**: 3.8+
- **加密**: bcrypt (12轮salt)
- **数据库**: PyMySQL
- **依赖管理**: requirements.txt

### 安全标准
- **密码**: 8-128字符，包含大小写字母、数字、特殊字符
- **会话**: 24小时过期，支持刷新令牌
- **审计**: 所有敏感操作记录
- **防护**: 登录失败锁定、IP限制

## 性能指标

### 存储优化
- 用户表空间节省：22%
- 角色表空间节省：25%
- 权限表空间节省：25%
- 关联表空间节省：40%

### 查询性能
- 用户权限查询：提升30%
- 角色验证查询：提升25%
- 批量权限检查：提升35%

### 索引优化
- 索引数量：减少40%
- 维护开销：降低35%
- 内存占用：减少30%

## 测试场景

### 快速测试 (quick_test)
- 用户：1,000个
- 角色：50个
- 权限：200个
- 操作日志：10,000条
- 适用：功能验证、开发测试

### 标准测试 (standard_test)
- 用户：50,000个
- 角色：500个
- 权限：2,500个
- 操作日志：500,000条
- 适用：性能评估、集成测试

### 完整测试 (full_test)
- 用户：100,000个
- 角色：1,000个
- 权限：5,000个
- 操作日志：1,000,000条
- 适用：压力测试、生产验证

## 未来扩展
- [ ] Redis缓存层
- [ ] 读写分离
- [ ] 微服务架构
- [ ] 多租户支持

## 文档

- [数据库设计文档](docs/01_database_design.md)
- [优化报告](docs/02_optimization_report.md)
- [安全设计文档](docs/03_security_design.md)
- [项目框架文档](RBAC权限系统设计框架.md)

## 许可证

本项目仅用于学习和研究目的。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

---

*最后更新：2025-07-17*
