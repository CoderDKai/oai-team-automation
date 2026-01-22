# API Contracts: Token Manager

**Module**: `src/auth/token_manager.py`

## 1. extract_tokens_from_response

从 OAuth 响应中提取 token 信息。

```python
def extract_tokens_from_response(response: dict) -> dict:
    """从 OAuth 响应中提取 token 信息

    Args:
        response: OAuth 授权响应数据

    Returns:
        {
            "access_token": str,
            "refresh_token": str | None,
            "token_expires_at": int,
            "id_token": str | None
        }
    """
```

## 2. refresh_access_token

使用 refresh_token 刷新 access_token。

```python
def refresh_access_token(
    refresh_token: str,
    provider: str = "openai"
) -> dict | None:
    """刷新 access_token

    Args:
        refresh_token: 刷新令牌
        provider: 服务提供商 (openai)

    Returns:
        {
            "access_token": str,
            "refresh_token": str,
            "token_expires_at": int
        } | None
    """
```

## 3. is_token_expired

检查 token 是否已过期或即将过期。

```python
def is_token_expired(
    expires_at: int,
    buffer_seconds: int = 3600
) -> bool:
    """检查 token 是否过期

    Args:
        expires_at: 过期时间戳
        buffer_seconds: 提前刷新缓冲时间（默认1小时）

    Returns:
        bool: 是否需要刷新
    """
```

## 4. update_team_tokens

更新 team.json 中的 token 信息。

```python
def update_team_tokens(
    team_index: int,
    tokens: dict
) -> bool:
    """更新 team.json 中的 token

    Args:
        team_index: team 索引
        tokens: token 信息

    Returns:
        bool: 是否更新成功
    """
```
