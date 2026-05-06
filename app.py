import streamlit as st
import requests
import psycopg2
import pandas as pd
import html
import xml.etree.ElementTree as ET
import urllib.parse

# ══════════════════════════════════════════════
#  페이지 설정
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="📰 AI 뉴스 검색",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.05);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    h1, h2, h3 { color: #ffffff !important; }
    .news-card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 14px;
    }
    .news-card:hover {
        background: rgba(255,255,255,0.12);
        border-color: #7c3aed;
    }
    .news-title { font-size: 16px; font-weight: 700; color: #e2e8f0; margin-bottom: 8px; }
    .news-desc  { font-size: 14px; color: #94a3b8; line-height: 1.6; }
    .news-meta  { font-size: 12px; color: #64748b; margin-top: 10px; }
    .news-link  { color: #7c3aed; text-decoration: none; font-weight: 600; }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-right: 8px; }
    .badge-naver  { background: #03c75a; color: white; }
    .badge-google { background: #4285f4; color: white; }
    .badge-ai     { background: #7c3aed; color: white; }
    .stTextInput input {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        font-size: 16px !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 10px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #7c3aed !important; border-bottom-color: #7c3aed !important; }
    .summary-box {
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.4);
        border-radius: 16px;
        padding: 24px;
        color: #e2e8f0;
        font-size: 15px;
        line-height: 1.8;
    }
    .stat-card { background: rgba(255,255,255,0.06); border-radius: 14px; padding: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }
    .stat-number { font-size: 36px; font-weight: 800; color: #7c3aed; }
    .stat-label  { font-size: 13px; color: #94a3b8; margin-top: 4px; }
    .empty-state { text-align:center; padding:60px; color:#64748b; }
    .empty-icon  { font-size: 64px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  사이드바
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    st.markdown("---")
    try:
        naver_id     = st.secrets["NAVER_CLIENT_ID"]
        naver_secret = st.secrets["NAVER_CLIENT_SECRET"]
        groq_key     = st.secrets["GROQ_API_KEY"]
        db_url       = st.secrets["DATABASE_URL"]
        st.success("✅ API 키 자동 로드됨")
    except Exception:
        st.warning("직접 입력하세요")
        naver_id     = st.text_input("Naver Client ID",     type="password")
        naver_secret = st.text_input("Naver Client Secret", type="password")
        groq_key     = st.text_input("Groq API Key",        type="password")
        db_url       = st.text_input("Database URL",        type="password")

    st.markdown("---")
    display_count = st.slider("검색 결과 수", 3, 10, 5)
    st.markdown("---")
    st.markdown("""
    <div style='color:#64748b; font-size:12px; line-height:2.2;'>
    📌 <b style='color:#94a3b8'>사용법</b><br>
    1️⃣ 검색어 입력<br>
    2️⃣ 검색 버튼 클릭<br>
    3️⃣ 네이버 / 구글 비교<br>
    4️⃣ DB 저장 클릭<br>
    5️⃣ AI 요약 확인<br>
    6️⃣ 저장 내역 조회
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  헤더
# ══════════════════════════════════════════════
st.markdown("""
<div style='text-align:center; padding:30px 0 20px 0;'>
    <h1 style='font-size:46px; font-weight:900;
               background: linear-gradient(135deg, #7c3aed, #06b6d4);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        📰 AI 뉴스 검색
    </h1>
    <p style='color:#94a3b8; font-size:16px; margin-top:6px;'>
        Naver + Google 뉴스 비교 &nbsp;·&nbsp; AI 요약 &nbsp;·&nbsp; 클라우드 저장
    </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  DB
# ══════════════════════════════════════════════
def get_conn():
    result = urllib.parse.urlparse(db_url)
    return psycopg2.connect(
        host=result.hostname,
        port=result.port or 6543,
        database=result.path[1:],
        user=result.username,
        password=urllib.parse.unquote(result.password),
        sslmode="require"
    )

def init_db():
    if not db_url:
        return
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
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
#  헬퍼
# ══════════════════════════════════════════════
def clean(text):
    return html.unescape(str(text).replace("<b>","").replace("</b>","").strip())

def render_news(items, badge_class, badge_label):
    if not items:
        st.markdown("<div class='empty-state'><div class='empty-icon'>😶</div><p>결과가 없습니다</p></div>", unsafe_allow_html=True)
        return
    for item in items:
        title = clean(item.get("title",""))
        desc  = clean(item.get("description",""))
        link  = item.get("link","#")
        date  = item.get("pubDate","")
        st.markdown(f"""
        <div class="news-card">
            <div class="news-title">
                <span class="badge {badge_class}">{badge_label}</span>{title}
            </div>
            <div class="news-desc">{desc}</div>
            <div class="news-meta">
                🕒 {date} &nbsp;|&nbsp;
                <a href="{link}" target="_blank" class="news-link">기사 원문 →</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  API 함수
# ══════════════════════════════════════════════
def search_naver(query, n=5):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": naver_id,
        "X-Naver-Client-Secret": naver_secret,
    }
    res = requests.get(url, headers=headers,
                       params={"query": query, "display": n, "sort": "date"}, timeout=10)
    res.raise_for_status()
    return res.json().get("items", [])

def search_google(query, n=5):
    url = "https://news.google.com/rss/search"
    params = {"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
    res = requests.get(url, params=params, timeout=10)
    root = ET.fromstring(res.content)
    items = []
    for item in root.findall(".//item")[:n]:
        items.append({
            "title":       item.findtext("title", ""),
            "link":        item.findtext("link", ""),
            "description": item.findtext("description", ""),
            "pubDate":     item.findtext("pubDate", ""),
        })
    return items

def save_to_db(query, items):
    with get_conn() as conn:
        with conn.cursor() as cur:
            for item in items:
                cur.execute("""
                    INSERT INTO naver_news (query, title, link, description, pub_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, (query,
                      clean(item.get("title","")),
                      item.get("link",""),
                      clean(item.get("description","")),
                      item.get("pubDate","")))
        conn.commit()

def llm_compare(query, naver_items, google_items):
    from groq import Groq
    client = Groq(api_key=groq_key)
    naver_text  = "\n".join([f"- {clean(a.get('title',''))}" for a in naver_items])
    google_text = "\n".join([f"- {clean(a.get('title',''))}" for a in google_items])
    prompt = f"""검색어: [{query}]

[네이버 뉴스 목록]
{naver_text}

[구글 뉴스 목록]
{google_text}

두 뉴스 소스를 비교 분석해서 한국어로 정리해주세요:

1. 📌 공통 주제
2. 🟢 네이버에서만 다루는 내용
3. 🔵 구글에서만 다루는 내용
4. 📝 전체 요약"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "당신은 뉴스 비교 분석 전문가입니다."},
            {"role": "user",   "content": prompt},
        ]
    )
    return res.choices[0].message.content

def load_saved():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, query, title, description, pub_date, saved_at
                FROM naver_news ORDER BY saved_at DESC LIMIT 100
            """)
            rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["ID","검색어","제목","내용","발행일","저장시각"])

def load_stats():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM naver_news")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT query) FROM naver_news")
            queries = cur.fetchone()[0]
            cur.execute("SELECT query FROM naver_news GROUP BY query ORDER BY COUNT(*) DESC LIMIT 1")
            row = cur.fetchone()
            top_q = row[0] if row else "-"
    return total, queries, top_q

# ══════════════════════════════════════════════
#  검색창
# ══════════════════════════════════════════════
col_i, col_b = st.columns([5, 1])
with col_i:
    query = st.text_input("", placeholder="🔍  검색어를 입력하세요  (예: 인공지능, 주식, 날씨)", label_visibility="collapsed")
with col_b:
    search_clicked = st.button("검색 🔍")

if search_clicked and query:
    if not naver_id or not naver_secret:
        st.error("❌ Naver API 키를 입력해주세요!")
    else:
        with st.spinner("🔍 네이버 & 구글 뉴스 검색 중..."):
            try:
                naver_items  = search_naver(query, display_count)
                google_items = search_google(query, display_count)
                st.session_state["naver_items"]  = naver_items
                st.session_state["google_items"] = google_items
                st.session_state["query"]        = query
                st.session_state.pop("summary", None)
                st.success(f"✅ 네이버 {len(naver_items)}건 · 구글 {len(google_items)}건 검색 완료!")
            except Exception as e:
                st.error(f"검색 실패: {e}")

# ══════════════════════════════════════════════
#  탭
# ══════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "  📡 네이버 뉴스  ",
    "  🌐 구글 뉴스  ",
    "  🤖 AI 비교 요약  ",
    "  🗄️ 저장 내역  "
])

# ── 탭 1: 네이버 ─────────────────────────────
with tab1:
    if "naver_items" in st.session_state:
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.markdown(f"<p style='color:#94a3b8; margin-bottom:16px;'>🟢 <b style='color:#03c75a;'>네이버 뉴스</b> — '{st.session_state['query']}' 검색 결과 {len(st.session_state['naver_items'])}건</p>", unsafe_allow_html=True)
        with col_b:
            if st.button("💾 DB 저장"):
                if not db_url:
                    st.error("DB URL 없음!")
                else:
                    try:
                        save_to_db(st.session_state["query"], st.session_state["naver_items"])
                        st.success("✅ 저장 완료!")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
        render_news(st.session_state["naver_items"], "badge-naver", "NAVER")
    else:
        st.markdown("<div class='empty-state'><div class='empty-icon'>📡</div><p style='font-size:18px; margin-top:16px;'>검색어를 입력하고 검색 버튼을 눌러보세요</p></div>", unsafe_allow_html=True)

# ── 탭 2: 구글 ──────────────────────────────
with tab2:
    if "google_items" in st.session_state:
        st.markdown(f"<p style='color:#94a3b8; margin-bottom:16px;'>🔵 <b style='color:#4285f4;'>구글 뉴스</b> — '{st.session_state['query']}' 검색 결과 {len(st.session_state['google_items'])}건</p>", unsafe_allow_html=True)
        render_news(st.session_state["google_items"], "badge-google", "GOOGLE")
    else:
        st.markdown("<div class='empty-state'><div class='empty-icon'>🌐</div><p style='font-size:18px; margin-top:16px;'>검색어를 입력하고 검색 버튼을 눌러보세요</p></div>", unsafe_allow_html=True)

# ── 탭 3: AI 비교 요약 ───────────────────────
with tab3:
    if "naver_items" not in st.session_state:
        st.markdown("<div class='empty-state'><div class='empty-icon'>🤖</div><p style='font-size:18px; margin-top:16px;'>먼저 뉴스를 검색해주세요</p></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='color:#94a3b8;'>네이버 <b style='color:#03c75a;'>{len(st.session_state['naver_items'])}건</b> + 구글 <b style='color:#4285f4;'>{len(st.session_state['google_items'])}건</b> — AI 비교 분석</p>", unsafe_allow_html=True)
        if st.button("✨ AI로 비교 요약하기"):
            if not groq_key:
                st.error("❌ Groq API 키를 입력해주세요!")
            else:
                with st.spinner("🤖 AI가 분석 중입니다..."):
                    try:
                        summary = llm_compare(
                            st.session_state["query"],
                            st.session_state["naver_items"],
                            st.session_state["google_items"]
                        )
                        st.session_state["summary"] = summary
                    except Exception as e:
                        st.error(f"요약 실패: {e}")

        if "summary" in st.session_state:
            st.markdown(f"""
            <div class="summary-box">
                <span class="badge badge-ai">AI 비교 분석</span><br><br>
                {st.session_state["summary"].replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)

# ── 탭 4: 저장 내역 ──────────────────────────
with tab4:
    if not db_url:
        st.error("❌ Database URL을 입력해주세요!")
    else:
        col_r, _ = st.columns([1, 5])
        with col_r:
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
            df = load_saved()
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("저장된 뉴스가 없습니다. 검색 후 저장해보세요!")
        except Exception as e:
            st.error(f"DB 연결 실패: {e}")
