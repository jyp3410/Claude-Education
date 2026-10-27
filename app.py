import uuid
from datetime import datetime

import streamlit as st

from storage import MAX_NAME_LEN, MAX_QTY, MIN_QTY, load_items, save_items

MD_SPECIAL_CHARS = "\\`*_{}[]()#+-.!|~<>:$"
AUTOLINK_BREAKERS = (("://", ":⁠//"), ("www.", "www⁠."), ("@", "@⁠"))

st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")

if "editing_id" not in st.session_state:
    st.session_state["editing_id"] = None
if "flash" not in st.session_state:
    st.session_state["flash"] = []


# ---------- 상태 변경 로직 (모두 위젯 콜백에서 호출) ----------

def _reload() -> None:
    """파일을 기준으로 목록을 다시 읽는다.

    세션이 들고 있던 목록을 그대로 저장하면 다른 탭에서 바꾼 내용을 덮어쓰므로,
    변경 직전과 매 렌더링마다 파일에서 최신 목록을 읽은 뒤 id로 찾아 바꾼다.
    """
    st.session_state["items"] = load_items()


def _persist() -> None:
    save_items(st.session_state["items"])


def _escape_md(text: str) -> str:
    """사용자 입력이 마크다운/LaTeX로 해석되지 않도록 특수문자를 이스케이프한다.

    URL·이메일 자동 링크는 백슬래시 이스케이프로 막히지 않으므로
    보이지 않는 문자(U+2060 WORD JOINER)를 끼워 패턴을 깬다.
    """
    for pattern, broken in AUTOLINK_BREAKERS:
        text = text.replace(pattern, broken)
    return "".join("\\" + c if c in MD_SPECIAL_CHARS else c for c in text)


def _flash(kind: str, message: str) -> None:
    """콜백 안에서 만든 메시지를 다음 렌더링 때 폼 아래에 보여준다."""
    st.session_state["flash"].append((kind, message))


def _find(item_id: str) -> dict | None:
    return next((i for i in st.session_state["items"] if i["id"] == item_id), None)


def _clean_name(raw: str) -> str | None:
    name = (raw or "").strip()
    if not name:
        _flash("warning", "아이템 이름을 입력해 주세요.")
        return None
    return name[:MAX_NAME_LEN]


def _warn_if_duplicate(name: str, exclude_id: str | None = None) -> None:
    if any(
        i["name"].casefold() == name.casefold() and i["id"] != exclude_id
        for i in st.session_state["items"]
    ):
        _flash("info", f"'{_escape_md(name)}'은(는) 이미 리스트에 있어요.")


def add_item() -> None:
    name = _clean_name(st.session_state["new_name"])
    if name is None:
        return
    _reload()
    _warn_if_duplicate(name)
    st.session_state["items"].append(
        {
            "id": str(uuid.uuid4()),
            "name": name,
            "quantity": int(st.session_state["new_qty"]),
            "checked": False,
            "created_at": datetime.now().isoformat(),
        }
    )
    _persist()


def toggle_item(item_id: str) -> None:
    _reload()
    item = _find(item_id)
    if item is None:
        return
    item["checked"] = st.session_state[f"check_{item_id}"]
    _persist()


def start_edit(item_id: str) -> None:
    st.session_state["editing_id"] = item_id


def cancel_edit() -> None:
    st.session_state["editing_id"] = None


def update_item(item_id: str) -> None:
    _reload()
    item = _find(item_id)
    if item is None:
        st.session_state["editing_id"] = None
        return
    name = _clean_name(st.session_state[f"edit_name_{item_id}"])
    if name is None:
        return  # 편집 모드 유지
    _warn_if_duplicate(name, exclude_id=item_id)
    item["name"] = name
    item["quantity"] = int(st.session_state[f"edit_qty_{item_id}"])
    st.session_state["editing_id"] = None
    _persist()


def delete_item(item_id: str) -> None:
    _reload()
    item = _find(item_id)
    if item is None:
        return
    st.session_state["items"].remove(item)
    if st.session_state["editing_id"] == item_id:
        st.session_state["editing_id"] = None
    _persist()
    st.toast(f"'{_escape_md(item['name'])}'를 삭제했어요")


def clear_checked() -> None:
    _reload()
    items = st.session_state["items"]
    removed = [i for i in items if i["checked"]]
    if not removed:
        return
    st.session_state["items"] = [i for i in items if not i["checked"]]
    if any(i["id"] == st.session_state["editing_id"] for i in removed):
        st.session_state["editing_id"] = None
    _persist()
    st.toast(f"완료 항목 {len(removed)}개를 삭제했어요")


# ---------- UI ----------

def render_item(item: dict) -> None:
    item_id = item["id"]

    if st.session_state["editing_id"] == item_id:
        with st.container(key=f"editrow_{item_id}"):
            # 모바일에서는 이름 입력 한 줄, 수량·저장·취소 한 줄로 나눠 입력칸이 너무 좁아지지 않게 한다
            st.text_input(
                "이름", value=item["name"], max_chars=MAX_NAME_LEN,
                key=f"edit_name_{item_id}", label_visibility="collapsed",
            )
            qty_col, save_col, cancel_col = st.columns([2, 1, 1], vertical_alignment="center", wrap=False)
            qty_col.number_input(
                "수량", min_value=MIN_QTY, max_value=MAX_QTY, value=item["quantity"], step=1,
                key=f"edit_qty_{item_id}", label_visibility="collapsed",
            )
            save_col.button(
                "저장", key=f"save_{item_id}", on_click=update_item, args=(item_id,),
                type="primary", width="stretch",
            )
            cancel_col.button("취소", key=f"cancel_{item_id}", on_click=cancel_edit, width="stretch")
        return

    label = f"{_escape_md(item['name'])} × {item['quantity']}"
    if item["checked"]:
        label = f":gray[~~{label}~~]"

    with st.container(key=f"row_{item_id}"):
        check_col, edit_col, del_col = st.columns(
            [12, 1, 1], gap="small", vertical_alignment="center", wrap=False
        )
        # 위젯이 이전 실행의 값을 기억하므로, 다른 탭에서 바뀐 체크 상태가 보이도록 파일 값으로 맞춘다
        st.session_state[f"check_{item_id}"] = item["checked"]
        check_col.checkbox(
            label, key=f"check_{item_id}", on_change=toggle_item, args=(item_id,),
        )
        edit_col.button(
            "✏️", key=f"edit_{item_id}", on_click=start_edit, args=(item_id,),
            type="tertiary", help="수정",
        )
        del_col.button(
            "🗑️", key=f"del_{item_id}", on_click=delete_item, args=(item_id,),
            type="tertiary", help="삭제",
        )


# Streamlit 내부 클래스명(emotion 해시)은 버전마다 바뀌므로 data-testid와 st-key-* 클래스만 사용한다.
CUSTOM_CSS = """
<style>
.block-container { padding-top: 2.5rem; }

/* 아이템 행 */
.st-key-item_list { gap: 0.15rem; }
[class*="st-key-row_"] {
    padding: 0.2rem 0.5rem;
    border-radius: 0.5rem;
    transition: background-color 0.15s;
}
[class*="st-key-row_"]:hover { background-color: rgba(128, 128, 128, 0.08); }
[class*="st-key-row_"] [data-testid="stCheckbox"] label { min-height: 2rem; align-items: center; }
/* 긴 이름은 말줄임 대신 줄바꿈 */
[class*="st-key-row_"] [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"],
[class*="st-key-row_"] [data-testid="stCheckbox"] p {
    white-space: normal;
    overflow: visible;
    word-break: break-word;
}
/* wrap=False 컬럼에 Streamlit이 주는 최소 폭(8rem)을 없애 좁은 화면에서도 한 줄에 들어가게 한다 */
[class*="st-key-row_"] [data-testid="stColumn"],
[class*="st-key-editrow_"] [data-testid="stColumn"],
[data-testid="stForm"] [data-testid="stColumn"] { min-width: 0 !important; }
[class*="st-key-row_"] [data-testid="stColumn"]:not(:first-child) { min-width: 2rem !important; }
[class*="st-key-row_"] button { padding: 0.15rem 0.3rem; min-height: 2rem; font-size: 1.05rem; }

/* 편집 중인 행 */
[class*="st-key-editrow_"] {
    padding: 0.6rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(46, 158, 106, 0.45);
    background-color: rgba(46, 158, 106, 0.08);
    gap: 0.5rem;
}

/* "완료" 구분 제목 */
.done-heading {
    margin: 0.75rem 0 0.25rem;
    padding: 0.6rem 0.5rem 0;
    border-top: 1px solid rgba(128, 128, 128, 0.25);
    font-size: 0.85rem;
    opacity: 0.65;
}

/* 좁은 화면에서 입력 폼 수량 칸의 +/- 버튼을 숨겨 입력칸 폭을 확보한다 */
@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    h1 { font-size: 1.75rem !important; }
    [data-testid="stForm"] [data-testid="stNumberInputStepDown"],
    [data-testid="stForm"] [data-testid="stNumberInputStepUp"] { display: none; }
    [data-testid="stForm"] button { padding-left: 0.4rem; padding-right: 0.4rem; white-space: nowrap; }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.title("🛒 쇼핑 리스트")

# F-01 아이템 추가
with st.form("add_form", clear_on_submit=True):
    name_col, qty_col, btn_col = st.columns([4, 1.6, 1.6], vertical_alignment="bottom", wrap=False)
    name_col.text_input("아이템 이름", max_chars=MAX_NAME_LEN, key="new_name", placeholder="예: 우유")
    qty_col.number_input("수량", min_value=MIN_QTY, max_value=MAX_QTY, value=1, step=1, key="new_qty")
    btn_col.form_submit_button("추가", on_click=add_item, type="primary", width="stretch")

for kind, message in st.session_state["flash"]:
    getattr(st, kind)(message)
st.session_state["flash"] = []

_reload()
items = st.session_state["items"]
if st.session_state["editing_id"] not in {i["id"] for i in items}:
    st.session_state["editing_id"] = None  # 다른 탭에서 삭제된 경우
total = len(items)
done = sum(i["checked"] for i in items)

if total == 0:
    st.info("쇼핑 리스트가 비어 있어요. 아이템을 추가해 보세요!", icon="📝")
else:
    # F-07 진행률
    st.progress(done / total, text=f"{total}개 중 {done}개 완료")
    if done == total:
        st.success("장보기 완료! 🎉")

    # F-02 목록: 미완료 → 완료, 각 그룹은 추가한 순서
    ordered = sorted(items, key=lambda i: (i["checked"], i["created_at"]))
    with st.container(key="item_list"):
        for item in ordered:
            if item["checked"] and item is ordered[total - done]:
                st.markdown(f'<div class="done-heading">완료 {done}</div>', unsafe_allow_html=True)
            render_item(item)

    # F-08 완료 항목 일괄 삭제
    _, clear_col = st.columns([3, 2])
    clear_col.button("완료 항목 삭제", on_click=clear_checked, disabled=done == 0, width="stretch")
