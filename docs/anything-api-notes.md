# Anything 接口梳理

本文档记录基于 `/Users/flx/IdeaProjects/to-api/anything.har` 在 2026-04-05 抽取并接入的 `https://www.anything.com/` 相关接口。

## 注册 / 登录

### 1. 发起注册

- 方法：`POST https://www.anything.com/api/graphql`
- 操作名：`SignUpWithAppPrompt`
- 请求体关键字段：

```json
{
  "input": {
    "email": "xxx@example.com",
    "postLoginRedirect": null,
    "language": "zh-CN",
    "referralCode": "y6xx8d3a"
  }
}
```

- 返回关键字段：
  - `success`
  - `projectGroup.id`
  - `user.id`
  - `organization.id`

说明：

- 该步骤只创建用户/组织/项目组。
- HAR 返回里的 `accessToken` 为空字符串，不能把这一步当成登录完成。

### 2. 邮件魔法链接

- 邮件落地页面：`GET https://www.anything.com/auth/magic-link?code=<code>&email=<email>&redirect_after_login=<path>`
- 关键参数：
  - `code`
  - `email`
  - `redirect_after_login`

说明：

- 后端实际登录不是直接请求这个 HTML 页，而是从链接里取出 `code + email` 再调用 GraphQL 登录 mutation。

### 3. 使用 magic link code 登录

- 方法：`POST https://www.anything.com/api/graphql`
- 操作名：`SignInWithMagicLinkCode`
- 请求体关键字段：

```json
{
  "input": {
    "email": "xxx@example.com",
    "codeAttempt": "662179"
  }
}
```

- 返回关键字段：
  - `user.id`
  - `user.email`
  - `accessToken`
- 响应 `Set-Cookie`：
  - `refresh_token=<jwt>; Domain=.anything.com; Path=/; ...`

说明：

- `authorization` 请求头使用的是原始 JWT 字符串，不带 `Bearer ` 前缀。
- 后续 GraphQL 请求依赖 `authorization: <accessToken>`。
- `refresh_token` 是长期 cookie，需要和 `accessToken` 一起持久化。

### 4. 刷新 access token

- 方法：`POST https://www.anything.com/api/refresh_token`
- 认证：
  - Cookie: `refresh_token=<jwt>`
- 返回字段：

```json
{
  "ok": true,
  "accessToken": "<jwt>",
  "refreshToken": "<jwt>"
}
```

HAR 里抓到的请求都返回：

```json
{"ok":false,"accessToken":"","refreshToken":""}
```

这批样本没有带上有效 `refresh_token` cookie，所以这里只能确认接口形态，成功分支是根据接口命名和项目接入方式推断的。

## 账号状态

### 1. 当前用户

- 方法：`POST https://www.anything.com/api/graphql`
- 操作名：`Me`
- 认证：
  - `authorization: <accessToken>`
- 返回关键字段：
  - `me.id`
  - `me.email`
  - `me.roles`
  - `me.createdAt`

### 2. 组织 / 套餐

- 方法：`POST https://www.anything.com/api/graphql`
- 操作名：`GetOrganizations`
- 认证：
  - `authorization: <accessToken>`
- 返回关键字段：
  - `organizations.edges[].node.id`
  - `organizations.edges[].node.name`
  - `organizations.edges[].node.plan`
  - `organizations.edges[].node.planId`
  - `organizations.edges[].node.planCredits`
  - `organizations.edges[].node.stripeProductId`
  - `organizations.edges[].node.stripeSubscriptionInterval`

HAR 样本显示：

- `plan = PRO_USAGE`
- `planId = usage_pro_20`

## 支付

### 1. 生成 Checkout 链接

- 方法：`POST https://www.anything.com/api/graphql`
- 操作名：`CreateCheckoutSessionWithLookup`
- 认证：
  - `authorization: <accessToken>`
- HAR 请求体：

```json
{
  "input": {
    "lookup": "usage_pro_price_20_monthly",
    "organizationId": "25aa1edf-8b44-4122-9684-a70edf040ed0",
    "referral": "",
    "redirectURL": "https://www.anything.com"
  }
}
```

- 返回关键字段：
  - `url`

说明：

- 返回值是可直接打开的 `https://pay.anything.com/c/pay/cs_live_...` 链接。
- 这是当前接入里保留的支付入口，不直接对接后面的 Stripe 页面下游请求。

## 当前项目接入情况

已新增：

- `platforms/anything/core.py`
- `platforms/anything/protocol_mailbox.py`
- `platforms/anything/plugin.py`

能力范围：

- 协议邮箱注册
- magic link 登录
- access/refresh token 持久化
- 账号状态查询
- checkout 链接生成

