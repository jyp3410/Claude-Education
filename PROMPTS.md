# 쇼핑 리스트 앱 개발 단계별 프롬프트

> 각 단계의 프롬프트를 순서대로 복사해 Claude Code에 붙여넣어 사용하세요.
> 한 단계가 끝나면 로컬에서 `streamlit run app.py`로 직접 확인한 뒤 다음 단계로 넘어가는 것을 권장합니다.

---

## 1단계: 기본 뼈대 작성

```
PRD.md를 읽고 쇼핑 리스트 앱의 기본 뼈대를 만들어줘.

[범위]
- PRD 6.1의 프로젝트 구조대로 파일 생성: app.py, storage.py, requirements.txt, .gitignore, README.md
- data/ 폴더는 실행 시 자동 생성되도록 하고, data/shopping_list.json은 .gitignore에 추가

[storage.py]
- PRD 4장 데이터 모델(id, name, quantity, checked, created_at) 기준
- load_items() -> list[dict]: 파일이 없거나 JSON이 손상되면 빈 리스트 반환 (예외로 앱이 죽으면 안 됨)
- save_items(items): 임시 파일에 쓴 뒤 os.replace로 교체하는 atomic write
- 한글이 깨지지 않도록 ensure_ascii=False, encoding="utf-8"

[app.py]
- st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")
- 타이틀 "🛒 쇼핑 리스트"
- st.session_state["items"]가 없을 때만 load_items()로 초기화
- st.session_state["editing_id"] = None 초기화
- 아직 기능은 넣지 말고, 현재 items를 단순 텍스트로 출력하는 자리만 만들어 둘 것

[requirements.txt]
- streamlit (버전 하한 명시, 예: streamlit>=1.40)

[README.md]
- 로컬 실행 방법 (가상환경 생성, pip install, streamlit run app.py)
- PRD 8장의 "Streamlit Cloud에서는 데이터가 초기화될 수 있음" 주의사항

[완료 조건]
- 가상환경을 만들고 패키지를 설치한 뒤 `streamlit run app.py --server.headless true`로 실행해 에러 없이 뜨는지 확인
- storage.py의 load/save를 간단한 파이썬 스크립트로 검증 (정상 저장, 파일 없음, 손상된 JSON 3가지 경우)
- 만든 파일 목록과 검증 결과를 요약해줘
```

---

## 2단계: 주요 기능 추가

```
PRD.md의 3장 기능 요구사항 중 P0, P1 기능(F-01 ~ F-08)을 app.py에 구현해줘.
F-09(필터)는 P2이므로 이번에는 구현하지 마.

[구현 항목]
- F-01 추가: st.form + clear_on_submit=True, 이름(text_input, max_chars=50) + 수량(number_input, 1~999, 기본 1)
  - 공백만 있는 이름은 추가하지 않고 st.warning
  - 같은 이름이 이미 있으면 추가는 하되 st.info로 중복 안내
- F-02 조회: 미완료 → 완료 순, 각 그룹 안에서는 created_at 순 정렬
  - 빈 리스트면 "쇼핑 리스트가 비어 있어요. 아이템을 추가해 보세요!" 표시
- F-03 체크: st.checkbox + on_change 콜백, 변경 즉시 저장
- F-04 수정: 수정 버튼 → 해당 행만 편집 모드(이름/수량 입력 + 저장/취소)
  - editing_id로 한 번에 하나만 편집, 저장 시 F-01과 같은 유효성 검사
- F-05 삭제: 삭제 버튼 → 즉시 삭제 후 st.toast("'{이름}'를 삭제했어요")
- F-06 저장: 상태가 바뀌는 모든 콜백에서 save_items 호출
- F-07 진행률: st.progress + "N개 중 M개 완료", 전부 완료 시 "장보기 완료! 🎉"
- F-08 완료 항목 일괄 삭제: 완료 아이템이 0개면 버튼 disabled

[구현 규칙 - 중요]
- 모든 행 위젯의 key는 아이템 id 기반 (f"check_{id}", f"edit_{id}", f"del_{id}" 등). 리스트 인덱스 사용 금지
- 상태 변경은 on_click / on_change 콜백에서 처리하고, 본문에서 st.rerun()을 남발하지 말 것
- 상태 변경 로직(add_item, update_item, delete_item, toggle_item, clear_checked)은 함수로 분리해 UI 코드와 섞이지 않게 할 것
- 디자인은 3단계에서 할 예정이니 기본 위젯 위주로 기능 동작에 집중

[완료 조건]
- 앱을 실행해 PRD 10장 수용 기준 중 기능 관련 항목을 직접 하나씩 확인
- 특히 다음 경우를 확인: 중간 아이템 삭제 후 다른 아이템 체크 상태가 유지되는지, 편집 중 다른 아이템 삭제 시 오류가 없는지, 새로고침 후 데이터 유지
- 구현한 기능과 확인 결과를 PRD 기능 ID별 표로 정리해줘
```

---

## 3단계: UI 디자인

```
2단계에서 만든 쇼핑 리스트 앱의 UI를 다듬어줘. 기능 동작은 바꾸지 말고 보기와 사용성만 개선해.

[레이아웃]
- PRD 5장 와이어프레임 구조를 따를 것: 타이틀 → 입력 폼 → 진행률 → 목록 → 완료 항목 삭제 버튼
- 입력 폼은 이름/수량/추가 버튼이 한 줄에 오도록 st.columns 비율 조정 (예: [5, 2, 2])
- 목록 행: [체크박스+이름×수량 | 수정 | 삭제], 버튼은 아이콘(✏️, 🗑️)으로 작게
- 모바일 폭(360px)에서도 행이 세로로 깨지지 않도록 컬럼 비율과 CSS 조정

[스타일]
- 완료 아이템: 취소선 + 회색 글자 (st.markdown의 :gray[~~텍스트~~] 또는 CSS)
- st.markdown(unsafe_allow_html=True)로 최소한의 커스텀 CSS 주입
  - 행 사이 간격 줄이기, 버튼 크기 통일, 아이템 행 hover 시 은은한 배경
- .streamlit/config.toml로 테마 지정 (primaryColor 등). 라이트/다크 모드 모두 글자가 잘 보이는지 확인
- 체크된 항목과 안 된 항목 사이에 얇은 구분선 또는 "완료" 소제목

[사용성]
- 아이템 추가 후 이름 입력창에 계속 입력할 수 있게 유지
- 편집 모드 행은 배경색 등으로 구분되게
- 모든 문구는 한국어, PRD 문구와 일치시킬 것

[완료 조건]
- 데스크톱 폭과 모바일 폭(360px)에서 각각 실행해 레이아웃 확인
- 2단계 기능이 전부 그대로 동작하는지 다시 확인
- 변경한 내용을 요약하고, 커스텀 CSS가 Streamlit 버전 업데이트에 영향받을 수 있는 부분이 있으면 알려줘
```

---

## 4단계: PRD 준수 및 버그 검토 (Playwright 활용)

```
완성된 쇼핑 리스트 앱이 PRD.md대로 개발됐는지, 버그는 없는지 Playwright로 자세하게 검토해줘.
검토 중에는 코드를 고치지 말고, 결과 보고서를 먼저 작성한 뒤 수정 여부를 나에게 물어봐.

[준비]
- data/shopping_list.json을 백업하고 빈 상태에서 시작
- `streamlit run app.py --server.headless true --server.port 8501`를 백그라운드로 실행
- Playwright 브라우저로 http://localhost:8501 접속
- Streamlit은 상호작용마다 재실행되므로, 매 조작 후 화면이 갱신될 때까지 기다린 뒤 확인할 것

[1. PRD 기능 검증] - PRD 3장 F-01 ~ F-08 각각에 대해
- F-01: 정상 추가 / 빈 이름 / 공백만 입력 / 51자 이상 / 수량 0·1000 / 중복 이름 / Enter 키로 추가
- F-02: 정렬 순서(미완료→완료), 빈 리스트 안내 문구
- F-03: 체크 → 취소선 + 아래로 이동, 체크 해제 → 원위치
- F-04: 수정 저장 / 취소 / 빈 이름으로 저장 시도 / 편집 중 다른 행 수정 버튼 클릭
- F-05: 삭제 및 토스트 문구, 첫 번째·중간·마지막 아이템 삭제
- F-06: 새로고침 후 유지, JSON 파일 내용이 화면과 일치하는지 직접 열어서 비교
- F-07: 진행률 숫자·바 정확성, 0개일 때, 전부 완료 시 축하 문구
- F-08: 완료 0개일 때 비활성화, 일괄 삭제 후 미완료 항목 보존

[2. 버그 탐색] - 엣지 케이스
- 중간 아이템 삭제 후 나머지 아이템의 체크 상태·이름이 뒤섞이지 않는지 (위젯 key 문제)
- 편집 중인 아이템을 다른 경로(일괄 삭제)로 삭제했을 때
- 빠르게 연속 클릭(체크 토글 여러 번, 추가 버튼 연타)
- 특수문자·이모지·HTML 태그(<b>test</b>, <script>) 입력 시 화면 깨짐이나 HTML 주입 여부
- 아이템 50~100개 추가 시 동작 속도 (PRD 7장: 1초 이내)
- JSON 파일을 일부러 손상시킨 뒤 새로고침 → 앱이 죽지 않는지
- 브라우저 콘솔 에러와 Streamlit 서버 로그 에러 확인

[3. UI/반응형 검증]
- 데스크톱(1280px)과 모바일(375px, 360px) 크기로 각각 스크린샷
- 다크 모드(emulate media)에서 글자 가독성
- PRD 5장 와이어프레임과의 차이

[4. 코드 리뷰]
- app.py, storage.py를 읽고 PRD 6.2(상태 관리, id 기반 key, 콜백, atomic write) 준수 여부
- 예외 처리 누락, 중복 코드, 불필요한 st.rerun() 사용

[보고서] REVIEW.md로 작성
- 요약: 전체 통과율, 심각한 문제 개수
- PRD 10장 수용 기준 체크리스트 (통과 ✅ / 실패 ❌ / 부분 ⚠️ + 근거)
- 버그 목록 표: ID, 심각도(Critical/High/Medium/Low), 재현 절차, 기대 결과, 실제 결과, 스크린샷 경로, 원인 추정 위치(파일:줄)
- PRD 대비 누락·초과 구현 사항
- 개선 제안 (우선순위 순)
- 스크린샷은 screenshots/ 폴더에 저장

[마무리]
- 검토가 끝나면 백업한 data/shopping_list.json을 복원하고 실행한 streamlit 서버 종료
- 보고서 요약을 보여주고, 어떤 버그부터 고칠지 나에게 물어봐
```

---

## (선택) 5단계: 버그 수정 및 배포

```
REVIEW.md에서 Critical, High 버그를 먼저 수정하고, 수정한 항목마다 Playwright로 재현 절차를 다시 실행해 해결됐는지 확인해줘.
그다음 PRD 6.3 순서대로 GitHub 저장소 생성과 Streamlit Community Cloud 배포를 안내해줘.
(push 같은 외부 작업은 실행 전에 나에게 먼저 확인받을 것)
```
