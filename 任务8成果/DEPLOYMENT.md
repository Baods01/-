# RBAC权限管理系统前端部署指南

## 📋 部署概述

本文档详细说明了RBAC权限管理系统前端的部署流程，包括环境要求、部署步骤、配置说明和常见问题解决方案。

## 🔧 环境要求

### 服务器环境
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+) / Windows Server 2019+ / macOS 12+
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **存储**: 20GB以上可用空间
- **网络**: 稳定的互联网连接

### 软件依赖
- **Node.js**: 18.0+ 或 20.0+ (推荐LTS版本)
- **npm**: 9.0+ 或 **yarn**: 1.22+ 或 **pnpm**: 8.0+
- **Web服务器**: Nginx 1.18+ 或 Apache 2.4+ (可选)
- **SSL证书**: 用于HTTPS部署 (推荐)

### 浏览器支持
- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## 🚀 部署步骤

### 1. 环境准备

#### 1.1 安装Node.js
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs

# 验证安装
node --version
npm --version
```

#### 1.2 安装包管理器 (可选)
```bash
# 安装yarn
npm install -g yarn

# 安装pnpm
npm install -g pnpm
```

### 2. 代码部署

#### 2.1 获取源代码
```bash
# 克隆代码仓库
git clone <repository-url>
cd rbac-frontend

# 或者上传代码包
tar -xzf rbac-frontend.tar.gz
cd rbac-frontend
```

#### 2.2 安装依赖
```bash
# 使用npm
npm install --production

# 或使用yarn
yarn install --production

# 或使用pnpm
pnpm install --production
```

### 3. 环境配置

#### 3.1 创建环境配置文件
```bash
# 复制环境配置模板
cp .env.example .env.production

# 编辑生产环境配置
vim .env.production
```

#### 3.2 配置环境变量
```bash
# .env.production
# API基础URL (必须配置)
VITE_API_BASE_URL=https://api.yourdomain.com

# 应用标题
VITE_APP_TITLE=RBAC权限管理系统

# 生产环境配置
NODE_ENV=production

# 禁用Mock数据
VITE_USE_MOCK=false

# 禁用调试模式
VITE_DEBUG=false

# CDN配置 (可选)
VITE_CDN_URL=https://cdn.yourdomain.com

# 监控配置 (可选)
VITE_SENTRY_DSN=your-sentry-dsn
```

### 4. 构建应用

#### 4.1 构建生产版本
```bash
# 构建应用
npm run build

# 构建完成后，dist目录包含所有静态文件
ls -la dist/
```

#### 4.2 验证构建结果
```bash
# 预览构建结果
npm run preview

# 访问 http://localhost:4173 验证
```

### 5. Web服务器配置

#### 5.1 Nginx配置

创建Nginx配置文件 `/etc/nginx/sites-available/rbac-frontend`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 网站根目录
    root /path/to/rbac-frontend/dist;
    index index.html;
    
    # 启用gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
    }
    
    # SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    }
    
    # API代理 (可选)
    location /api/ {
        proxy_pass http://backend-server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

#### 5.2 启用Nginx配置
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/rbac-frontend /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx
```

#### 5.3 Apache配置 (可选)

创建Apache虚拟主机配置:

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    DocumentRoot /path/to/rbac-frontend/dist
    
    # 重定向到HTTPS
    Redirect permanent / https://yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    DocumentRoot /path/to/rbac-frontend/dist
    
    # SSL配置
    SSLEngine on
    SSLCertificateFile /path/to/your/certificate.crt
    SSLCertificateKeyFile /path/to/your/private.key
    
    # 启用压缩
    LoadModule deflate_module modules/mod_deflate.so
    <Location />
        SetOutputFilter DEFLATE
        SetEnvIfNoCase Request_URI \
            \.(?:gif|jpe?g|png)$ no-gzip dont-vary
        SetEnvIfNoCase Request_URI \
            \.(?:exe|t?gz|zip|bz2|sit|rar)$ no-gzip dont-vary
    </Location>
    
    # SPA路由支持
    <Directory "/path/to/rbac-frontend/dist">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
</VirtualHost>
```

### 6. SSL证书配置

#### 6.1 使用Let's Encrypt (免费)
```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 设置自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

#### 6.2 使用商业证书
```bash
# 将证书文件上传到服务器
sudo mkdir -p /etc/ssl/certs/yourdomain.com
sudo cp certificate.crt /etc/ssl/certs/yourdomain.com/
sudo cp private.key /etc/ssl/private/yourdomain.com/
sudo chmod 600 /etc/ssl/private/yourdomain.com/private.key
```

## ⚙️ 高级配置

### 1. CDN配置

#### 1.1 配置CDN加速
```bash
# 在.env.production中配置CDN
VITE_CDN_URL=https://cdn.yourdomain.com

# 上传静态资源到CDN
aws s3 sync dist/assets/ s3://your-cdn-bucket/assets/
```

#### 1.2 修改构建配置
```javascript
// vite.config.js
export default defineConfig({
  base: process.env.VITE_CDN_URL || '/',
  build: {
    rollupOptions: {
      output: {
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  }
})
```

### 2. 监控配置

#### 2.1 性能监控
```javascript
// 在main.js中添加性能监控
import { performanceMonitor } from '@/utils/performance'

// 启动性能监控
performanceMonitor.start('app-load')
```

#### 2.2 错误监控
```bash
# 配置Sentry
npm install @sentry/vue @sentry/tracing

# 在main.js中配置
import * as Sentry from "@sentry/vue"

Sentry.init({
  app,
  dsn: process.env.VITE_SENTRY_DSN,
  environment: process.env.NODE_ENV
})
```

### 3. 缓存策略

#### 3.1 浏览器缓存
```nginx
# 在Nginx配置中添加
location ~* \.(js|css)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location ~* \.(png|jpg|jpeg|gif|ico|svg)$ {
    expires 6M;
    add_header Cache-Control "public";
}
```

#### 3.2 Service Worker缓存
```javascript
// 注册Service Worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
}
```

## 🔍 常见问题解决

### 1. 构建问题

#### Q: 构建时内存不足
```bash
# 增加Node.js内存限制
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

#### Q: 依赖安装失败
```bash
# 清理缓存重新安装
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 2. 部署问题

#### Q: 页面刷新404错误
**解决方案**: 确保Web服务器配置了SPA路由支持，参考上述Nginx/Apache配置。

#### Q: 静态资源加载失败
**解决方案**: 检查`VITE_API_BASE_URL`配置和CDN配置是否正确。

#### Q: HTTPS证书问题
```bash
# 检查证书有效性
openssl x509 -in certificate.crt -text -noout

# 检查私钥匹配
openssl rsa -in private.key -check
```

### 3. 性能问题

#### Q: 首屏加载慢
**解决方案**:
1. 启用gzip压缩
2. 配置CDN加速
3. 优化图片资源
4. 启用浏览器缓存

#### Q: 内存使用过高
**解决方案**:
1. 检查内存泄漏
2. 优化组件销毁
3. 减少全局状态

### 4. 安全问题

#### Q: XSS攻击防护
**解决方案**: 确保配置了安全头，参考上述Nginx配置中的安全头设置。

#### Q: CSRF攻击防护
**解决方案**: 配置SameSite Cookie和CSRF Token验证。

## 📊 部署检查清单

### 部署前检查
- [ ] 环境变量配置正确
- [ ] API接口地址可访问
- [ ] SSL证书配置完成
- [ ] 域名DNS解析正确
- [ ] 防火墙端口开放

### 部署后检查
- [ ] 网站可正常访问
- [ ] 所有页面功能正常
- [ ] API接口调用正常
- [ ] 移动端适配正常
- [ ] 性能指标达标

### 监控检查
- [ ] 错误监控配置
- [ ] 性能监控配置
- [ ] 日志收集配置
- [ ] 备份策略配置
- [ ] 更新策略配置

## 📞 技术支持

如在部署过程中遇到问题，请联系技术支持：

- 📧 邮箱：deploy@rbac-system.com
- 📱 电话：400-123-4567
- 💬 在线支持：https://support.rbac-system.com
- 📖 文档中心：https://docs.rbac-system.com

---

**部署团队**：RBAC DevOps Team  
**文档版本**：v1.0.0  
**最后更新**：2025-07-25
