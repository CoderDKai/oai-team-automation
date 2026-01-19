# API Contract: 邮件管理 API

**Base URL**: `https://<worker-name>.<account>.workers.dev/api`
**Authentication**: Bearer Token (API Key)

## Authentication

所有 API 请求必须包含 `Authorization` 头：

```
Authorization: Bearer <api_key>
```

### 错误响应

| Status | Description |
|--------|-------------|
| 401 | 未提供 API Key 或 API Key 无效 |
| 403 | API Key 权限不足 |

---

## Mailboxes API

### GET /api/mailboxes

获取所有邮箱账号列表。

**Response 200**:
```json
{
  "data": [
    {
      "id": "uuid",
      "address": "user@example.com",
      "enabled": true,
      "emailCount": 42,
      "unreadCount": 5,
      "createdAt": "2026-01-16T10:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /api/mailboxes

创建新邮箱账号。

**Request Body**:
```json
{
  "address": "newuser@example.com"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "address": "newuser@example.com",
  "enabled": true,
  "createdAt": "2026-01-16T10:00:00Z"
}
```

**Error 409**: 邮箱已存在

### PATCH /api/mailboxes/{address}

更新邮箱设置。

**Request Body**:
```json
{
  "enabled": false
}
```

**Response 200**: 返回更新后的邮箱对象

**Error 404**: 邮箱不存在

### DELETE /api/mailboxes/{address}

删除邮箱及其所有邮件。

**Response 204**: 删除成功

**Error 404**: 邮箱不存在

---

## Emails API

### GET /api/mailboxes/{address}/emails

获取指定邮箱的邮件列表。

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | number | 1 | 页码 |
| limit | number | 20 | 每页数量 (max: 100) |
| unread | boolean | - | 筛选未读邮件 |
| starred | boolean | - | 筛选星标邮件 |
| trashed | boolean | false | 是否显示垃圾箱 |
| archived | boolean | false | 是否显示归档 |

**Response 200**:
```json
{
  "data": [
    {
      "id": "uuid",
      "from": "sender@example.com",
      "subject": "Hello",
      "bodyPreview": "This is a preview...",
      "isRead": false,
      "isStarred": false,
      "receivedAt": "2026-01-16T10:00:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 100
}
```

### GET /api/emails/{id}

获取单封邮件详情。

**Response 200**:
```json
{
  "id": "uuid",
  "from": "sender@example.com",
  "to": "user@example.com",
  "subject": "Hello",
  "textBody": "Plain text content",
  "htmlBody": "<p>HTML content</p>",
  "bodyPreview": "Plain text content...",
  "isRead": true,
  "isStarred": false,
  "isArchived": false,
  "isTrashed": false,
  "labels": ["work", "important"],
  "receivedAt": "2026-01-16T10:00:00Z"
}
```

**Error 404**: 邮件不存在

### PATCH /api/emails/{id}

更新邮件状态。

**Request Body**:
```json
{
  "isRead": true,
  "isStarred": true,
  "isArchived": false,
  "isTrashed": false,
  "labels": ["work"]
}
```

**Response 200**: 返回更新后的邮件对象

### DELETE /api/emails/{id}

永久删除邮件。

**Response 204**: 删除成功

**Error 404**: 邮件不存在

---

## Batch Operations

### PATCH /api/emails/batch

批量更新邮件状态。

**Request Body**:
```json
{
  "ids": ["uuid1", "uuid2"],
  "update": {
    "isRead": true
  }
}
```

**Response 200**:
```json
{
  "updated": 2
}
```

### DELETE /api/emails/batch

批量删除邮件。

**Request Body**:
```json
{
  "ids": ["uuid1", "uuid2"]
}
```

**Response 200**:
```json
{
  "deleted": 2
}
```

### DELETE /api/mailboxes/{address}/trash

清空指定邮箱的垃圾箱。

**Response 200**:
```json
{
  "deleted": 5
}
```

---

## Error Responses

所有错误响应使用统一格式：

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Email not found"
  }
}
```

### 错误码

| Code | Status | Description |
|------|--------|-------------|
| UNAUTHORIZED | 401 | 未认证 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| VALIDATION_ERROR | 400 | 请求参数错误 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

