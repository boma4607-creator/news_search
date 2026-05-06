# 📰 AI 뉴스 검색 앱

> Naver + Google 뉴스 비교 · Groq AI 요약 · PostgreSQL 클라우드 저장

🌐 **사이트**: https://newssearch-j2njeoappxhlzgdtrah3wwr.streamlit.app/
💻 **GitHub**: https://github.com/your-id/news-search

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 📡 **네이버 뉴스** | Naver API로 최신 뉴스 검색 |
| 🌐 **구글 뉴스** | Google RSS로 뉴스 검색 (API 불필요) |
| 🤖 **AI 비교 요약** | Groq Llama3로 두 소스 비교 분석 |
| 💾 **DB 저장** | PostgreSQL에 검색 결과 저장 |
| 🗄️ **저장 조회** | 저장된 뉴스 통계 및 테이블 조회 |

---

## 🗄️ 데이터베이스 구조 (PostgreSQL - Supabase)

### 테이블: `naver_news`
```sql
CREATE TABLE naver_news (
    id          SERIAL PRIMARY KEY,
    query       TEXT,        -- 검색어
    title       TEXT,        -- 기사 제목
    link        TEXT,        -- 기사 URL
    description TEXT,        -- 기사 요약
    pub_date    TEXT,        -- 발행일
    saved_at    TIMESTAMP DEFAULT NOW()
);
```

---

## ⚙️ 코드 구조

```
app.py
 ├── CSS 스타일       → 다크 그라디언트 UI
 ├── 사이드바         → API 키 / 검색 설정
 ├── init_db()        → DB 테이블 자동 생성
 ├── search_naver()   → Naver API 호출
 ├── search_google()  → Google RSS 파싱
 ├── save_to_db()     → DB 저장
 ├── llm_compare()    → Groq AI 비교 분석
 ├── load_saved()     → DB 조회
 └── 탭 UI
      ├── 탭1: 네이버 뉴스
      ├── 탭2: 구글 뉴스
      ├── 탭3: AI 비교 요약
      └── 탭4: 저장 내역
```

---

## 🔑 API 키 발급

| API | 사이트 | 비용 |
|-----|--------|------|
| Naver | https://developers.naver.com | 무료 |
| Groq  | https://console.groq.com | 무료 |
| Supabase | https://supabase.com | 무료 |

---

## 🚀 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Secrets 설정
```toml
NAVER_CLIENT_ID     = "..."
NAVER_CLIENT_SECRET = "..."
GROQ_API_KEY        = "gsk_..."
DATABASE_URL        = "postgresql://..."
```

> ⚠️ secrets.toml은 GitHub에 절대 올리지 마세요!
