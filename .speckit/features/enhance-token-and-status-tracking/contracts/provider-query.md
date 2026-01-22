# API Contracts: Provider Query

**Modules**:
- `src/auth/crs/client.py`
- `src/auth/cpa/client.py`
- `src/auth/s2a/client.py`

## 1. CRS Query

```python
def crs_query_account(email: str) -> dict:
    """查询 CRS 入库状态

    Args:
        email: 账号邮箱

    Returns:
        {
            "exists": bool,
            "account_id": str | None,
            "account_data": dict | None
        }
    """
```

## 2. CPA Query

```python
def cpa_query_account(email: str) -> dict:
    """查询 CPA 入库状态

    Args:
        email: 账号邮箱

    Returns:
        {
            "exists": bool,
            "account_id": str | None,
            "account_data": dict | None
        }
    """
```

## 3. S2A Query

```python
def s2a_query_account(email: str) -> dict:
    """查询 S2A 入库状态

    Args:
        email: 账号邮箱

    Returns:
        {
            "exists": bool,
            "account_id": str | None,
            "account_data": dict | None
        }
    """
```
