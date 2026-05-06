# 📰 AI 뉴스 검색 앱

> Naver 뉴스 API + GPT 요약 + PostgreSQL 클라우드 저장소를 결합한 Streamlit 웹 앱

🌐 **사이트**: https://your-app.streamlit.app  
💻 **GitHub**: https://github.com/your-id/news-search

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 **네이버 뉴스 검색** | Naver API로 최신 뉴스 실시간 검색 |
| 🤖 **GPT AI 요약** | gpt-4o-mini로 기사 자동 요약 |
| 💾 **클라우드 저장** | PostgreSQL DB에 검색 결과 저장 |
| 🗄️ **저장 내역 조회** | 저장된 뉴스 통계 및 테이블 조회 |

---

## 🗄️ 데이터베이스 구조 (PostgreSQL)

### 테이블 1: `search_history` — 검색 이력
```sql
CREATE TABLE search_history (
    id         SERIAL PRIMARY KEY,
    query      TEXT,           -- 검색어
    result     TEXT,           -- LLM 응답
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 테이블 2: `naver_news` — 네이버 뉴스 저장 (신규)
```sql
CREATE TABLE naver_news (
    id          SERIAL PRIMARY KEY,
    query       TEXT,           -- 검색어
    title       TEXT,           -- 기사 제목
    link        TEXT,           -- 기사 URL
    description TEXT,           -- 기사 요약
    pub_date    TEXT,           -- 발행일
    saved_at    TIMESTAMP DEFAULT NOW()
);
```

---

## ⚙️ 코드 구조 설명

```
app.py
 ├── 커스텀 CSS         → 다크 그라디언트 UI 스타일
 ├── 사이드바           → API 키 입력 / 검색 설정
 ├── init_db()          → DB 테이블 자동 생성
 ├── search_naver()     → Naver API 호출
 ├── save_to_db()       → 검색 결과 DB 저장
 ├── llm_summary()      → OpenAI GPT 요약
 ├── load_saved_news()  → DB에서 뉴스 조회
 └── 탭 UI
      ├── 탭1: 뉴스 검색 결과 카드
      ├── 탭2: AI 요약 결과
      └── 탭3: 저장 통계 + 테이블
```

### 핵심 함수 설명

**`search_naver(query, n)`**  
Naver 검색 API에 GET 요청 → 최신순으로 n개 뉴스 반환

**`save_to_db(query, items)`**  
HTML 태그 제거 후 `naver_news` 테이블에 INSERT

**`llm_summary(query, items)`**  
기사 제목+내용을 GPT에게 전달 → 핵심 요약 + 불렛포인트 반환

**`load_stats()`**  
총 저장 수, 검색어 종류, 인기 검색어 통계 반환

---

## 🚀 실행 방법

### 1. 로컬 실행
```bash
git clone https://github.com/your-id/news-search.git
cd news-search
pip install -r requirements.txt
streamlit run app.py
```

### 2. secrets 설정 (`.streamlit/secrets.toml`)
```toml
NAVER_CLIENT_ID     = "your_naver_client_id"
NAVER_CLIENT_SECRET = "your_naver_client_secret"
OPENAI_API_KEY      = "sk-..."
DATABASE_URL        = "postgresql://user:pass@host:5432/dbname"
```

### 3. Streamlit Cloud 배포
1. GitHub에 push
2. [share.streamlit.io](https://share.streamlit.io) 접속
3. 레포지토리 연결
4. Settings → Secrets에 위 내용 입력
5. Deploy!

---

## 🔑 API 키 발급 방법

### Naver API
1. https://developers.naver.com 접속
2. 로그인 → Application → 애플리케이션 등록
3. 검색 체크 → 등록 → Client ID / Secret 복사

### OpenAI API
1. https://platform.openai.com 접속
2. API Keys → Create new secret key

### Supabase (PostgreSQL)
1. https://supabase.com 접속
2. New Project 생성
3. Settings → Database → Connection string (URI) 복사

---

## 📁 파일 구조
```
news-search/
├── app.py              # 메인 앱
├── requirements.txt    # 패키지 목록
├── README.md           # 설명서
└── .streamlit/
    └── secrets.toml    # API 키 (⚠️ .gitignore에 추가!)
```

> ⚠️ `secrets.toml`은 절대 GitHub에 올리지 마세요!  
> `.gitignore`에 `.streamlit/secrets.toml` 추가 필수!
