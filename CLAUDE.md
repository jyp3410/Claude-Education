# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

A lightweight shopping list web app (add / edit / delete / check items) built with Python + Streamlit and deployed to Streamlit Community Cloud. Stages 1–4 are done (F-01~F-08 + UI + Playwright review), and the High/Medium bugs in `REVIEW.md` (BUG-01~04) are fixed; Low bugs BUG-05~11 remain open. The file is the source of truth, not session state: `_reload()` re-reads `data/shopping_list.json` on every run and at the start of every mutating callback, so a stale tab never saves its old list over newer changes. Keep that pattern for any new mutation. Checkbox state is pushed into `st.session_state[f"check_{id}"]` before rendering (no `value=`), so changes from other tabs show up. `storage._normalize()` clamps loaded values to what the widgets accept; range constants live in `storage.py`. Any user text that goes into markdown (labels, `st.info`, `st.toast`) must go through `_escape_md`, which also breaks URL/email autolinks with U+2060. Styling lives in the `CUSTOM_CSS` string in `app.py`; it targets only `data-testid` attributes and `st-key-*` classes (from `st.container(key=...)`: `row_{id}`, `editrow_{id}`, `item_list`), never emotion hash classes. Rows use `st.columns(..., wrap=False)` plus a CSS `min-width: 0` override so they stay on one line at 360px. Theme colors are set under `[theme.light]` / `[theme.dark]` in `.streamlit/config.toml`; a bare `[theme]` section would disable system dark mode. Row edit/delete buttons are emoji-only, so tests should locate them by position within the `st-key-row_*` container. Callback messages are queued in `st.session_state["flash"]` and rendered under the add form; item names are markdown-escaped (`_escape_md`) before going into widget labels. Planning documents:

- `PRD.md` — the source of truth for requirements. Feature IDs (F-01 ~ F-09), priorities (P0/P1/P2), data model, wireframe, risks, and acceptance criteria (section 10). Reference feature IDs when implementing or reporting.
- `PROMPTS.md` — the staged development plan: 1) skeleton, 2) core features F-01~F-08 (F-09 filter is P2, deferred), 3) UI design, 4) Playwright review producing `REVIEW.md` + `screenshots/`, 5) optional fix & deploy. Follow the scope of the current stage; don't pull later-stage work forward.

UI text is Korean.

## Commands

A virtualenv exists at `.venv/` (Python 3.12, Streamlit 1.66). On Windows use `.venv/Scripts/python -m streamlit ...`.

```bash
pip install -r requirements.txt
streamlit run app.py                                         # local dev
streamlit run app.py --server.headless true --server.port 8501   # headless (for Playwright review)
```

No test framework or linter is defined in the PRD; verification is done by running the app and, in stage 4, driving it with Playwright at http://localhost:8501.

## Planned architecture (PRD section 6)

- `app.py` — Streamlit UI. State lives in `st.session_state["items"]` (loaded once from storage) and `st.session_state["editing_id"]` (only one item editable at a time).
- `storage.py` — `load_items()` / `save_items(items)` against `data/shopping_list.json`. Load must return `[]` on missing or corrupt files rather than crash; save uses an atomic write (temp file + `os.replace`) with `ensure_ascii=False`, UTF-8.
- `data/shopping_list.json` is git-ignored and created at runtime.

Item schema: `id` (UUID4), `name` (1–50 chars), `quantity` (int 1–999, default 1), `checked` (bool), `created_at` (ISO 8601). List order: unchecked first, then checked, each by `created_at`.

### Streamlit rules that matter here

- Every per-row widget key must be derived from the item `id` (`check_{id}`, `edit_{id}`, `del_{id}`), never the list index — index keys cause state to shift onto the wrong row after deletion.
- Mutate state in `on_click` / `on_change` callbacks and call `save_items` there; avoid `st.rerun()` in the script body.
- Keep mutation logic (`add_item`, `update_item`, `delete_item`, `toggle_item`, `clear_checked`) as plain functions separate from UI code.

## Known constraints (accepted for MVP)

- Streamlit Cloud's filesystem is ephemeral: the JSON file is wiped on restart, redeploy, or sleep. Persistent storage (Google Sheets / Supabase) is a v2 item.
- No auth: everyone with the URL shares one list; concurrent edits are last-write-wins.
