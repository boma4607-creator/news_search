import streamlit as st
import requests
import psycopg2
import openai
import pandas as pd
import html
from datetime import datetime

# ══════════════════════════════════════════════
#  페이지 설정
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="📰 뉴스 검색 AI",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
#  커스텀 CSS (스타일)
# ══════════════════════════════════════════════
st.markdown("""
<style>
    /* 배경 */
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.05);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* 제목 */
    h1, h2, h3 { color: #ffffff !important; }

    /* 카드 스타일 */
    .news-card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    .news-card:hover {
        background: rgba(255,255,255,0.13);
        border-color: #7c3aed;
        transform: translateY(-2px);
    }
    .news-title {
        font-size: 17px;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 8px;
    }
    .news-desc {
        font-size: 14px;
        color: #94a3b8;
        line-height: 1.6;
    }
    .news-meta {
        font-size: 12px;
        color: #64748b;
        margin-top: 10px;
    }
    .news-link {
        color: #7c3aed;
        text-decoration: none;
        font-weight: 600;
    }

    /* 배지 */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-naver { background: #03c75a; color: white; }
    .badge-ai    { background: #7c3aed; color: white; }

    /* 입력창 */
    .stTextInput input {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        font-size: 16px !important;
    }

    /* 버튼 */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.3s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(124,58,237,0.4) !important;
    }

    /* 탭 */
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #7c3aed !important;
        border-bottom-color: #7c3aed !important;
    }

    /* 요약 박스 */
    .summary-box {
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.4);
        border-radius: 16px;
        padding: 24px;
        color: #e2e8f0;
        font-size: 15px;
        line-height: 1.8;
    }

    /* 통계 카드 */
    .stat-card {
        background: rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .stat-number { font-size: 36px; font-weight: 800; color: #7c3aed; }
    .stat-label  { font-size: 13px; color: #94a3b8; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  사이드바
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    st.markdown("---")

    # API 키 (secrets 우선, 없으면 직접 입력)
    try:
        naver_id     = st.secrets["NAVER_CLIENT_ID"]
        naver_secret = st.secrets["NAVER_CLIENT_SECRET"]
        openai_key   = st.secrets["OPENAI_API_KEY"]
        db_url       = st.secrets["DATABASE_URL"]
        st.success("✅ API 키 자동 로드됨")
    except Exception:
        st.warning("secrets.toml 없음 → 직접 입력")
        naver_id     = st.text_input("Naver Client ID",     type="password")
        naver_secret = st.text_input("Naver Client Secret", type="password")
        openai_key   = st.text_input("OpenAI API Key",      type="password")
        db_url       = st.text_input("Database URL",        type="password")

    st.markdown("---")
    display_count = st.slider("검색 결과 수", 3, 10, 5)
    st.markdown("---")
    st.markdown("""
    <div style='color:#64748b; font-size:12px; line-height:1.8;'>
    📌 <b style='color:#94a3b8'>사용법</b><br>
    1. 검색어 입력<br>
    2. 뉴스 검색 클릭<br>
    3. DB 저장 클릭<br>
    4. AI 요약 탭 확인<br>
    5. 저장 내역 탭 확인
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  헤더
# ══════════════════════════════════════════════
st.markdown("""
<div style='text-align:center; padding: 30px 0 10px 0;'>
    <h1 style='font-size:48px; font-weight:900; 
               background: linear-gradient(135deg, #7c3aed, #06b6d4);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        📰 AI 뉴스 검색
    </h1>
    <p style='color:#94a3b8; font-size:16px; margin-top:8px;'>
        Naver 뉴스 + GPT 요약 + 클라우드 저장
    </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  DB 초기화
# ══════════════════════════════════════════════
def get_conn():
    return psycopg2.connect(db_url)

def init_db():
    if not db_url:
        return
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS search_history (
                        id SERIAL PRIMARY KEY,
                        query TEXT,
                        result TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS naver_news (
                        id SERIAL PRIMARY KEY,
                        query TEXT,
                        title TEXT,
                        link TEXT,
                        description TEXT,
                        pub_date TEXT,
                        saved_at TIMESTAMP DEFAULT NOW()
                    )
                """)
            conn.commit()
    except Exception as e:
        st.sidebar.error(f"DB 연결 실패: {e}")

init_db()

# ══════════════════════════════════════════════
#  함수들
# ══════════════════════════════════════════════
def clean(text):
    return html.unescape(text.replace("<b>","").replace("</b>",""))

def search_naver(query, n=5):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": naver_id,
        "X-Naver-Client-Secret": naver_secret,
    }
    res = requests.get(url, headers=headers, params={"query": query, "display": n, "sort": "date"})
    res.raise_for_status()
    return res.json().get("items", [])

def save_to_db(query, items):
    with get_conn() as conn:
        with conn.cursor() as cur:
            for item in items:
                cur.execute("""
                    INSERT INTO naver_news (query, title, link, description, pub_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, (query, clean(item["title"]), item.get("link",""),
                      clean(item.get("description","")), item.get("pubDate","")))
        conn.commit()

def llm_summary(query, items):
    openai.api_key = openai_key
    content = "\n\n".join([f"제목: {clean(a['title'])}\n내용: {clean(a.get('description',''))}" for a in items])
    res = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 전문 뉴스 분석가입니다. 주어진 뉴스 기사들을 핵심 위주로 한국어로 요약하고, 주요 포인트를 bullet point로 정리해주세요."},
            {"role": "user",   "content": f"검색어: [{query}]\n\n{content}"},
        ]
    )
    return res.choices[0].message.content

def load_saved_news():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, query, title, description, pub_date, saved_at FROM naver_news ORDER BY saved_at DESC LIMIT 100")
            rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["ID","검색어","제목","내용","발행일","저장시각"])

def load_stats():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM naver_news")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT query) FROM naver_news")
            queries = cur.fetchone()[0]
            cur.execute("SELECT query, COUNT(*) as cnt FROM naver_news GROUP BY query ORDER BY cnt DESC LIMIT 1")
            row = cur.fetchone()
            top_query = row[0] if row else "-"
    return total, queries, top_query

# ══════════════════════════════════════════════
#  검색창
# ══════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input("", placeholder="🔍  검색어를 입력하세요  (예: 인공지능, 주식시장, 날씨)", label_visibility="collapsed")
with col_btn:
    search_clicked = st.button("검색 🔍")

# ══════════════════════════════════════════════
#  탭
# ══════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["  📡 네이버 뉴스  ", "  🤖 AI 요약  ", "  🗄️ 저장 내역  "])

# ── 탭 1: 검색 ───────────────────────────────
with tab1:
    if search_clicked and query:
        if not naver_id or not naver_secret:
            st.error("❌ Naver API 키를 입력해주세요!")
        else:
            with st.spinner("🔍 뉴스 검색 중..."):
                try:
                    items = search_naver(query, display_count)
                    st.session_state["items"] = items
                    st.session_state["query"] = query
                except Exception as e:
                    st.error(f"검색 실패: {e}")

    if "items" in st.session_state and st.session_state["items"]:
        items = st.session_state["items"]
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.markdown(f"<p style='color:#94a3b8;'>🔎 <b style='color:white;'>'{st.session_state['query']}'</b> 검색 결과 <b style='color:#7c3aed;'>{len(items)}건</b></p>", unsafe_allow_html=True)
        with col_b:
            if st.button("💾 DB 저장"):
                if not db_url:
                    st.error("DB URL 없음!")
                else:
                    save_to_db(st.session_state["query"], items)
                    st.success("✅ 저장 완료!")

        for item in items:
            title = clean(item["title"])
            desc  = clean(item.get("description", ""))
            link  = item.get("link", "#")
            date  = item.get("pubDate", "")
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">
                    <span class="badge badge-naver">NAVER</span>
                    {title}
                </div>
                <div class="news-desc">{desc}</div>
                <div class="news-meta">
                    🕒 {date} &nbsp;|&nbsp;
                    <a href="{link}" target="_blank" class="news-link">기사 원문 →</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
    elif not search_clicked:
        st.markdown("""
        <div style='text-align:center; padding:60px; color:#64748b;'>
            <div style='font-size:64px;'>🔍</div>
            <p style='font-size:18px; margin-top:16px;'>위에서 검색어를 입력하고 검색 버튼을 눌러보세요</p>
        </div>
        """, unsafe_allow_html=True)

# ── 탭 2: AI 요약 ─────────────────────────────
with tab2:
    if "items" not in st.session_state or not st.session_state["items"]:
        st.markdown("""
        <div style='text-align:center; padding:60px; color:#64748b;'>
            <div style='font-size:64px;'>🤖</div>
            <p style='font-size:18px; margin-top:16px;'>먼저 뉴스를 검색해주세요</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:#94a3b8;'>검색어: <b style='color:white;'>{st.session_state['query']}</b> — {len(st.session_state['items'])}개 기사 AI 요약</p>", unsafe_allow_html=True)
        if st.button("✨ GPT로 요약하기"):
            if not openai_key:
                st.error("❌ OpenAI API 키를 입력해주세요!")
            else:
                with st.spinner("🤖 AI가 분석 중입니다..."):
                    try:
                        summary = llm_summary(st.session_state["query"], st.session_state["items"])
                        st.session_state["summary"] = summary
                    except Exception as e:
                        st.error(f"요약 실패: {e}")

        if "summary" in st.session_state:
            st.markdown(f"""
            <div class="summary-box">
                <span class="badge badge-ai">AI 요약</span><br><br>
                {st.session_state["summary"].replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)

# ── 탭 3: 저장 내역 ───────────────────────────
with tab3:
    if not db_url:
        st.error("❌ Database URL을 입력해주세요!")
    else:
        col_r, col_s = st.columns([5, 1])
        with col_s:
            if st.button("🔄 새로고침"):
                st.rerun()
        try:
            total, queries, top_q = load_stats()
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{total}</div><div class="stat-label">총 저장 기사</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="stat-card"><div class="stat-number">{queries}</div><div class="stat-label">검색어 종류</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="stat-card"><div class="stat-number" style="font-size:22px;">{top_q}</div><div class="stat-label">인기 검색어</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            df = load_saved_news()
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("저장된 뉴스가 없습니다.")
        except Exception as e:
            st.error(f"DB 조회 실패: {e}")
