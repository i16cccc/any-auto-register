# 前后端接口文档

本文档用于给前端和后端协作对接，覆盖两类接口：

- 当前项目里已经存在、可直接调用的管理端接口
- 面向未来 C 端用户体系的规划接口

其中注册链路的原则是：

- 前端只调用本系统后端接口
- 后端统一封装平台注册、验证码、邮箱、代理、任务调度等逻辑
- 前端不直接调用各个平台的第三方注册接口

## 1. 文档约定

### 1.1 基础信息

- Base URL：`/api`
- Content-Type：`application/json`
- 当前项目的大多数接口直接返回 JSON 对象或数组，不做统一 `code/data/message` 包装
- 当前项目的错误响应主要是 FastAPI 默认文本错误或 `{"detail": "..."}`

### 1.2 状态标记

- `已实现`：当前仓库已经存在对应后端接口
- `规划中`：本轮只做接口文档定义，后端尚未落地

### 1.3 鉴权约定

当前已实现接口尚未接入用户登录态。为支持 C 端，建议后续采用 Bearer Token：

```http
Authorization: Bearer <access_token>
```

## 2. 注册链路说明

注册链路是本系统最核心的前后端协作接口。

### 2.1 职责边界

前端职责：

- 获取平台列表
- 获取注册所需配置项和 provider 元数据
- 组织注册参数并调用后端注册接口
- 轮询任务状态，或订阅日志流
- 展示注册结果、错误信息、支付链接等

后端职责：

- 校验请求参数
- 读取平台能力和全局配置
- 组装邮箱 provider、验证码 provider、浏览器执行器、代理
- 封装平台注册逻辑
- 创建异步任务并持久化
- 输出任务状态、事件流、结果数据

### 2.2 推荐时序

#### 管理端当前时序

1. `GET /api/platforms`
2. `GET /api/config`
3. `GET /api/config/options`
4. `POST /api/tasks/register`
5. `GET /api/tasks/{task_id}` 或 `GET /api/tasks/{task_id}/logs/stream`

#### C 端推荐时序

1. `POST /api/auth/login`
2. `GET /api/app/platforms`
3. `GET /api/app/config/options`
4. `POST /api/app/tasks/register`
5. `GET /api/app/tasks/{task_id}` 或 `GET /api/app/tasks/{task_id}/events`

## 3. 认证接口

本组接口为 C 端所需接口，当前仓库尚未实现。

### 3.1 登录

- 状态：`规划中`
- 方法：`POST /api/auth/login`
- 用途：用户或管理员登录

请求体：

```json
{
  "account": "admin@example.com",
  "password": "******"
}
```

响应示例：

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "expires_in": 7200,
  "user": {
    "id": 1,
    "username": "admin",
    "display_name": "管理员",
    "role_code": "admin"
  }
}
```

### 3.2 刷新 Token

- 状态：`规划中`
- 方法：`POST /api/auth/refresh`

请求体：

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

### 3.3 登出

- 状态：`规划中`
- 方法：`POST /api/auth/logout`

请求体：

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

### 3.4 当前用户信息

- 状态：`规划中`
- 方法：`GET /api/auth/me`
- 用途：返回用户资料、角色、权限、可访问平台

响应示例：

```json
{
  "id": 12,
  "username": "tom",
  "display_name": "Tom",
  "role_code": "user",
  "permissions": [
    "app:platform:view",
    "app:task:create",
    "app:task:view_self"
  ],
  "platforms": [
    {
      "platform_code": "chatgpt",
      "platform_name": "ChatGPT"
    }
  ]
}
```

## 4. 用户端接口

本组接口是面向普通用户的推荐接口命名，当前仓库尚未实现。

### 4.1 获取当前用户可用平台

- 状态：`规划中`
- 方法：`GET /api/app/platforms`
- 用途：只返回当前登录用户被授权的平台

响应示例：

```json
[
  {
    "name": "chatgpt",
    "display_name": "ChatGPT",
    "version": "1.0.0",
    "supported_executors": ["protocol", "headed"],
    "supported_identity_modes": ["mailbox", "oauth_browser"],
    "supported_oauth_providers": ["google"],
    "supported_executor_options": [
      { "value": "protocol", "label": "协议模式" },
      { "value": "headed", "label": "可视浏览器自动" }
    ],
    "supported_identity_mode_options": [
      { "value": "mailbox", "label": "系统邮箱" },
      { "value": "oauth_browser", "label": "第三方账号" }
    ],
    "supported_oauth_provider_options": [
      { "value": "google", "label": "Google" }
    ]
  }
]
```

### 4.2 获取用户侧注册元数据

- 状态：`规划中`
- 方法：`GET /api/app/config/options`
- 用途：返回用户侧注册页需要的可用 provider、验证码策略、平台选项

说明：

- 结构可复用当前 `GET /api/config/options`
- 用户侧建议只返回当前用户可见平台和允许使用的 provider
- 前端通过该接口动态渲染注册表单，不在前端写死平台差异

响应结构建议与管理端 `GET /api/config/options` 保持一致。

### 4.3 发起注册任务

- 状态：`规划中`
- 方法：`POST /api/app/tasks/register`
- 用途：C 端发起平台注册，由后端统一封装注册逻辑
- 权限：用户必须已登录，且拥有目标平台访问权限

请求体：

```json
{
  "platform": "chatgpt",
  "email": "user@example.com",
  "password": "Password@123",
  "count": 1,
  "concurrency": 1,
  "proxy": "",
  "executor_type": "protocol",
  "captcha_solver": "auto",
  "extra": {
    "identity_provider": "mailbox",
    "oauth_provider": "",
    "oauth_email_hint": "",
    "chrome_user_data_dir": "",
    "chrome_cdp_url": "",
    "mail_provider": "moemail"
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `platform` | string | 是 | 平台编码，对应平台列表中的 `name` |
| `email` | string \| null | 否 | 部分模式由系统邮箱自动生成，可为空 |
| `password` | string \| null | 否 | 平台账号密码，可由前端输入或后端生成 |
| `count` | int | 否 | 创建数量，默认 `1` |
| `concurrency` | int | 否 | 并发数，默认 `1` |
| `proxy` | string \| null | 否 | 代理地址 |
| `executor_type` | string | 否 | `protocol` / `headless` / `headed` |
| `captcha_solver` | string | 否 | 当前建议固定传 `auto` |
| `extra.identity_provider` | string | 是 | `mailbox` 或 `oauth_browser` |
| `extra.oauth_provider` | string | 否 | 第三方登录 provider，如 `google` |
| `extra.oauth_email_hint` | string | 否 | 第三方登录邮箱提示 |
| `extra.chrome_user_data_dir` | string | 否 | 复用本机浏览器 profile 路径 |
| `extra.chrome_cdp_url` | string | 否 | 远端 Chrome CDP 地址 |
| `extra.mail_provider` | string | 否 | 邮箱 provider 编码 |
| `extra.*` | string | 否 | 其他 provider 动态字段，由 `/config/options` 返回 |

响应示例：

```json
{
  "id": "task_1770000000000_ab12cd",
  "task_id": "task_1770000000000_ab12cd",
  "type": "register",
  "platform": "chatgpt",
  "status": "pending",
  "terminal": false,
  "cancellable": true,
  "progress": "0/1",
  "progress_detail": {
    "current": 0,
    "total": 1,
    "label": "0/1"
  },
  "success": 0,
  "error_count": 0,
  "errors": [],
  "cashier_urls": [],
  "data": null,
  "result": {
    "errors": [],
    "cashier_urls": [],
    "data": null
  },
  "error": "",
  "created_at": "2026-04-01T14:00:00Z",
  "started_at": null,
  "finished_at": null,
  "updated_at": "2026-04-01T14:00:00Z"
}
```

失败场景：

- `401`：未登录
- `403`：无该平台注册权限
- `422`：参数校验失败
- `500`：后端创建任务失败

### 4.4 我的任务列表

- 状态：`规划中`
- 方法：`GET /api/app/tasks`
- 用途：查询当前用户自己的任务

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `platform` | string | 否 | 平台筛选 |
| `status` | string | 否 | 状态筛选 |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页数量，默认 `50` |

### 4.5 我的任务详情

- 状态：`规划中`
- 方法：`GET /api/app/tasks/{task_id}`

### 4.6 我的任务事件

- 状态：`规划中`
- 方法：`GET /api/app/tasks/{task_id}/events`

### 4.7 我的订单

- 状态：`规划中`
- 方法：`GET /api/app/orders`

### 4.8 我的订单详情

- 状态：`规划中`
- 方法：`GET /api/app/orders/{order_no}`

### 4.9 我的订阅

- 状态：`规划中`
- 方法：`GET /api/app/subscriptions`

### 4.10 我的资料

- 状态：`规划中`
- 方法：`GET /api/app/profile`

### 4.11 更新我的资料

- 状态：`规划中`
- 方法：`PATCH /api/app/profile`

## 5. 管理端接口

本组接口为当前仓库中已经存在的主要后端接口，可作为后台 Web UI 调用依据。

### 5.1 平台列表

- 状态：`已实现`
- 方法：`GET /api/platforms`
- 用途：获取系统已加载的平台及其能力信息

响应示例：

```json
[
  {
    "name": "chatgpt",
    "display_name": "ChatGPT",
    "version": "1.0.0",
    "supported_executors": ["protocol", "headless", "headed"],
    "supported_identity_modes": ["mailbox", "oauth_browser"],
    "supported_oauth_providers": ["google", "github"],
    "supported_executor_options": [
      { "value": "protocol", "label": "协议模式" },
      { "value": "headless", "label": "后台浏览器自动" },
      { "value": "headed", "label": "可视浏览器自动" }
    ],
    "supported_identity_mode_options": [
      { "value": "mailbox", "label": "系统邮箱" },
      { "value": "oauth_browser", "label": "第三方账号" }
    ],
    "supported_oauth_provider_options": [
      { "value": "google", "label": "Google" },
      { "value": "github", "label": "GitHub" }
    ]
  }
]
```

### 5.2 平台桌面状态

- 状态：`已实现`
- 方法：`GET /api/platforms/{platform}/desktop-state`

### 5.3 获取注册页配置

- 状态：`已实现`
- 方法：`GET /api/config`
- 用途：获取扁平化配置，例如默认执行器、默认 provider、浏览器 profile 路径等

响应示例：

```json
{
  "default_executor": "protocol",
  "default_identity_provider": "mailbox",
  "default_oauth_provider": "",
  "oauth_email_hint": "",
  "chrome_user_data_dir": "",
  "chrome_cdp_url": ""
}
```

### 5.4 获取注册页元数据

- 状态：`已实现`
- 方法：`GET /api/config/options`
- 用途：返回前端注册页所需的 provider、验证码策略、平台可选项元数据

响应字段：

| 字段 | 说明 |
|---|---|
| `mailbox_providers` | 邮箱 provider 定义列表 |
| `captcha_providers` | 验证码 provider 定义列表 |
| `mailbox_drivers` | 邮箱 driver 模板 |
| `captcha_drivers` | 验证码 driver 模板 |
| `captcha_policy` | 验证码策略 |
| `mailbox_settings` | 当前已配置邮箱 provider 列表 |
| `captcha_settings` | 当前已配置验证码 provider 列表 |
| `executor_options` | 执行器选项 |
| `identity_mode_options` | 身份模式选项 |
| `oauth_provider_options` | OAuth provider 选项 |

示例：

```json
{
  "mailbox_providers": [
    {
      "provider_type": "mailbox",
      "provider_key": "moemail",
      "value": "moemail",
      "label": "MoeMail",
      "description": "临时邮箱服务",
      "driver_type": "http",
      "default_auth_mode": "token",
      "auth_modes": [
        { "value": "token", "label": "Token" }
      ],
      "fields": [
        { "key": "api_url", "label": "API URL" }
      ]
    }
  ],
  "captcha_providers": [],
  "mailbox_settings": [],
  "captcha_settings": [],
  "captcha_policy": {
    "protocol_mode": "remote",
    "protocol_order": [],
    "browser_mode": ""
  },
  "executor_options": [
    { "value": "protocol", "label": "协议模式" }
  ],
  "identity_mode_options": [
    { "value": "mailbox", "label": "系统邮箱" }
  ],
  "oauth_provider_options": []
}
```

### 5.5 更新配置

- 状态：`已实现`
- 方法：`PUT /api/config`

请求体：

```json
{
  "data": {
    "default_executor": "protocol",
    "chrome_user_data_dir": ""
  }
}
```

响应示例：

```json
{
  "ok": true,
  "updated": {
    "default_executor": "protocol",
    "chrome_user_data_dir": ""
  }
}
```

### 5.6 发起注册任务

- 状态：`已实现`
- 方法：`POST /api/tasks/register`
- 用途：管理端发起平台注册任务

请求体字段与 `POST /api/app/tasks/register` 一致。

推荐前端请求体：

```json
{
  "platform": "chatgpt",
  "email": "",
  "password": "",
  "count": 1,
  "concurrency": 1,
  "proxy": "",
  "executor_type": "protocol",
  "captcha_solver": "auto",
  "extra": {
    "identity_provider": "mailbox",
    "oauth_provider": "",
    "oauth_email_hint": "",
    "chrome_user_data_dir": "",
    "chrome_cdp_url": "",
    "mail_provider": "moemail"
  }
}
```

响应字段与任务详情结构一致。

### 5.7 任务列表

- 状态：`已实现`
- 方法：`GET /api/tasks`

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `platform` | string | 否 | 平台筛选 |
| `status` | string | 否 | 状态筛选 |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页数量，默认 `50` |

响应示例：

```json
{
  "total": 1,
  "page": 1,
  "items": [
    {
      "id": "task_1770000000000_ab12cd",
      "task_id": "task_1770000000000_ab12cd",
      "type": "register",
      "platform": "chatgpt",
      "status": "running",
      "progress": "0/1",
      "progress_detail": {
        "current": 0,
        "total": 1,
        "label": "0/1"
      },
      "success": 0,
      "error_count": 0,
      "errors": [],
      "cashier_urls": [],
      "error": "",
      "created_at": "2026-04-01T14:00:00Z",
      "started_at": "2026-04-01T14:00:02Z",
      "finished_at": null,
      "updated_at": "2026-04-01T14:00:05Z",
      "result": {
        "errors": [],
        "cashier_urls": [],
        "data": null
      }
    }
  ]
}
```

### 5.8 任务详情

- 状态：`已实现`
- 方法：`GET /api/tasks/{task_id}`

返回字段与任务列表中的单个任务对象一致。

### 5.9 任务事件

- 状态：`已实现`
- 方法：`GET /api/tasks/{task_id}/events`

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `since` | int | 否 | 起始事件 ID，默认 `0` |
| `limit` | int | 否 | 返回条数，默认 `200` |

响应示例：

```json
{
  "items": [
    {
      "id": 101,
      "task_id": "task_1770000000000_ab12cd",
      "type": "state",
      "level": "info",
      "message": "任务已创建: register",
      "line": "[22:00:01] 任务已创建: register",
      "detail": {},
      "created_at": "2026-04-01T14:00:01Z"
    }
  ]
}
```

### 5.10 任务日志流

- 状态：`已实现`
- 方法：`GET /api/tasks/{task_id}/logs/stream`
- 类型：`text/event-stream`
- 用途：前端实时接收日志和终态事件

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `since` | int | 否 | 事件游标，默认 `0` |

事件示例：

```text
retry: 5000
: connected

data: {"id":101,"task_id":"task_1770000000000_ab12cd","type":"state","level":"info","message":"任务已创建: register","line":"[22:00:01] 任务已创建: register","detail":{},"created_at":"2026-04-01T14:00:01Z"}

data: {"done":true,"status":"succeeded","line":"任务已完成"}
```

### 5.11 取消任务

- 状态：`已实现`
- 方法：`POST /api/tasks/{task_id}/cancel`

响应示例：

```json
{
  "id": "task_1770000000000_ab12cd",
  "task_id": "task_1770000000000_ab12cd",
  "type": "register",
  "platform": "chatgpt",
  "status": "cancel_requested",
  "progress": "0/1",
  "progress_detail": {
    "current": 0,
    "total": 1,
    "label": "0/1"
  },
  "success": 0,
  "error_count": 0,
  "errors": [],
  "cashier_urls": [],
  "error": "",
  "created_at": "2026-04-01T14:00:00Z",
  "started_at": null,
  "finished_at": null,
  "updated_at": "2026-04-01T14:00:08Z",
  "result": {
    "errors": [],
    "cashier_urls": [],
    "data": null
  }
}
```

### 5.12 历史任务日志

- 状态：`已实现`
- 方法：`GET /api/tasks/logs`

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `platform` | string | 否 | 平台筛选 |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页数量，默认 `50` |

响应示例：

```json
{
  "total": 1,
  "page": 1,
  "items": [
    {
      "id": 1,
      "platform": "chatgpt",
      "email": "user@example.com",
      "status": "success",
      "error": "",
      "detail": {},
      "created_at": "2026-04-01T14:00:00Z"
    }
  ]
}
```

### 5.13 账号列表

- 状态：`已实现`
- 方法：`GET /api/accounts`

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `platform` | string | 否 | 平台筛选 |
| `status` | string | 否 | 状态筛选 |
| `email` | string | 否 | 邮箱筛选 |
| `page` | int | 否 | 页码，默认 `1` |
| `page_size` | int | 否 | 每页数量，默认 `20` |

响应示例：

```json
{
  "total": 1,
  "page": 1,
  "items": [
    {
      "id": 1001,
      "platform": "chatgpt",
      "email": "user@example.com",
      "password": "Password@123",
      "user_id": "user_123",
      "primary_token": "",
      "trial_end_time": 0,
      "cashier_url": "",
      "lifecycle_status": "registered",
      "validity_status": "unknown",
      "plan_state": "unknown",
      "plan_name": "",
      "display_status": "registered",
      "overview": {},
      "credentials": {},
      "provider_accounts": [],
      "provider_resources": [],
      "created_at": "2026-04-01T14:00:00Z",
      "updated_at": "2026-04-01T14:00:00Z"
    }
  ]
}
```

### 5.14 新增账号

- 状态：`已实现`
- 方法：`POST /api/accounts`

请求体：

```json
{
  "platform": "chatgpt",
  "email": "user@example.com",
  "password": "Password@123",
  "user_id": "",
  "lifecycle_status": "registered",
  "overview": {},
  "credentials": {},
  "provider_accounts": [],
  "provider_resources": [],
  "primary_token": "",
  "cashier_url": "",
  "region": "",
  "trial_end_time": 0
}
```

### 5.15 账号详情

- 状态：`已实现`
- 方法：`GET /api/accounts/{account_id}`

### 5.16 更新账号

- 状态：`已实现`
- 方法：`PATCH /api/accounts/{account_id}`

### 5.17 删除账号

- 状态：`已实现`
- 方法：`DELETE /api/accounts/{account_id}`

响应示例：

```json
{
  "ok": true
}
```

### 5.18 账号统计

- 状态：`已实现`
- 方法：`GET /api/accounts/stats`

### 5.19 导入账号

- 状态：`已实现`
- 方法：`POST /api/accounts/import`

请求体：

```json
{
  "platform": "chatgpt",
  "lines": [
    "user1@example.com password1",
    "user2@example.com password2"
  ]
}
```

### 5.20 导出账号

- 状态：`已实现`
- 方法：
  - `GET /api/accounts/export`
  - `POST /api/accounts/export/json`
  - `POST /api/accounts/export/csv`
  - `POST /api/accounts/export/sub2api`
  - `POST /api/accounts/export/cpa`

### 5.21 平台动作列表

- 状态：`已实现`
- 方法：`GET /api/actions/{platform}`

### 5.22 执行平台动作

- 状态：`已实现`
- 方法：`POST /api/actions/{platform}/{account_id}/{action_id}`

请求体：

```json
{
  "params": {}
}
```

### 5.23 代理列表

- 状态：`已实现`
- 方法：`GET /api/proxies`

### 5.24 新增代理

- 状态：`已实现`
- 方法：`POST /api/proxies`

请求体：

```json
{
  "url": "http://127.0.0.1:7890",
  "region": "SG"
}
```

### 5.25 批量新增代理

- 状态：`已实现`
- 方法：`POST /api/proxies/bulk`

请求体：

```json
{
  "proxies": [
    "http://127.0.0.1:7890",
    "http://127.0.0.1:7891"
  ],
  "region": "SG"
}
```

### 5.26 删除代理

- 状态：`已实现`
- 方法：`DELETE /api/proxies/{proxy_id}`

### 5.27 启停代理

- 状态：`已实现`
- 方法：`PATCH /api/proxies/{proxy_id}/toggle`

### 5.28 检测代理

- 状态：`已实现`
- 方法：`POST /api/proxies/check`

### 5.29 Solver 状态

- 状态：`已实现`
- 方法：`GET /api/solver/status`

### 5.30 重启 Solver

- 状态：`已实现`
- 方法：`POST /api/solver/restart`

## 6. 错误码建议

当前已实现接口主要沿用 FastAPI 默认行为。为了后续 C 端统一，建议新接口按下面语义使用：

| 状态码 | 说明 |
|---|---|
| `200` | 请求成功 |
| `201` | 创建成功 |
| `400` | 业务参数错误 |
| `401` | 未登录或 token 失效 |
| `403` | 无权限 |
| `404` | 资源不存在 |
| `422` | 请求参数校验失败 |
| `500` | 服务端异常 |

推荐错误响应：

```json
{
  "detail": "任务不存在"
}
```

## 7. 前端接入建议

### 7.1 当前管理端

现有前端调用方式可继续保持：

1. `GET /api/platforms`
2. `GET /api/config`
3. `GET /api/config/options`
4. `POST /api/tasks/register`
5. `GET /api/tasks/{task_id}` 或 `GET /api/tasks/{task_id}/logs/stream`

### 7.2 后续 C 端

后续普通用户侧建议按下述方式对接：

1. 登录获取 token
2. 获取可访问平台 `GET /api/app/platforms`
3. 渲染注册表单
4. 调用 `POST /api/app/tasks/register`
5. 轮询 `GET /api/app/tasks/{task_id}`
6. 展示任务日志、注册结果、支付链接

### 7.3 关键原则
[runtime.log](../../../../%E6%B3%A8%E5%86%8C%E6%9C%BA/chatgpt-03-31/runtime/logs/runtime.log)
- 前端不直接调用第三方平台接口
- 平台差异通过 `platforms` 与 `config/options` 元数据驱动
- 注册逻辑统一沉淀在后端任务系统中
- C 端接口建议统一收口到 `/api/app/*`
- 管理端接口继续保留在现有 `/api/*`
