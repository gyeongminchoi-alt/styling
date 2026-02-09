# app.py
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests
import streamlit as st
from openai import OpenAI


# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="얼굴형 기반 미용실 추천", layout="wide")
st.title("얼굴형 기반 미용실 추천 (Kakao Local + 웹후기 기반 확장검색)")
st.caption("자가진단 선택 → (GPT 추천 3개) → (웹후기 태그 기반 확장검색) → 근처 미용실 추천")


# =========================
# ✅ 실존 헤어스타일/시술 용어 화이트리스트
# =========================
STYLE_TERMS = [
    "단발", "중단발", "장발", "숏컷", "보브컷", "허쉬컷", "레이어드컷", "샤기컷",
    "리프컷", "가일컷", "투블럭", "댄디컷", "크롭컷",
    "C컬펌", "S컬펌", "빌드펌", "히피펌", "쉐도우펌", "가르마펌", "애즈펌",
    "리젠트펌", "아이롱펌", "볼륨펌", "디지털펌", "셋팅펌",
    "볼륨매직", "매직", "매직셋팅",
    "염색", "탈색", "뿌리염색", "옴브레", "발레아쥬",
    "애쉬브라운", "애쉬그레이", "애쉬블루",
    "핑크브라운", "초코브라운", "카키브라운",
    "다운펌", "두피케어", "클리닉",
    "시스루뱅", "처피뱅", "풀뱅", "애교머리",
]
STYLE_STOP = {"미용실", "헤어", "컷", "펌", "염색"}


# =========================
# 필요한 이미지 파일 체크
# =========================
REQUIRED_IMAGES = [
    "웜톤.jpg", "쿨톤.jpg",
    "계란형.png", "마름모형.png", "하트형.png", "땅콩형.png", "육각형.png", "둥근형.png",
    "아치형.png", "직선형.png", "각진형.png", "둥근형(눈썹).png",
    "직모.png", "곱슬.png",
]


def must_exist(path: str) -> None:
    if not Path(path).exists():
        st.error(
            f"이미지를 찾을 수 없어요: {path}\n\n"
            f"app.py와 같은 폴더에 '{path}' 파일이 있는지 확인해주세요."
        )
        st.stop()


for p in REQUIRED_IMAGES:
    must_exist(p)


# =========================
# Kakao API 키 로드
# =========================
KAKAO_REST_API_KEY = (st.secrets.get("KAKAO_REST_API_KEY", "") or "").strip()
if not KAKAO_REST_API_KEY:
    st.warning("KAKAO_REST_API_KEY가 없어요. .streamlit/secrets.toml에 설정해주세요.")
    st.stop()


# =========================
# OpenAI API Key (사이드바 입력)
# =========================
st.sidebar.header("🔑 API Key 설정")
OPENAI_API_KEY = st.sidebar.text_input("OpenAI API Key (필수)", type="password").strip()
st.sidebar.caption("모든 선택 완료 시 GPT 추천(3개) + 웹후기 기반 확장검색으로 미용실을 찾습니다.")


# =========================
# UI 카드 렌더 유틸 (✅ 1클릭 즉시 반영)
# =========================
def select_card(
    *,
    title: str,
    image_path: str,
    button_label: str,
    on_click_value: str,
    session_key: str,
    button_key: str,
    desc_md: str | None = None,
    img_width: int = 160,
    selected: bool = False,
) -> None:
    st.subheader(title)
    st.image(image_path, width=img_width)
    if desc_md:
        st.markdown(desc_md)

    btn_type = "primary" if selected else "secondary"
    if st.button(button_label, key=button_key, use_container_width=True, type=btn_type):
        st.session_state[session_key] = on_click_value
        st.rerun()


# =========================
# 얼굴형 → 힌트 용어
# =========================
FACE_SHAPE_TO_KEYWORDS: Dict[str, List[str]] = {
    "둥근얼굴형": ["레이어드컷", "S컬펌", "C컬펌", "시스루뱅"],
    "긴얼굴형": ["단발", "중단발", "C컬펌", "히피펌"],
    "각진 얼굴형": ["레이어드컷", "S컬펌", "볼륨펌"],
    "역삼각형 얼굴": ["단발", "C컬펌", "볼륨매직"],
    "계란형 얼굴": ["단발", "중단발", "레이어드컷", "S컬펌"],
}

APP_FACE_TO_RECO_FACE: Dict[str, str] = {
    "둥근형": "둥근얼굴형",
    "계란형": "계란형 얼굴",
    "하트형": "역삼각형 얼굴",
    "육각형": "각진 얼굴형",
    "마름모형": "긴얼굴형",
    "땅콩형": "각진 얼굴형",
}


def build_auto_terms(app_face_shape: str, max_terms: int = 6) -> List[str]:
    if not app_face_shape:
        return ["레이어드컷", "C컬펌", "S컬펌"]
    reco_face = APP_FACE_TO_RECO_FACE.get(app_face_shape, "계란형 얼굴")
    terms = FACE_SHAPE_TO_KEYWORDS.get(reco_face, [])
    return terms[:max_terms] if terms else ["레이어드컷", "C컬펌", "S컬펌"]


# =========================
# GPT 추천 생성(3개) - 실존 용어만
# =========================
def safe_json_extract(text: str) -> str:
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    return m.group(0) if m else raw


def normalize_query(q: str) -> str:
    q = (q or "").replace("\n", " ").strip()
    q = re.sub(r"\s+", " ", q)
    if "미용실" not in q:
        q = f"{q} 미용실".strip()
    return q


def enforce_style_whitelist(query: str, allowed_terms: List[str]) -> str:
    q = query.replace("미용실", "").strip()
    terms_sorted = sorted(allowed_terms, key=len, reverse=True)
    picked: List[str] = []
    for t in terms_sorted:
        if t in q and t not in picked:
            picked.append(t)

    if not picked:
        picked = [allowed_terms[0]] if allowed_terms else ["레이어드컷"]

    picked = picked[:2]
    return normalize_query(" ".join(picked))


def make_queries_with_openai(
    *,
    api_key: str,
    tone: str,
    face_shape: str,
    brow_shape: str,
    hair_type: str,
    hint_terms: List[str],
) -> Tuple[List[str], List[str]]:
    client = OpenAI(api_key=api_key)
    allowed = STYLE_TERMS

    prompt = f"""
너는 한국 헤어디자이너야.
아래 사용자의 자가진단 정보(톤/얼굴형/눈썹/모발)를 바탕으로
카카오 로컬에서 검색 가능한 "미용실 검색 키워드 3개"를 추천해줘.

중요 규칙:
- 각 query에는 반드시 '미용실' 포함
- query는 반드시 "허용된 스타일 용어 목록"에서만 골라 조합
- 허용 목록 밖 단어 절대 금지
- (스타일용어 1~2개 + '미용실')로 간결하게

[사용자 정보]
- tone: {tone}
- face_shape: {face_shape}
- brow_shape: {brow_shape}
- hair_type: {hair_type}

[추천 힌트(우선 고려 가능)]
{json.dumps(hint_terms, ensure_ascii=False)}

[허용된 스타일 용어 목록]
{json.dumps(allowed, ensure_ascii=False)}

출력(JSON만):
{{
  "recommendations": [
    {{"query":"... 미용실","reason":"..."}},
    {{"query":"... 미용실","reason":"..."}},
    {{"query":"... 미용실","reason":"..."}}
  ]
}}
""".strip()

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    raw = safe_json_extract(resp.choices[0].message.content or "")
    queries: List[str] = []
    reasons: List[str] = []

    try:
        obj = json.loads(raw)
        recs = obj.get("recommendations", [])
        if isinstance(recs, list):
            for it in recs:
                if not isinstance(it, dict):
                    continue
                queries.append(str(it.get("query", "")).strip())
                reasons.append(str(it.get("reason", "")).strip())
    except Exception:
        queries, reasons = [], []

    final_q: List[str] = []
    final_r: List[str] = []
    seen = set()

    for q, r in zip(queries, reasons):
        fixed = enforce_style_whitelist(q, allowed_terms=allowed)
        if fixed and fixed not in seen:
            seen.add(fixed)
            final_q.append(fixed)
            final_r.append(r)
        if len(final_q) >= 3:
            break

    if len(final_q) < 3:
        fallback_pool = []
        for t in hint_terms:
            if t in STYLE_TERMS:
                fallback_pool.append(normalize_query(f"{t} 미용실"))
        for t in STYLE_TERMS:
            fallback_pool.append(normalize_query(f"{t} 미용실"))

        for q in fallback_pool:
            if q not in seen:
                seen.add(q)
                final_q.append(q)
                final_r.append("화이트리스트 기반 보완 추천")
            if len(final_q) >= 3:
                break

    return final_q[:3], final_r[:3]


# =========================
# Kakao Local + Kakao Search 유틸
# =========================
def kakao_headers() -> Dict[str, str]:
    return {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}


@st.cache_data(show_spinner=False, ttl=3600)
def kakao_address_to_xy(address: str) -> Tuple[float, float]:
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    r = requests.get(url, headers=kakao_headers(), params={"query": address}, timeout=10)
    r.raise_for_status()
    docs = r.json().get("documents", [])
    if not docs:
        raise ValueError("주소를 찾지 못했어요. 더 자세한 주소로 입력해 주세요.")
    return float(docs[0]["x"]), float(docs[0]["y"])


@st.cache_data(show_spinner=False, ttl=600)
def kakao_keyword_search(
    query: str,
    x: float,
    y: float,
    radius_m: int = 3000,
    size: int = 15,
    page: int = 1,
) -> List[dict]:
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {
        "query": query,
        "x": str(x),
        "y": str(y),
        "radius": str(radius_m),
        "size": str(size),
        "page": str(page),
        "sort": "distance",
    }
    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("documents", [])


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@st.cache_data(show_spinner=False, ttl=1800)
def kakao_search_blog(query: str, size: int = 5) -> List[dict]:
    url = "https://dapi.kakao.com/v2/search/blog"
    params = {"query": query, "size": size, "sort": "accuracy"}
    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("documents", [])


@st.cache_data(show_spinner=False, ttl=1800)
def kakao_search_web(query: str, size: int = 5) -> List[dict]:
    url = "https://dapi.kakao.com/v2/search/web"
    params = {"query": query, "size": size, "sort": "accuracy"}
    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("documents", [])


def build_review_snippet_for_place(place_name: str, area_hint: str) -> str:
    q = f"{place_name} {area_hint} 미용실 후기 펌 컷"
    blog_docs = []
    web_docs = []
    try:
        blog_docs = kakao_search_blog(q, size=5)
    except Exception:
        blog_docs = []
    try:
        web_docs = kakao_search_web(q, size=5)
    except Exception:
        web_docs = []

    parts: List[str] = []
    for d in blog_docs[:5]:
        parts.append(f"[블로그] {strip_html(d.get('title',''))} - {strip_html(d.get('contents',''))}")
    for d in web_docs[:5]:
        parts.append(f"[웹] {strip_html(d.get('title',''))} - {strip_html(d.get('contents',''))}")

    return " | ".join([p for p in parts if p.strip()])[:2500]


def analyze_styles_from_reviews_with_openai(
    *,
    api_key: str,
    chosen_query: str,
    places: List[dict],
    review_snippets: Dict[str, str],
) -> Dict[str, Dict]:
    client = OpenAI(api_key=api_key)

    payload = []
    for p in places:
        name = p.get("place_name", "")
        addr = p.get("road_address_name", "") or p.get("address_name", "")
        snip = review_snippets.get(name, "")
        payload.append({"name": name, "address": addr, "snippet": snip})

    prompt = f"""
너는 한국 헤어/미용실 리뷰 분석가야.
사용자의 의도 키워드와 각 미용실의 웹 후기 스니펫을 보고,
각 미용실이 유명한 시술/스타일 태그를 뽑아줘.

규칙:
- tags는 반드시 아래 허용 목록에서만 선택
- snippet이 빈 경우 tags=[], summary="정보 부족"
- JSON만 출력

[chosen_query] {chosen_query}
[허용된 스타일 용어 목록] {json.dumps(STYLE_TERMS, ensure_ascii=False)}
[데이터] {json.dumps(payload, ensure_ascii=False)}

출력:
{{"salons":[{{"name":"...","tags":["..."],"summary":"..."}}, ...]}}
""".strip()

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    raw = safe_json_extract(resp.choices[0].message.content or "")
    result: Dict[str, Dict] = {}
    try:
        obj = json.loads(raw)
        salons = obj.get("salons", [])
        if isinstance(salons, list):
            for s in salons:
                if not isinstance(s, dict):
                    continue
                name = str(s.get("name", "")).strip()
                tags = s.get("tags", [])
                summary = str(s.get("summary", "")).strip()
                if isinstance(tags, list):
                    tags = [str(t).strip() for t in tags if str(t).strip() in STYLE_TERMS]
                else:
                    tags = []
                if name:
                    result[name] = {"tags": tags[:6], "summary": summary}
    except Exception:
        result = {}
    return result


def build_expanded_queries_from_tags(
    chosen_query: str,
    style_map: Dict[str, Dict],
    max_queries: int = 3,
) -> List[str]:
    counter = Counter()
    for v in style_map.values():
        for t in v.get("tags", []):
            if t and t not in STYLE_STOP:
                counter[t] += 1

    ranked = [t for t, _ in counter.most_common()]

    chosen_words = set(re.findall(r"[가-힣A-Za-z0-9]+", chosen_query))
    ranked = [t for t in ranked if t not in chosen_words]

    expanded = [normalize_query(f"{t} 미용실") for t in ranked[:max_queries]]
    # 중복 제거
    uniq, seen = [], set()
    for q in expanded:
        if q not in seen:
            seen.add(q)
            uniq.append(q)
    return uniq[:max_queries]


def merge_places(*lists: List[dict]) -> List[dict]:
    merged = []
    seen = set()
    for lst in lists:
        for p in lst:
            key = p.get("place_url") or (p.get("place_name", "") + "|" + (p.get("road_address_name", "") or p.get("address_name", "")))
            if key and key not in seen:
                seen.add(key)
                merged.append(p)
    return merged


# =========================
# ✅ 검색 결과가 잘 나오게 하는 핵심: fallback 검색
# =========================
def build_fallback_queries(chosen_query: str) -> List[str]:
    q = (chosen_query or "").strip()
    q_no_salon = q.replace("미용실", "").strip()
    fallbacks = []

    if q:
        fallbacks.append(q)
    if q_no_salon:
        fallbacks.append(q_no_salon)
        fallbacks.append(f"{q_no_salon} 헤어")
        fallbacks.append(f"{q_no_salon} 헤어샵")

    # 최후의 보루 (거의 무조건 결과 있음)
    fallbacks.append("미용실")
    # 중복 제거
    uniq = []
    seen = set()
    for x in fallbacks:
        x = re.sub(r"\s+", " ", x).strip()
        if x and x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def search_salons_with_fallback(
    *,
    chosen_query: str,
    x: float,
    y: float,
    radius_m: int,
    size: int = 15,
) -> Tuple[List[dict], str, int]:
    """
    (results, used_query, used_radius)
    - query를 완화하며 시도
    - 결과가 없으면 radius를 2배까지 늘려서 재시도
    """
    queries = build_fallback_queries(chosen_query)
    radius_try = [radius_m, min(radius_m * 2, 20000)]

    for r in radius_try:
        for q in queries:
            # page=1만으로 부족하면 2페이지까지 추가(결과 늘리기)
            res1 = kakao_keyword_search(query=q, x=x, y=y, radius_m=r, size=size, page=1)
            res2 = kakao_keyword_search(query=q, x=x, y=y, radius_m=r, size=size, page=2) if res1 else []
            res = merge_places(res1, res2)
            if res:
                return res, q, r

    return [], queries[0] if queries else chosen_query, radius_m


# =========================
# 1) 선택 UI
# =========================
for k in ("tone", "face_shape", "brow_shape", "hair_type"):
    if k not in st.session_state:
        st.session_state[k] = None

steps_done = sum(1 for k in ("tone", "face_shape", "brow_shape", "hair_type") if st.session_state[k] is not None)
st.progress(steps_done / 4)

# ---- tone
st.header("1) 웜톤 / 쿨톤 선택")
tone_cols = st.columns(2, gap="large")
with tone_cols[0]:
    select_card(
        title="웜톤",
        image_path="웜톤.jpg",
        desc_md="**자가진단**\n1. 팔목 혈관이 **초록빛**\n2. 피부에 **노란기**가 많음",
        button_label="✅ 웜톤 선택",
        on_click_value="웜",
        session_key="tone",
        button_key="btn_tone_warm",
        img_width=100,
        selected=(st.session_state["tone"] == "웜"),
    )
with tone_cols[1]:
    select_card(
        title="쿨톤",
        image_path="쿨톤.jpg",
        desc_md="**자가진단**\n1. 팔목 혈관이 **파란빛**\n2. 피부에 **붉은기**가 많음",
        button_label="✅ 쿨톤 선택",
        on_click_value="쿨",
        session_key="tone",
        button_key="btn_tone_cool",
        img_width=100,
        selected=(st.session_state["tone"] == "쿨"),
    )

if st.button("tone 초기화", key="reset_tone", type="secondary"):
    st.session_state["tone"] = None
    st.rerun()

st.divider()

# ---- face
st.header("2) 얼굴형 선택")
FACE_CHOICES = [
    ("계란형", "계란형.png", "광대 X, 턱 X - 광대와 턱 골격이 이상적으로 잡혀있고 눈에 띄게 돌출되어 있지 않음."),
    ("마름모형", "마름모형.png", "광대 O, 턱 X - 옆턱 골격은 없는데 광대만 부각됨."),
    ("하트형", "하트형.png", "광대 O 턱 △ - 광대 골격과 턱 골격이 모두 있는데 광대 골격이 턱 골격보다 넓고 강함."),
    ("땅콩형", "땅콩형.png", "광대 O 턱 O - 광대 골격과 턱 골격이 모두 있고, 하트형과 다르게 광대 골격과 턱 골격의 너비가 같음."),
    ("육각형", "육각형.png", "광대 X 턱 O - 턱 골격만 있고 땅콩형과는 다르게 옆으로 튀어나온 광대 골격이 없음."),
    ("둥근형", "둥근형.png", "광대 X 턱 X - 얼굴 전체적으로 살이 많아 테투리에 골격이 잘 보이지 않음."),
]
rows = [FACE_CHOICES[:3], FACE_CHOICES[3:]]
for r_i, r in enumerate(rows):
    cols = st.columns(3, gap="large")
    for col, (name, img, desc) in zip(cols, r):
        with col:
            select_card(
                title=name,
                image_path=img,
                desc_md=desc,
                button_label=f"✅ {name} 선택",
                on_click_value=name,
                session_key="face_shape",
                button_key=f"btn_face_{r_i}_{name}",
                img_width=160,
                selected=(st.session_state["face_shape"] == name),
            )

if st.button("face_shape 초기화", key="reset_face", type="secondary"):
    st.session_state["face_shape"] = None
    st.rerun()

st.divider()

# ---- brow
st.header("3) 눈썹 모양 선택")
BROW_CHOICES = [("아치형", "아치형.png"), ("직선형", "직선형.png"), ("각진형", "각진형.png"), ("둥근형", "둥근형(눈썹).png")]
brow_rows = [BROW_CHOICES[:2], BROW_CHOICES[2:]]
for r_i, r in enumerate(brow_rows):
    cols = st.columns(2, gap="large")
    for col, (name, img) in zip(cols, r):
        with col:
            select_card(
                title=name,
                image_path=img,
                button_label=f"✅ {name} 선택",
                on_click_value=name,
                session_key="brow_shape",
                button_key=f"btn_brow_{r_i}_{name}",
                img_width=100,
                selected=(st.session_state["brow_shape"] == name),
            )

if st.button("brow_shape 초기화", key="reset_brow", type="secondary"):
    st.session_state["brow_shape"] = None
    st.rerun()

st.divider()

# ---- hair type
st.header("4) 모발 타입 선택")
hair_cols = st.columns(2, gap="large")
with hair_cols[0]:
    select_card(
        title="직모",
        image_path="직모.png",
        button_label="✅ 직모 선택",
        on_click_value="직모",
        session_key="hair_type",
        button_key="btn_hair_straight",
        img_width=80,
        selected=(st.session_state["hair_type"] == "직모"),
    )
with hair_cols[1]:
    select_card(
        title="곱슬",
        image_path="곱슬.png",
        button_label="✅ 곱슬 선택",
        on_click_value="곱슬",
        session_key="hair_type",
        button_key="btn_hair_curly",
        img_width=80,
        selected=(st.session_state["hair_type"] == "곱슬"),
    )

if st.button("hair_type 초기화", key="reset_hair", type="secondary"):
    st.session_state["hair_type"] = None
    st.rerun()

st.divider()


# =========================
# 5) GPT 추천(3개)
# =========================
st.header("5) GPT 추천 키워드 3개(실존 스타일 용어)")

tone = st.session_state["tone"]
face_shape = st.session_state["face_shape"]
brow_shape = st.session_state["brow_shape"]
hair_type = st.session_state["hair_type"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("tone", tone or "-")
m2.metric("face_shape", face_shape or "-")
m3.metric("brow_shape", brow_shape or "-")
m4.metric("hair_type", hair_type or "-")

all_selected = all([tone, face_shape, brow_shape, hair_type])
has_openai_key = bool(OPENAI_API_KEY)

hint_terms = build_auto_terms(face_shape)

if "gpt_queries" not in st.session_state:
    st.session_state["gpt_queries"] = []
if "gpt_reasons" not in st.session_state:
    st.session_state["gpt_reasons"] = []

if not has_openai_key:
    st.warning("OpenAI API Key가 필요합니다. (사이드바에서 입력)")
elif not all_selected:
    st.warning("tone/face_shape/brow_shape/hair_type를 모두 선택하면 GPT 추천(3개)으로만 검색합니다.")
else:
    st.success("✅ 모든 선택 완료 → GPT 추천(3개)으로 검색합니다.")

gpt_btn = st.button(
    "✨ GPT 추천 검색어 3개 만들기",
    key="btn_make_gpt_queries",
    use_container_width=True,
    disabled=(not has_openai_key or not all_selected),
)

if gpt_btn:
    try:
        with st.spinner("GPT가 검색어 3개를 추천하는 중..."):
            qs, rs = make_queries_with_openai(
                api_key=OPENAI_API_KEY,
                tone=tone,
                face_shape=face_shape,
                brow_shape=brow_shape,
                hair_type=hair_type,
                hint_terms=hint_terms,
            )
            st.session_state["gpt_queries"] = qs
            st.session_state["gpt_reasons"] = rs
    except Exception as e:
        st.error(f"GPT 호출 오류: {e}")

chosen_query = ""
chosen_idx = 0
if all_selected and has_openai_key and st.session_state["gpt_queries"]:
    options = [f"🤖 GPT 추천 {i+1}: {q}" for i, q in enumerate(st.session_state["gpt_queries"])]
    chosen = st.radio(
        "아래 GPT 추천 키워드(3개) 중 하나로 1차 검색합니다.",
        options=options,
        index=0,
        key="auto_query_radio",
    )
    chosen_idx = options.index(chosen)
    chosen_query = st.session_state["gpt_queries"][chosen_idx]
    reason = st.session_state["gpt_reasons"][chosen_idx] if chosen_idx < len(st.session_state["gpt_reasons"]) else ""
    if reason:
        st.info(f"GPT 추천 이유: {reason}")

st.divider()


# =========================
# 6) Kakao Local 검색 + 웹후기 기반 확장검색
# =========================
st.header("6) (웹 후기 분석)으로 유명 스타일을 찾고 확장 검색하기")

address = st.text_input("내 위치(주소)를 입력해주세요 (예: 서울시 서대문구 연세로 50)", key="input_address")
radius = st.slider("검색 반경(미터)", 500, 10000, 3000, step=500, key="radius_slider")

use_review_expansion = st.toggle("웹 후기 기반 확장검색 사용", value=True)
topn_for_review = st.slider("후기 분석할 후보 개수(상위 N개)", 3, 15, 10, step=1)
expansion_queries_n = st.slider("확장 검색어 개수", 1, 3, 3, step=1)

# ✅ 추가: “검색 결과 잘 나오게” 옵션
st.subheader("검색 결과가 잘 나오게 하는 옵션")
auto_fallback = st.toggle("검색어 자동 완화(fallback) 사용", value=True)
auto_increase_radius = st.toggle("결과 없으면 반경 자동 확대(최대 2배)", value=True)
result_size = st.slider("검색 결과 개수(size)", 5, 20, 15, step=1)

find_btn = st.button("📍 (1차+확장) 근처 미용실 찾기", key="btn_find_salon", use_container_width=True)

if find_btn:
    if not has_openai_key:
        st.error("OpenAI API Key가 필요합니다. (사이드바에서 입력)")
        st.stop()
    if not all_selected:
        st.error("tone/face_shape/brow_shape/hair_type를 모두 선택해주세요.")
        st.stop()
    if not st.session_state["gpt_queries"] or not chosen_query.strip():
        st.error("먼저 GPT 추천 검색어(3개)를 생성하고 하나를 선택해주세요.")
        st.stop()
    if not address.strip():
        st.error("주소를 입력해주세요.")
        st.stop()

    try:
        with st.spinner("주소를 좌표로 변환 중..."):
            x, y = kakao_address_to_xy(address.strip())

        # 1차 검색 (자동 완화 적용)
        with st.spinner("1차: 미용실 검색 중..."):
            if auto_fallback:
                base_results, used_q, used_r = search_salons_with_fallback(
                    chosen_query=chosen_query,
                    x=x, y=y,
                    radius_m=radius,
                    size=result_size,
                )
                if (not auto_increase_radius) and used_r != radius:
                    # 사용자가 자동 확대 OFF면, 확대된 결과는 쓰지 않도록 처리
                    if used_r != radius:
                        # 다시 radius 고정으로만 시도
                        base_results, used_q, used_r = search_salons_with_fallback(
                            chosen_query=chosen_query,
                            x=x, y=y,
                            radius_m=radius,
                            size=result_size,
                        )
            else:
                base_results = kakao_keyword_search(query=chosen_query, x=x, y=y, radius_m=radius, size=result_size, page=1)
                used_q, used_r = chosen_query, radius

        if not base_results:
            st.warning("검색 결과가 없어요. (자동 완화/반경 확대 옵션을 켜보세요.)")
            st.stop()

        st.success(f"1차 검색 성공: '{used_q}' / 반경 {used_r}m / 결과 {len(base_results)}개")

        merged_results = base_results
        style_map: Dict[str, Dict] = {}
        expanded_queries: List[str] = []

        # 웹후기 기반 확장검색
        if use_review_expansion and base_results:
            candidates = base_results[:topn_for_review]
            area_hint = " ".join(address.strip().split()[:3]) or address.strip()

            with st.spinner("웹 후기(블로그/웹문서) 스니펫 수집 중..."):
                snippets: Dict[str, str] = {}
                for p in candidates:
                    name = p.get("place_name", "")
                    if not name:
                        continue
                    snippets[name] = build_review_snippet_for_place(name, area_hint)

            with st.spinner("웹 후기 기반 유명 스타일 태그 분석(GPT)..."):
                style_map = analyze_styles_from_reviews_with_openai(
                    api_key=OPENAI_API_KEY,
                    chosen_query=chosen_query,
                    places=candidates,
                    review_snippets=snippets,
                )

            expanded_queries = build_expanded_queries_from_tags(
                chosen_query=chosen_query,
                style_map=style_map,
                max_queries=expansion_queries_n,
            )

            extra_lists: List[List[dict]] = []
            if expanded_queries:
                with st.spinner("확장 검색어로 추가 검색 중..."):
                    for q in expanded_queries:
                        if auto_fallback:
                            res, _, _ = search_salons_with_fallback(
                                chosen_query=q, x=x, y=y, radius_m=radius, size=result_size
                            )
                            extra_lists.append(res)
                        else:
                            extra_lists.append(kakao_keyword_search(query=q, x=x, y=y, radius_m=radius, size=result_size, page=1))
                merged_results = merge_places(base_results, *extra_lists)

        # 출력
        st.success(f"최종 결과 {len(merged_results)}개")
        if expanded_queries:
            st.write("확장 검색어(후기 기반):", ", ".join(expanded_queries))

        map_points = [
            {"lat": float(r["y"]), "lon": float(r["x"])}
            for r in merged_results
            if r.get("x") and r.get("y")
        ]
        if map_points:
            st.map(map_points, zoom=13)

        st.subheader("미용실 리스트")
        for i, r in enumerate(merged_results, start=1):
            name = r.get("place_name", "")
            road = r.get("road_address_name", "") or r.get("address_name", "")
            phone = r.get("phone", "")
            dist = r.get("distance", "")
            url = r.get("place_url", "")

            st.markdown(f"### {i}. {name}")
            if dist:
                st.write(f"- 거리: **{dist}m**")
            st.write(f"- 주소: {road}")
            if phone:
                st.write(f"- 전화: {phone}")
            if url:
                st.write(f"- 카카오맵: {url}")

            if use_review_expansion and name in style_map:
                tags = style_map[name].get("tags", [])
                summary = style_map[name].get("summary", "")
                if tags:
                    st.write("- 웹 후기 기반 유명 스타일:", " / ".join(tags))
                if summary:
                    st.caption(f"후기 요약: {summary}")

    except Exception as e:
        st.error(f"오류: {e}")

st.divider()

if st.button("전체 선택/결과 초기화", key="reset_all", type="secondary"):
    for k in ("tone", "face_shape", "brow_shape", "hair_type"):
        st.session_state[k] = None
    st.session_state["gpt_queries"] = []
    st.session_state["gpt_reasons"] = []
    st.rerun()












