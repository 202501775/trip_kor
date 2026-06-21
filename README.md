# 같이가자 - 국내 여행 플래너

지역, 날짜, 인원, 예산과 취향을 입력하면 날짜별 일정, 맛집, 지도, 숙소 검색 링크와 예상 비용을 생성하는 Streamlit 앱입니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

API 키가 없어도 서울, 부산, 강릉, 제주 샘플 데이터로 실행됩니다.

## 카카오 장소 검색 연결

1. [Kakao Developers](https://developers.kakao.com/)에서 애플리케이션을 만듭니다.
2. 앱 키의 `REST API 키`를 확인합니다.
3. `.streamlit/secrets.toml.example`을 참고하여 `.streamlit/secrets.toml`을 만듭니다.

```toml
KAKAO_REST_API_KEY = "발급받은-키"
```

## Streamlit Community Cloud 배포

1. 이 폴더를 GitHub 저장소에 올립니다.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에서 저장소와 `app.py`를 선택합니다.
3. 앱 설정의 Secrets에 아래 내용을 등록합니다.

```toml
KAKAO_REST_API_KEY = "발급받은-키"
```

4. Deploy를 누르면 공개 URL이 생성됩니다.

## 현재 범위

- 카카오 키워드 검색을 이용한 관광지·식당 후보 수집
- 장소 간 직선거리를 이용한 날짜별 동선 구성
- 인원·여행 기간·소비 성향에 따른 예상 예산
- 일정 CSV 내려받기와 지도 표시
- 네이버·카카오맵·숙박 플랫폼 검색 연결

식당 영업시간과 숙소 실시간 가격은 각 예약·지도 서비스에서 최종 확인해야 합니다.
