# API Contracts: Storage Manager

**Module**: `src/core/storage_manager.py`

## 1. init_storage_status

初始化 storage_status 结构。

```python
def init_storage_status() -> dict:
    """初始化入库状态结构

    Returns:
        {
            "crs": {"status": "not_stored"},
            "cpa": {"status": "not_stored"},
            "s2a": {"status": "not_stored"}
        }
    """
```

## 2. check_account_stored

查询账号在指定服务商中的入库状态。

```python
def check_account_stored(
    email: str,
    provider: str
) -> dict:
    """查询入库状态

    Args:
        email: 账号邮箱
        provider: 服务商 (crs/cpa/s2a)

    Returns:
        {
            "exists": bool,
            "account_id": str | None,
            "last_check": str (datetime)
        }
    """
```

## 3. update_storage_status

更新 team_tracker.json 中的入库状态。

```python
def update_storage_status(
    tracker: dict,
    team_name: str,
    email: str,
    provider: str,
    status_data: dict
) -> None:
    """更新入库状态

    Args:
        tracker: tracker 数据
        team_name: team 名称
        email: 账号邮箱
        provider: 服务商
        status_data: 状态数据
    """
```

## 4. get_enabled_providers

获取已启用的服务商列表。

```python
def get_enabled_providers() -> list[str]:
    """获取已启用的服务商

    Returns:
        ["crs", "cpa", "s2a"] 的子集
    """
```
