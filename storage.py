"""쇼핑 리스트 데이터를 JSON 파일로 불러오고 저장한다."""

import json
import os
import tempfile
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "shopping_list.json"

MAX_NAME_LEN = 50
MIN_QTY, MAX_QTY = 1, 999


def load_items(path: Path = DATA_FILE) -> list[dict]:
    """저장된 아이템 목록을 반환한다. 파일이 없거나 손상되면 빈 리스트를 반환한다."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []

    if not isinstance(data, dict):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    return _normalize(items)


def _normalize(items: list) -> list[dict]:
    """화면에서 오류를 낼 수 있는 값을 정리한다.

    타입이 틀리거나 이름이 비었거나 id가 중복된 아이템은 제외하고(위젯 key 중복 방지),
    이름 길이와 수량은 입력 위젯이 허용하는 범위로 맞춘다.
    """
    seen_ids = set()
    result = []
    for item in items:
        if not _is_valid_item(item) or item["id"] in seen_ids:
            continue
        name = item["name"].strip()[:MAX_NAME_LEN]
        if not name:
            continue
        seen_ids.add(item["id"])
        result.append({**item, "name": name, "quantity": min(max(item["quantity"], MIN_QTY), MAX_QTY)})
    return result


def _is_valid_item(item) -> bool:
    """필드가 빠지거나 타입이 틀린 아이템을 걸러낸다."""
    return (
        isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("name"), str)
        and isinstance(item.get("quantity"), int)
        and not isinstance(item.get("quantity"), bool)
        and isinstance(item.get("checked"), bool)
        and isinstance(item.get("created_at"), str)
    )


def save_items(items: list[dict], path: Path = DATA_FILE) -> None:
    """임시 파일에 쓴 뒤 교체하는 방식으로 저장해 쓰기 도중 파일이 손상되지 않게 한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"items": items}, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
