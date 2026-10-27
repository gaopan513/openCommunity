# openCommunity 生产部署指南

> 适用版本：Django 5 + DRF 后端 / Vue 3 + Vite 前端
> 开发环境默认 SQLite + DEBUG=True，**不可直接用于生产**；本文描述完整的生产形态。

## 一、环境变量

后端全部通过环境变量注入（参见 `backend/.env.example`），核心项：

| 变量 | 必填 | 说明 |
|---|---|---|
| `DJANGO_SECRET_KEY` | ✅ 生产必填 | 长随机字符串；未设置且 DEBUG=False 时后端拒绝启动 |
| `DJANGO_DEBUG` | ✅ | 生产必须 `False` |
| `DJANGO_ALLOWED_HOSTS` | ✅ | 逗号分隔域名白名单，生产不允许 `*` |
| `DJANGO_CORS_ALLOW_ALL` | — | 生产必须 `False`（缺省即 False） |
| `DJANGO_CORS_ALLOWED_ORIGINS` | 按需 | 前端同域部署时无需配置 |
| `DJANGO_DB_ENGINE` 等 `DJANGO_DB_*` | 按需 | 不设则使用 SQLite；生产建议 PostgreSQL |

前端仅一个可选变量 `VITE_API_BASE_URL`（参见 `frontend/.env.example`）：
默认 `/api/v1` 相对路径，开发走 vite 代理、生产走同域反代，**同域部署时无需设置**。

## 二、数据库：切换 PostgreSQL

1. 安装驱动：`pip install -r requirements.txt`（含 `psycopg2-binary`）。
2. 创建库与用户，并按上表设置 `DJANGO_DB_*` 环境变量。
3. 执行迁移：

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser   # 管理员
```

## 三、后端生产运行

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 4
```

- 静态文件（含 Django admin）：`collectstatic` 收集到 `STATIC_ROOT` 后由 nginx 服务；
- 媒体文件（用户上传）：由 nginx 直接服务 `media/` 目录，**不要**用 Django 开发服务器对外提供；
- 进程管理建议使用 systemd 或 supervisor。

## 四、nginx 参考配置

```nginx
server {
    listen 443 ssl;
    server_name example.com;

    # 前端构建产物
    root /var/www/opencommunity/dist;
    index index.html;

    # 前端路由（history 模式）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反代到 gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10m;   # 与后端上传上限一致
    }

    # 用户上传的媒体文件
    location /media/ {
        alias /path/to/openCommunity/backend/media/;
        expires 7d;
    }

    # Django 静态文件（admin 后台等）
    location /static/ {
        alias /path/to/static_root/;
        expires 30d;
    }
}
```

## 五、前端构建与部署

```bash
cd frontend
npm install
npm run build   # 产物在 dist/
```

将 `dist/` 发布到 nginx 的前端根目录即可。前后端同域部署时无需 CORS 配置。

## 六、微信小程序端

工程位于仓库顶层 `miniprogram/`（uni-app + Vue3），复用同一后端与 nginx，**无需新增服务端组件**：

```bash
cd miniprogram
npm install
npm run build:mp-weixin   # 产物在 dist/build/mp-weixin，用微信开发者工具导入上传
```

上线前配置项：

| 项 | 说明 |
|---|---|
| 后端环境变量 | 新增 `WECHAT_MINIAPP_APPID` / `WECHAT_MINIAPP_SECRET`（见 `backend/.env.example`）；为空时 `/api/v1/auth/wechat-login/` 返回明确错误码 50101 |
| 小程序合法域名 | 微信公众平台配置 request / uploadFile / downloadFile 合法域名 = 本 nginx 的 HTTPS 域名（同域复用，证书自然覆盖；nginx 无需变更） |
| 前端环境变量 | `miniprogram/.env.production` 的 `VITE_API_BASE_URL` 指向线上 HTTPS 域名 |
| 隐私合规 | 公众平台完善《用户隐私保护指引》（头像等收集声明）；manifest 已开启 `__usePrivacyCheck__` |

数据库变更注意：微信登录依赖 users 迁移 `0002_user_openid_user_unionid`，部署时须执行 `python manage.py migrate`。

联调与提审核对清单见 [miniprogram-checklist.md](miniprogram-checklist.md)。

## 七、安全清单

- [ ] `DJANGO_SECRET_KEY` 已通过环境变量注入，未写入代码仓库；
- [ ] `DJANGO_DEBUG=False`、`ALLOWED_HOSTS` 为显式白名单、CORS 未全放行；
- [ ] 全站 HTTPS（JWT 明文传输必须走 TLS）；
- [ ] 数据库已切换 PostgreSQL 并定期备份（SQLite 仅适用于单机开发）；
- [ ] `db.sqlite3`、`media/`、`.env` 均已加入 `.gitignore`，不在仓库中。

### Token 存储的权衡说明（架构决策）

当前 access/refresh token 存于浏览器 localStorage，XSS 攻击可读取。经评估接受的依据：

1. 全项目**禁止使用 `v-html` 渲染任何用户生成内容**（现有代码已遵守，全部为文本插值），XSS 注入面极小；后续开发必须延续该纪律，引入富文本时须配套服务端消毒（如 bleach）。
2. refresh token 已启用轮换 + 黑名单，登出/改密后旧 token 无法续期，泄露窗口有限。

若后续安全等级要求提高，演进路径为：refresh token 改存 HttpOnly Cookie（配合 SameSite），access token 保持内存态——需要同步调整 SimpleJWT 认证方式与前端刷新逻辑，属独立改造项。
