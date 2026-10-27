# 🛒 쇼핑 리스트

아이템 추가, 수정, 삭제, 체크 기능이 있는 가벼운 쇼핑 리스트 웹 앱입니다. Python + Streamlit으로 만들었습니다.
자세한 요구사항은 [PRD.md](PRD.md)를 참고하세요.

## 로컬 실행

```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 실행
streamlit run app.py
```

브라우저에서 http://localhost:8501 로 접속합니다.
데이터는 `data/shopping_list.json`에 저장되며, 처음 저장할 때 자동으로 만들어집니다.

## 주의사항

- **Streamlit Community Cloud에 배포하면 데이터가 초기화될 수 있습니다.** Cloud의 파일 시스템은 임시 저장소라 앱이 재시작·재배포되거나 오래 사용하지 않아 잠들면 저장된 리스트가 사라질 수 있습니다.
- 로그인 기능이 없어 **URL을 아는 사람은 모두 같은 리스트를 보고 수정**할 수 있습니다. 개인용으로 URL을 공유하지 않고 사용하세요.
