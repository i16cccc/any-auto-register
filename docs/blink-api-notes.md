# Blink 接口梳理

本文档记录基于 `注册.har` 和 `支付1.har` 在 2026-03-29 抽取并接入的 Blink Web 接口。

## 注册

### 1. 发送魔法链接

- 方法：`POST https://blink.new/api/auth/main-app/magic-link`
- 请求体：

```json
{
  "email": "xxx@example.com",
  "redirectUrl": "/my-blink-bb78"
}
```

- 用途：向邮箱发送 Blink 的 magic link

### 2. 兑换 magic token

- 方法：`GET https://blink.new/api/auth/main-app/magic-link?token=<magic_token>&email=<email>`
- 返回关键字段：
  - `success`
  - `customToken`
  - `user.id`
  - `workspaceSlug`

### 3. Firebase 登录

- 方法：`POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=<api_key>`
- 返回关键字段：
  - `idToken`
  - `refreshToken`
  - `expiresIn`

说明：

- 这里拿到的是 Firebase 层的长 token
- 项目里把它作为 Blink 账号的主刷新凭据保存

### 4. 交换 Blink app token

- 方法：`POST https://blink.new/api/auth/token`
- 请求体：

```json
{
  "idToken": "<firebase id token>"
}
```

- 返回关键字段：
  - `access_token`
  - `refresh_token`
  - `expires_in`

说明：

- `access_token` 只有 900 秒，不适合作为长期主 token
- 当前已验证的 `session-data`、`credits/migrate`、`referral/generate`、`stripe/checkout` 仍然使用 Firebase `idToken` 作为 `Authorization`
- `/api/auth/token` 返回的短 token 目前只做补充存档，不作为这些 Web 动作的主鉴权凭据

### 5. 建立 Web session

- 方法：`POST https://blink.new/api/auth/session`
- 请求体：

```json
{
  "idToken": "<firebase id token>"
}
```

- 结果：返回 `session` cookie

### 6. 初始化用户记录

- 方法：`POST https://blink.new/api/users/create`
- 认证：`Authorization: Bearer <firebase id token>`
- 用途：创建/补齐 Blink 用户记录与工作区信息

### 7. 注册后动作

- `POST https://blink.new/api/credits/migrate`
- `POST https://blink.new/api/referral/generate`

认证：

- `Authorization: Bearer <firebase id token>`
- `Cookie: session=<session token>`

## 套餐/额度状态

### 1. 查询 session-data

- 方法：`GET https://blink.new/api/auth/session-data`
- 认证：
  - `Authorization: Bearer <firebase id token>`
  - `Cookie: session=<session token>`
- 关键字段：
  - `user.customer_id`
  - `user.usage.daily_credits_limit`
  - `user.usage.monthly_credits_limit`
  - `user.usage.billing_period_credits_limit`
  - `workspace.id`
  - `workspace.slug`
  - `workspace.tier`
  - `workspace.plan_type`

HAR 对比结果：

- 注册后免费态：`workspace.tier = free`，`billing_period_credits_limit = 0`
- 支付完成后：`workspace.tier = pro`，`billing_period_credits_limit = 200`

## 支付

### 1. 生成 Stripe Checkout 链接

- 方法：`POST https://blink.new/api/stripe/checkout`
- 认证：
  - `Authorization: Bearer <firebase id token>`
  - `Cookie: session=<session token>`
- HAR 请求体：

```json
{
  "priceId": "price_1S2oW1IChkSeVZoQl1420r64",
  "planId": "pro",
  "toltReferralId": null,
  "workspaceId": "wsp_4a83yg0k",
  "cancelUrl": "https://blink.new/my-blink-bb78?showPricing=true"
}
```

- 返回关键字段：
  - `sessionId`
  - `url`

说明：

- 这是当前项目实际接入的上游支付入口
- 返回的 `url` 是可直接打开的 Stripe Checkout 地址

## API Key

### 1. 创建 Workspace API Key

- 方法：`POST https://blink.new/api/workspace/api-keys`
- 认证：
  - `Authorization: Bearer <firebase id token>`
  - `Cookie: session=<session token>`
  - `Cookie: workspace_slug=<workspace slug>`
- 请求体：

```json
{
  "workspaceId": "wsp_4a83yg0k",
  "name": "1111开发"
}
```

- 返回关键字段：
  - `id`
  - `name`
  - `key_value`
  - `key_prefix`

说明：

- `key_value` 是明文 API Key，只会在创建时返回一次
- 当前项目已将它接为账号列表动作 `create_api_key`
- 动作成功后会把 `key_value` 以 `api_key` 凭证形式保存到账号图中，便于后续复制和导出

## 不建议直接对接的下游接口

支付 HAR 里还能看到：

- `POST https://api.stripe.com/v1/payment_pages/<cs_live...>/init`
- `GET https://api.stripe.com/v1/payment_pages/<cs_live...>/poll`

这些都只是 Stripe Checkout 页面的下游请求，不应直接接入。原因：

- `cs_live_*` 是运行时动态 session
- `payment_pages/*` 依赖上游 `/api/stripe/checkout`
- 正确入口是 Blink 自己的 `POST /api/stripe/checkout`

## 当前项目接入情况

### 已接入后端

- `platforms/blink/plugin.py`
  - `get_account_state`
  - `generate_checkout_link`
  - `create_api_key`
- `platforms/blink/protocol_mailbox.py`
  - 注册完成后补抓 `session-data`
  - 注册成功后最佳努力自动生成 Pro 支付链接
- `platforms/blink/core.py`
  - 注册
  - Firebase refresh
  - `session-data`
  - `/api/stripe/checkout`
- `infrastructure/platform_runtime.py`
  - 执行 `generate_checkout_link` 后会把返回的支付链接写回账号 `cashier_url`

## 已知限制

- Blink 的 Firebase `idToken` 也会过期，但可以通过 `firebase_refresh_token` 稳定重建
- Blink 的 Web `access_token` 有效期只有 900 秒，目前不作为主要 Web 动作鉴权凭据
- 注册流程现在会在成功后最佳努力自动生成一次 Pro 支付链接；如果这一步失败，不影响账号注册成功
- 当前账号动作会优先尝试现有 `id_token`，失效后再用 Firebase refresh token 重建会话
- 当前动作不会自动把刷新后的新 token 回写数据库，但会保存新生成的支付链接到 `cashier_url`
