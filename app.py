# app.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests
import streamlit as st
from openai import OpenAI


import streamlit as st

st.set_page_config(page_title="✨🪞거울아 거울아🪞✨", layout="wide")

st.markdown("""
<h1 style='text-align: center;'>
✨🪞거울아 거울아🪞✨<br>
✨세상에서 내게 가장 어울리는 헤어스타일이 뭐니?✨
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<style>
div.stButton > button[kind="primary"] {
    background-color: #f8e99eec !important;   /* 골드 */
    border-color: #f8e99eec !important;
    color: #111111 !important;              /* 글씨 검정 */
    font-weight: 700 !important;
}
div.stButton > button[kind="primary"] * {
    color: #111111 !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #C9A227 !important;
    border-color: #C9A227 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# ✅ 실존 헤어스타일/시술 용어 화이트리스트
# =========================
STYLE_TERMS = [
    # 컷/기장
    "단발", "중단발", "장발", "숏컷", "보브컷", "허쉬컷", "레이어드컷", "샤기컷",
    "리프컷", "가일컷", "투블럭", "댄디컷", "크롭컷",
    # 펌/컬
    "C컬펌", "S컬펌", "빌드펌", "히피펌", "쉐도우펌", "가르마펌", "애즈펌",
    "리젠트펌", "아이롱펌", "볼륨펌", "디지털펌", "셋팅펌",
    "볼륨매직", "매직", "매직셋팅",
    # 염색/탈색
    "염색", "탈색", "뿌리염색", "옴브레", "발레아쥬",
    "애쉬브라운", "애쉬그레이", "애쉬블루",
    "핑크브라운", "초코브라운", "카키브라운",
    # 다운/클리닉
    "다운펌", "두피케어", "클리닉",
    # 앞머리/스타일링
    "시스루뱅", "처피뱅", "풀뱅", "애교머리",
]
STYLE_STOP = {"미용실", "헤어", "컷", "펌", "염색"}

# ✅ 염색 컬러/컬러링 관련 용어만 따로(후기 분석/추천에 사용)
COLOR_TERMS = [
    "염색", "탈색", "뿌리염색", "옴브레", "발레아쥬",
    "애쉬브라운", "애쉬그레이", "애쉬블루",
    "핑크브라운", "초코브라운", "카키브라운",
]


# =========================
# 이미지(선택) - 있으면 보여주고 없으면 텍스트 카드로만 진행
# =========================
OPTIONAL_IMAGES = {
    # tone
    "웜": "웜톤.jpg",
    "쿨": "쿨톤.jpg",
    # face
    "계란형": "계란형.png",
    "마름모형": "마름모형.png",
    "하트형": "하트형.png",
    "땅콩형": "땅콩형.png",
    "육각형": "육각형.png",
    "둥근형": "둥근형.png",
    # hair type
    "직모": "직모.png",
    "곱슬": "곱슬.png",
}


def maybe_image(path: Optional[str], width: int = 140) -> None:
    if not path:
        return
    if Path(path).exists():
        st.image(path, width=width)


# =========================
# ✅ 얼굴형/눈썹형 보완 포인트 & 강점 딕셔너리(고정)
# - reason 품질을 "안정적으로" 만들기 위한 기준 데이터
# =========================
FACE_PROFILE: Dict[str, Dict[str, List[str]]] = {
    # 얼굴형: {"concerns": [보완포인트], "strengths": [강점]}
    "계란형": {
        "concerns": ["비율은 좋지만 스타일에 따라 얼굴이 길어 보일 수 있음", "이마/턱 라인이 강조될 수 있음"],
        "strengths": ["가장 균형 잡힌 윤곽", "대부분의 기장/스타일 소화가 쉬움"],
    },
    "마름모형": {
        "concerns": ["광대 부각", "관자/볼 옆이 비어 보일 수 있음"],
        "strengths": ["선이 예뻐 세련된 분위기", "입체감이 있어 스타일링에 따라 분위기 전환이 큼"],
    },
    "하트형": {
        "concerns": ["상부(이마/관자) 넓어 보임", "턱이 상대적으로 가늘어 밸런스가 위로 쏠림"],
        "strengths": ["사랑스러운 인상", "이마가 시원해 경쾌한 스타일과 궁합이 좋음"],
    },
    "땅콩형": {
        "concerns": ["광대+턱 윤곽이 함께 도드라짐", "옆라인이 각져 보일 수 있음"],
        "strengths": ["또렷한 인상", "히피/샤기/레이어 계열로 개성 살리기 좋음"],
    },
    "육각형": {
        "concerns": ["턱/하관 존재감", "각이 도드라져 강해 보일 수 있음"],
        "strengths": ["라인이 또렷해 시크/도회적 무드에 강점", "볼륨/컬로 부드럽게 만들면 완성도가 큼"],
    },
    "둥근형": {
        "concerns": ["볼살/가로 폭이 강조", "얼굴이 짧아 보일 수 있음"],
        "strengths": ["동안/친근한 인상", "부드러운 분위기 연출이 쉬움"],
    },
}

BROW_PROFILE: Dict[str, Dict[str, List[str]]] = {
    # 눈썹형: {"concerns": [주의/보완포인트], "strengths": [강점]}
    "아치형": {
        "concerns": ["각도/두께가 과하면 세 보일 수 있음"],
        "strengths": ["세련되고 여성스러운 인상", "얼굴선을 부드럽게 정돈하는 효과"],
    },
    "직선형": {
        "concerns": ["너무 직선이면 딱딱/차가운 인상", "광대/이마가 더 강조될 수 있음"],
        "strengths": ["단정하고 지적인 인상", "시크/미니멀 무드와 궁합"],
    },
    "각진형": {
        "concerns": ["각이 강하면 공격적으로 보일 수 있음", "윤곽 각(턱/광대)과 합쳐져 더 강해질 수 있음"],
        "strengths": ["카리스마/도회적 인상", "스타일에 힘을 주면 존재감이 큼"],
    },
    "둥근형": {
        "concerns": ["너무 둥글면 얼굴도 둥글어 보일 수 있음"],
        "strengths": ["동안/친근한 인상", "부드러운 무드 강화"],
    },
}

# 무드 -> 추천 이유/키워드 톤 가이드
MOOD_GUIDE: Dict[str, Dict[str, List[str]]] = {
    "청순": {"keywords": ["부드럽게", "여리여리", "자연스럽게"], "avoid": ["과한 볼륨", "날카로운 라인"]},
    "시크": {"keywords": ["선명하게", "도회적으로", "깔끔하게"], "avoid": ["너무 러블리", "과한 히피"]},
    "힙한": {"keywords": ["텍스처", "무심한듯", "개성 있게"], "avoid": ["너무 단정"]},
    "단정한": {"keywords": ["정돈", "클린", "차분하게"], "avoid": ["과한 레이어", "과한 컬"]},
    "귀여운": {"keywords": ["가볍게", "발랄하게", "동안 무드"], "avoid": ["너무 무거운 기장"]},
    "세련된": {"keywords": ["윤곽 보정", "밸런스", "고급스럽게"], "avoid": ["산만한 텍스처"]},
    "동안 느낌": {"keywords": ["볼륨", "부드러움", "가벼운 앞머리"], "avoid": ["너무 각진 라인"]},
    "성숙한 느낌": {"keywords": ["무게감", "정제된 컬", "클래식하게"], "avoid": ["너무 짧은 기장"]},
}


# =========================
# ✅ 배포용 API Key 입력 지원 (Kakao + OpenAI)
# =========================
st.sidebar.header("🔑 API Key 입력")
st.sidebar.info("🔐 키는 서버에 저장되지 않으며, 새로고침하면 다시 입력해야 합니다.")

# Kakao Key
if "KAKAO_REST_API_KEY" not in st.session_state:
    st.session_state["KAKAO_REST_API_KEY"] = (st.secrets.get("KAKAO_REST_API_KEY", "") or "").strip()

kakao_input = st.sidebar.text_input(
    "Kakao REST API Key (필수)",
    value=st.session_state["KAKAO_REST_API_KEY"],
    type="password",
)
st.session_state["KAKAO_REST_API_KEY"] = (kakao_input or "").strip()
KAKAO_REST_API_KEY = st.session_state["KAKAO_REST_API_KEY"]

# OpenAI Key
if "OPENAI_API_KEY" not in st.session_state:
    st.session_state["OPENAI_API_KEY"] = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()

openai_input = st.sidebar.text_input(
    "OpenAI API Key (필수)",
    value=st.session_state["OPENAI_API_KEY"],
    type="password",
)
st.session_state["OPENAI_API_KEY"] = (openai_input or "").strip()
OPENAI_API_KEY = st.session_state["OPENAI_API_KEY"]


if not KAKAO_REST_API_KEY:
    st.warning("카카오 REST API Key를 사이드바에 입력해주세요.")
    st.stop()

if not OPENAI_API_KEY:
    st.warning("OpenAI API Key를 사이드바에 입력해주세요.")
    st.stop()


# =========================
# UI 카드 렌더 유틸
# =========================
def select_card(
    *,
    title: str,
    button_label: str,
    on_click_value: str,
    session_key: str,
    button_key: str,
    desc_md: str | None = None,
    image_path: str | None = None,
    img_width: int = 160,
    selected: bool = False,
) -> None:
    st.subheader(title)
    maybe_image(image_path, width=img_width)
    if desc_md:
       st.markdown(desc_md, unsafe_allow_html=True)
    btn_type = "primary" if selected else "secondary"
    if st.button(button_label, key=button_key, use_container_width=True, type=btn_type):
        st.session_state[session_key] = on_click_value
        st.rerun()


# =========================
# 얼굴형 힌트 (기본) - build_auto_terms에 사용
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


def build_auto_terms(
    *,
    app_face_shape: str | None,
    brow_shape: str | None,
    hair_type: str | None,
    current_length: str | None,
    bangs: str | None,
    mood: str | None,
    styling: str | None,
    max_terms: int = 6,
) -> List[str]:
    # 얼굴형 기반
    if not app_face_shape:
        base = ["레이어드컷", "C컬펌", "S컬펌"]
    else:
        reco_face = APP_FACE_TO_RECO_FACE.get(app_face_shape, "계란형 얼굴")
        base = FACE_SHAPE_TO_KEYWORDS.get(reco_face, []) or ["레이어드컷", "C컬펌", "S컬펌"]

    # 눈썹형(분위기 가중치) - 안정적인 힌트만 살짝
    if brow_shape in ("직선형", "각진형"):
        base = ["보브컷", "가일컷", "댄디컷"] + base
    if brow_shape in ("아치형", "둥근형"):
        base = ["C컬펌", "S컬펌", "레이어드컷"] + base

    # 앞머리 의향
    if bangs == "만들 의향 있음":
        base = base + ["시스루뱅", "풀뱅"]

    # 스타일링 난이도
    if styling == "손질 거의 안 함":
        prefer = ["볼륨매직", "매직", "다운펌", "단발", "중단발"]
        base = prefer + base

    # 현재 길이
    if current_length == "숏":
        base = ["숏컷", "투블럭", "댄디컷", "크롭컷"] + base

    # 모발 타입
    if hair_type == "곱슬":
        base = ["볼륨매직", "매직", "다운펌"] + base

    # 무드(가중치 느낌)
    if mood in ("단정한", "세련된"):
        base = ["보브컷", "레이어드컷", "볼륨매직"] + base
    if mood == "힙한":
        base = ["허쉬컷", "샤기컷", "히피펌"] + base
    if mood in ("청순", "동안 느낌"):
        base = ["C컬펌", "레이어드컷", "시스루뱅"] + base

    # 중복 제거 + 화이트리스트만
    uniq: List[str] = []
    seen = set()
    for t in base:
        if t in STYLE_TERMS and t not in seen:
            seen.add(t)
            uniq.append(t)

    return (uniq[:max_terms] if uniq else ["레이어드컷", "C컬펌", "S컬펌"])[:max_terms]


# =========================
# GPT/문자열 유틸
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


def tone_color_suggestions(tone: str) -> List[str]:
    if tone == "웜":
        return ["초코브라운", "핑크브라운", "카키브라운"]
    if tone == "쿨":
        return ["애쉬브라운", "애쉬그레이", "애쉬블루"]
    return []


# =========================
# Kakao API 유틸
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
    sort: str = "distance",  # ✅ 추가 (distance / accuracy)
) -> List[dict]:
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {
        "query": query,
        "x": str(x),
        "y": str(y),
        "radius": str(radius_m),
        "size": str(size),
        "page": str(page),
        "sort": sort,  # ✅ 적용
    }
    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("documents", [])
def strip_html(s: str) -> str:
    s = s or ""
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&nbsp;|&amp;|&quot;|&lt;|&gt;", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


@st.cache_data(show_spinner=False, ttl=3600)
def kakao_search_blog(query: str, size: int = 3, sort: str = "accuracy", page: int = 1) -> List[dict]:
    url = "https://dapi.kakao.com/v2/search/blog"
    params = {
        "query": query,
        "size": str(max(1, min(size, 50))),
        "sort": sort,  # "accuracy" or "recency"
        "page": str(max(1, min(page, 50))),
    }
    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("documents", [])


@st.cache_data(show_spinner=False, ttl=3600)
def kakao_search_web(query: str, size: int = 3, sort: str = "accuracy", page: int = 1) -> List[dict]:
    url = "https://dapi.kakao.com/v2/search/web"
    params = {
        "query": query,
        "size": str(max(1, min(size, 50))),
        "sort": sort,  # "accuracy" or "recency"
        "page": str(max(1, min(page, 50))),
    }
    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("documents", [])

# =========================
# ✅ Kakao 이미지 검색 API (추천 아래 이미지 3개씩)
# =========================
@st.cache_data(show_spinner=False, ttl=3600)
def kakao_search_image(query: str, size: int = 3, sort: str = "accuracy", page: int = 1) -> List[dict]:
    url = "https://dapi.kakao.com/v2/search/image"
    params = {
        "query": query,
        "size": str(max(1, min(size, 80))),
        "sort": sort,  # "accuracy" or "recency"
        "page": str(max(1, min(page, 50))),
    }
    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("documents", [])


def extract_style_terms_from_query(q: str, max_terms: int = 2) -> List[str]:
    raw = (q or "").replace("미용실", " ").strip()
    terms_sorted = sorted(STYLE_TERMS, key=len, reverse=True)
    picked: List[str] = []
    for t in terms_sorted:
        if t in raw and t not in picked:
            picked.append(t)
        if len(picked) >= max_terms:
            break
    return picked[:max_terms] if picked else ["레이어드컷"]


def render_3_images_for_reco_query(reco_query: str, img_width: int = 220) -> None:
    terms = extract_style_terms_from_query(reco_query, max_terms=2)
    q = f"{' '.join(terms)} 헤어스타일"  # 미용실 사진 섞임 완화

    try:
        docs = kakao_search_image(q, size=3, sort="accuracy", page=1)
    except Exception as e:
        st.caption(f"이미지 로딩 실패: {e}")
        return

    if not docs:
        st.caption("이미지 결과가 없어요.")
        return

    cols = st.columns(3, gap="small")
    for i, d in enumerate(docs[:3]):
        thumb = d.get("thumbnail_url") or d.get("image_url")
        doc_url = d.get("doc_url", "")
        with cols[i % 3]:
            if thumb:
                st.image(thumb, width=img_width)  # ✅ 폭 고정(작게)
            if doc_url:
                st.link_button("출처", doc_url)


# =========================
# 검색 fallback/merge
# =========================
def merge_places(*lists: List[dict]) -> List[dict]:
    merged = []
    seen = set()
    for lst in lists:
        for p in lst:
            key = p.get("place_url") or (
                p.get("place_name", "") + "|" + (p.get("road_address_name", "") or p.get("address_name", ""))
            )
            if key and key not in seen:
                seen.add(key)
                merged.append(p)
    return merged


def build_fallback_queries(chosen_query: str) -> List[str]:
    q = (chosen_query or "").strip()
    q_no = q.replace("미용실", "").strip()
    fallbacks = []
    if q:
        fallbacks.append(q)
    if q_no:
        fallbacks.append(q_no)
        fallbacks.append(f"{q_no} 헤어")
        fallbacks.append(f"{q_no} 헤어샵")
    fallbacks.append("미용실")

    uniq, seen = [], set()
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
    sort: str = "accuracy",  # ✅ 기본을 accuracy로
) -> Tuple[List[dict], str, int]:
    queries = build_fallback_queries(chosen_query)
    radius_try = [radius_m, min(radius_m * 2, 20000)]

    for r in radius_try:
        for q in queries:
            res1 = kakao_keyword_search(query=q, x=x, y=y, radius_m=r, size=size, page=1, sort=sort)
            res2 = kakao_keyword_search(query=q, x=x, y=y, radius_m=r, size=size, page=2, sort=sort) if res1 else []
            res = merge_places(res1, res2)
            if res:
                return res, q, r

    return [], (queries[0] if queries else chosen_query), radius_m

# =========================
# ✅ 9) GPT: 미용실 검색어 3개 + "안정적인 근거형 reason" 생성
# - 얼굴형/눈썹형 프로필 딕셔너리를 프롬프트에 제공
# =========================
def make_queries_with_openai(
    *,
    api_key: str,
    tone: str,
    face_shape: str,
    brow_shape: str,
    hair_type: str,
    length_pref: str,
    mood: str,
    current_length: str,
    bangs: str,
    styling: str,
    hint_terms: List[str],
) -> Tuple[List[str], List[str]]:
    client = OpenAI(api_key=api_key)
    allowed = STYLE_TERMS

    face_profile = FACE_PROFILE.get(face_shape, {"concerns": [], "strengths": []})
    brow_profile = BROW_PROFILE.get(brow_shape, {"concerns": [], "strengths": []})
    mood_profile = MOOD_GUIDE.get(mood, {"keywords": [], "avoid": []})

    # reason을 "정확한 표현"으로 고정시키기 위한 강한 제약
    prompt = f"""
너는 한국 헤어디자이너야.
아래 사용자 정보를 기반으로, 카카오 로컬에서 검색 가능한 "미용실 검색 키워드 3개"를 추천해줘.

[중요 규칙]
- 각 query에는 반드시 '미용실' 포함
- query는 반드시 "허용된 스타일 용어 목록"에서만 골라 조합
- 허용 목록 밖 단어 절대 금지
- (스타일용어 1~2개 + '미용실')로 간결하게
- tone({tone})은 '염색/컬러'에만 참고(염색 관련 용어는 0~1개만 허용)

[reason 작성 규칙 - 반드시 지켜]
- reason은 반드시 "한 문장" 한국어로 작성
- 아래 딕셔너리의 내용을 근거로 하되, 사용자가 선택한 얼굴형/눈썹형에 맞는 표현만 사용
- 반드시 다음 4요소를 포함:
  1) 얼굴형({face_shape})의 concerns 중 1개를 "보완"한다는 문장
  2) 눈썹형({brow_shape})의 strengths 중 1개를 "살린다"는 문장
  3) 무드({mood})의 keywords 중 1개를 반영(예: 도회적으로/깔끔하게/부드럽게)
  4) 최종 추천 스타일(허용된 스타일 용어 중 1~2개)을 포함하여 문장 끝을 "...을/를 추천"으로 마무리

[딕셔너리(고정 근거)]
- face_profile[{face_shape}]:
  concerns={json.dumps(face_profile.get("concerns", []), ensure_ascii=False)}
  strengths={json.dumps(face_profile.get("strengths", []), ensure_ascii=False)}
- brow_profile[{brow_shape}]:
  concerns={json.dumps(brow_profile.get("concerns", []), ensure_ascii=False)}
  strengths={json.dumps(brow_profile.get("strengths", []), ensure_ascii=False)}
- mood_guide[{mood}]:
  keywords={json.dumps(mood_profile.get("keywords", []), ensure_ascii=False)}
  avoid={json.dumps(mood_profile.get("avoid", []), ensure_ascii=False)}

[사용자 정보]
- tone: {tone}
- face_shape: {face_shape}
- brow_shape: {brow_shape}
- hair_type: {hair_type}
- length_preference: {length_pref}
- current_length: {current_length}
- bangs: {bangs}
- mood: {mood}
- styling_difficulty: {styling}

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

    # 부족하면 보강
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
                # reason 보강 문구도 "보완+강점+무드+추천" 형태로 고정
                mood_word = (mood_profile.get("keywords") or ["자연스럽게"])[0]
                face_concern = (face_profile.get("concerns") or ["얼굴 비율"])[0]
                brow_strength = (brow_profile.get("strengths") or ["인상"])[0]
                style_terms = extract_style_terms_from_query(q, max_terms=2)
                final_style = " ".join(style_terms[:2])
                final_r.append(f"{face_shape} 얼굴의 {face_concern}을 보완하고 {brow_shape} 눈썹의 {brow_strength}을 살리며 {mood_word} 연출에 어울리는 {final_style}을 추천")
            if len(final_q) >= 3:
                break

    # reasons 개수 맞추기
    while len(final_r) < len(final_q):
        final_r.append("선택 정보 기반 추천")

    return final_q[:3], final_r[:3]


# =========================
# 정석 RAG: 근거 청킹/수집
# =========================
def chunk_text(text: str, max_len: int = 180, max_chunks: int = 6) -> List[str]:
    s = strip_html(text or "").strip()
    if not s:
        return []
    parts = re.split(r"[|]\s*|\n+|[.?!]\s+|[。！？]\s*", s)
    chunks = []
    for p in parts:
        p = p.strip()
        if len(p) < 20:
            continue
        if len(p) > max_len:
            p = p[:max_len].rstrip() + "…"
        chunks.append(p)
        if len(chunks) >= max_chunks:
            break
    return chunks

@st.cache_data(show_spinner=False, ttl=1200)
def fetch_evidence_docs_for_place(
    place_name: str,
    area_hint: str,
    mode: str,
    tone: str,
    style_hint: str = "",   # ✅ 추가
    size_each: int = 3,     # ✅ (선택) 4→3으로 경량화
) -> List[dict]:
    """
    mode:
      - "style": 펌/컷 위주
      - "color": 염색 위주
    """
    style_hint = (style_hint or "").strip()

    if mode == "color":
        tone_hint = "애쉬" if tone == "쿨" else "브라운"
        q = f"{place_name} {area_hint} 염색 {tone_hint} 발레아쥬 옴브레 후기"
    else:
        # ✅ 사용자가 고른 스타일(추천 검색어에서 추출) 힌트를 후기 수집에 반영
        # 예: "{살롱} {지역} 레이어드컷 C컬펌 후기 펌 컷"
        if style_hint:
            q = f"{place_name} {area_hint} {style_hint} 후기 펌 컷"
        else:
            q = f"{place_name} {area_hint} 미용실 후기 펌 컷"

    blog_docs, web_docs = [], []
    try:
        blog_docs = kakao_search_blog(q, size=size_each)
    except Exception:
        blog_docs = []
    try:
        web_docs = kakao_search_web(q, size=size_each)
    except Exception:
        web_docs = []

    out = []
    for d in blog_docs:
        out.append(
            {
                "source": "blog",
                "title": strip_html(d.get("title", "")),
                "text": strip_html(d.get("contents", "")),
                "url": d.get("url", ""),
            }
        )
    for d in web_docs:
        out.append(
            {
                "source": "web",
                "title": strip_html(d.get("title", "")),
                "text": strip_html(d.get("contents", "")),
                "url": d.get("url", ""),
            }
        )
    return out[: (size_each * 2)]

def build_evidence_chunks(
    *,
    salons: List[dict],
    area_hint: str,
    tone: str,
    include_color: bool,
    chosen_query: str,            # ✅ 추가
    max_total_chunks: int = 240,
) -> List[dict]:
    evidence: List[dict] = []
    used = 0

    # ✅ 선택된 검색어에서 스타일 1~2개를 추출하여 후기 수집 쿼리에 반영
    style_terms = extract_style_terms_from_query(chosen_query, max_terms=2)
    style_hint = " ".join(style_terms).strip()

    for s_idx, p in enumerate(salons, start=1):
        name = p.get("place_name", "") or ""
        if not name:
            continue

        # style docs (✅ style_hint 반영)
        style_docs = fetch_evidence_docs_for_place(
            name,
            area_hint,
            mode="style",
            tone=tone,
            style_hint=style_hint,
            size_each=3,
        )
        for d_idx, d in enumerate(style_docs, start=1):
            for c_idx, chunk in enumerate(chunk_text(f"{d.get('title','')} - {d.get('text','')}"), start=1):
                evidence.append(
                    {
                        "chunk_id": f"S{s_idx}_STYLE_{d_idx}_{c_idx}",
                        "salon_name": name,
                        "source": d.get("source", "web"),
                        "title": d.get("title", ""),
                        "url": d.get("url", ""),
                        "text": chunk,
                    }
                )
                used += 1
                if used >= max_total_chunks:
                    return evidence

        if include_color:
            color_docs = fetch_evidence_docs_for_place(
                name,
                area_hint,
                mode="color",
                tone=tone,
                style_hint="",     # ✅ 컬러는 style_hint 불필요
                size_each=3,
            )
            for d_idx, d in enumerate(color_docs, start=1):
                for c_idx, chunk in enumerate(chunk_text(f"{d.get('title','')} - {d.get('text','')}"), start=1):
                    evidence.append(
                        {
                            "chunk_id": f"S{s_idx}_COLOR_{d_idx}_{c_idx}",
                            "salon_name": name,
                            "source": d.get("source", "web"),
                            "title": d.get("title", ""),
                            "url": d.get("url", ""),
                            "text": chunk,
                        }
                    )
                    used += 1
                    if used >= max_total_chunks:
                        return evidence

    return evidence
def fallback_rank_top3(salons: List[dict], chosen_query: str) -> dict:
    style_terms = extract_style_terms_from_query(chosen_query, max_terms=2)
    terms = [t for t in style_terms if t]

    def score(s: dict) -> int:
        name = (s.get("place_name", "") or "").lower()
        cat = (s.get("category_name", "") or "").lower()
        text = name + " " + cat

        hit = 0
        for t in terms:
            if t.lower() in text:
                hit += 3

        # (선택) 정보가 많을수록 가산점
        if s.get("road_address_name") or s.get("address_name"):
            hit += 1
        if s.get("phone"):
            hit += 1

        # (선택) 거리 타이브레이커를 쓰고 싶으면 아래처럼 아주 약하게
        # dist = int(s.get("distance") or 10**9)
        # hit += max(0, 3 - min(3, dist // 1000))

        return hit

    ranked = sorted(salons, key=score, reverse=True)[:3]

    out = {"top_salons": []}
    for i, s in enumerate(ranked, start=1):
        out["top_salons"].append({
            "rank": i,
            "name": s.get("place_name", ""),
            "why": "후기/스니펫 근거가 부족해 메타데이터(상호/카테고리/기본정보) 기반으로 우선 추천했어요.",
            "best_for": ["후기 근거 부족", "1차 후보 중 우선 추천", "추가 검색 권장"],
            "evidence_ids": [],
        })
    return out

# =========================
# 정석 RAG: 최종 추천(장윤주 페르소나 + 근거 인용 강제)
# =========================
JYJ_SYSTEM_PROMPT = """
당신은 패션에 능통하며 미적 감각이 특출난 모델 장윤주의 페르소나를 가집니다.
헤어스타일을 추천할 때 장윤주의 페르소나를 가지고 말투에 유의하여 추천해주세요.
헤어스타일 추천의 근거나 이유를 대서 논리적으로 답변하세요.

[근거 규칙]
- 입력으로 제공된 EVIDENCE(후기/스니펫) 내용에 있는 사실만 말한다.
- EVIDENCE에 없는 내용은 추측/상상하지 말고 "정보 부족"이라고 말한다.
- 최종 추천은 반드시 EVIDENCE의 chunk_id를 2~3개 인용해서 근거를 제시한다.
- evidence_ids는 반드시 해당 미용실(salon_name)과 일치하는 chunk_id만 사용한다.
- 출력은 반드시 JSON만 출력한다.

[추가 랭킹 규칙 - 매우 중요]
- 거리는 순위 기준이 아니다. (가까움/먼함을 근거로 추천하면 안 된다.)
- USER_PROFILE과 EVIDENCE에서 드러나는 '스타일 적합성/만족도/전문성'을 최우선으로 순위를 정한다.
- 동점일 때만, 주소의 접근성(대략적) 정도를 아주 약하게 타이브레이커로 고려할 수 있다.
""".strip()


def final_rank_with_rag_openai(
    *,
    api_key: str,
    user_profile: dict,
    salons: List[dict],
    evidence_chunks: List[dict],
    top_k: int = 3,
) -> dict:
    client = OpenAI(api_key=api_key)

    salons_payload = []
    for s in salons:
        salons_payload.append(
        {
            "name": s.get("place_name", ""),
            # "distance_m": s.get("distance", ""),  # ✅ 제거: 모델에 거리정보 제공하지 않음
            "address": s.get("road_address_name", "") or s.get("address_name", ""),
            "kakao_url": s.get("place_url", ""),
        }
    )

    prompt = f"""
[USER_PROFILE] {json.dumps(user_profile, ensure_ascii=False)}

[SALONS] {json.dumps(salons_payload, ensure_ascii=False)}

[EVIDENCE] {json.dumps(evidence_chunks, ensure_ascii=False)}

당신의 작업:
- SALONS 중에서 USER_PROFILE에 가장 잘 맞는 미용실 {top_k}개를 추천하라.
- 순위는 반드시 EVIDENCE 기반의 '원하는 스타일/시술 적합성, 만족도, 전문성 언급'을 최우선으로 한다.
- 거리는 순위 기준이 아니다. (가까움/먼함을 이유로 랭킹을 세우지 말라.)
- 각 추천마다 why(장윤주 페르소나 말투) + best_for(핵심 포인트 2~4개) + evidence_ids(2~3개) 제공
- 근거가 부족하면 why에 "정보 부족"을 명시하고 evidence_ids는 빈 배열로 둔다.

출력(JSON):
{{
  "top_salons": [
    {{
      "rank": 1,
      "name": "...",
      "why": "...",
      "best_for": ["...","..."],
      "evidence_ids": ["S1_STYLE_1_2","S1_COLOR_2_1"]
    }}
  ]
}}
""".strip()

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": JYJ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw = safe_json_extract(resp.choices[0].message.content or "")
    return json.loads(raw)


# =========================
# 1) 선택 UI
# =========================
STATE_KEYS = (
    "tone",
    "face_shape",
    "brow_shape",
    "hair_type",
    "length_pref",
    "mood",
    "current_length",
    "bangs",
    "styling",
)

for k in STATE_KEYS:
    if k not in st.session_state:
        st.session_state[k] = None

steps_done = sum(1 for k in STATE_KEYS if st.session_state[k] is not None)
st.progress(steps_done / len(STATE_KEYS))


# ---- 1) tone
st.header("1) 웜톤 / 쿨톤 선택")
tone_cols = st.columns(2, gap="large")
with tone_cols[0]:
    select_card(
        title="웜톤",
        image_path=OPTIONAL_IMAGES.get("웜"),
        desc_md="\n1. 팔목 혈관이 **초록빛**\n2. 악세사리로 **골드/로즈 골드**가 잘 어울림\n3. 피부에 **노란기**가 많음",
        button_label="✨ 웜톤",
        on_click_value="웜",
        session_key="tone",
        button_key="btn_tone_warm",
        img_width=90,
        selected=(st.session_state["tone"] == "웜"),
    )
with tone_cols[1]:
    select_card(
        title="쿨톤",
        image_path=OPTIONAL_IMAGES.get("쿨"),
        desc_md="\n1. 팔목 혈관이 **파란빛**\n2. 악세사리로 **실버**가 잘 어울림\n3. 피부에 **붉은기**가 많음",
        button_label="✨ 쿨톤",
        on_click_value="쿨",
        session_key="tone",
        button_key="btn_tone_cool",
        img_width=90,
        selected=(st.session_state["tone"] == "쿨"),
    )

if st.button("tone 초기화", key="reset_tone", type="secondary"):
    st.session_state["tone"] = None
    st.rerun()
    

st.divider()


# ---- 2) face
st.header("2) 얼굴형 선택")
FACE_CHOICES = [
    ("계란형", OPTIONAL_IMAGES.get("계란형"), "광대 X, 턱 X<br><strong>**광대와 턱 골격이 이상적이고 돌출이 적음**</strong>"),
    ("마름모형", OPTIONAL_IMAGES.get("마름모형"), "광대 O, 턱 X<br><strong>**옆턱 골격은 없는데 광대만 부각됨**</strong>"),
    ("하트형", OPTIONAL_IMAGES.get("하트형"), "광대 O, 턱 △<br><strong>**광대가 더 넓고 강하게 느껴짐**</strong>"),
    ("땅콩형", OPTIONAL_IMAGES.get("땅콩형"), "광대 O, 턱 O<br><strong>**광대/턱 골격이 모두 있고 너비가 비슷함**</strong>"),
    ("육각형", OPTIONAL_IMAGES.get("육각형"), "광대 X, 턱 O<br><strong>**턱 골격이 있고 광대는 덜 튀어나옴**</strong>"),
    ("둥근형", OPTIONAL_IMAGES.get("둥근형"), "광대 X, 턱 X<br><strong>**얼굴 윤곽이 부드럽고 살이 도드라짐**</strong>"),
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
                button_label=f"✨ {name}",
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


# ---- 3) brow (사용자가 이미 갖고 있던 코드 스타일 유지)
st.header("3) 눈썹 모양 선택")
BROW_CHOICES = [
    ("아치형", "아치형.png"),
    ("직선형", "직선형.png"),
    ("각진형", "각진형.png"),
    ("둥근형", "둥근형(눈썹).png"),
]
brow_rows = [BROW_CHOICES[:2], BROW_CHOICES[2:]]
for r_i, r in enumerate(brow_rows):
    cols = st.columns(2, gap="large")
    for col, (name, img) in zip(cols, r):
        with col:
            select_card(
                title=name,
                image_path=img,
                button_label=f"✨ {name}",
                on_click_value=name,
                session_key="brow_shape",
                button_key=f"btn_brow_{r_i}_{name}",
                img_width=80,
                selected=(st.session_state["brow_shape"] == name),
            )

if st.button("brow_shape 초기화", key="reset_brow", type="secondary"):
    st.session_state["brow_shape"] = None
    st.rerun()

st.divider()


# ---- 4) 모발 타입
st.header("4) 모발 타입 선택")
hair_cols = st.columns(2, gap="large")
with hair_cols[0]:
    select_card(
        title="직모",
        image_path=OPTIONAL_IMAGES.get("직모"),
        button_label="✨ 직모",
        on_click_value="직모",
        session_key="hair_type",
        button_key="btn_hair_straight",
        img_width=80,
        selected=(st.session_state["hair_type"] == "직모"),
    )
with hair_cols[1]:
    select_card(
        title="곱슬",
        image_path=OPTIONAL_IMAGES.get("곱슬"),
        button_label="✨ 곱슬",
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


# ---- 5) 기장 선호도
st.header("5) 기장 선호도 선택")
LENGTH_PREF_CHOICES = [
    ("짧게", "단발/숏 선호"),
    ("중간", "중단발 선호"),
    ("길게", "장발/롱 선호"),
]
cols = st.columns(3, gap="large")
for col, (name, desc) in zip(cols, LENGTH_PREF_CHOICES):
    with col:
        select_card(
            title=name,
            image_path=None,
            desc_md=desc,
            button_label=f"✨ {name}",
            on_click_value=name,
            session_key="length_pref",
            button_key=f"btn_lenpref_{name}",
            img_width=1,
            selected=(st.session_state["length_pref"] == name),
        )

if st.button("length_pref 초기화", key="reset_lenpref", type="secondary"):
    st.session_state["length_pref"] = None
    st.rerun()

st.divider()


# ---- 6) 무드
st.header("6) 원하는 이미지/무드 선택")
MOOD_CHOICES = ["청순", "러블리", "힙한", "단정한", "시크", "세련된"]
mood_cols = st.columns(3, gap="large")
for i, m in enumerate(MOOD_CHOICES):
    with mood_cols[i % 3]:
        select_card(
            title=m,
            image_path=None,
            desc_md=None,
            button_label=f"✨ {m}",
            on_click_value=m,
            session_key="mood",
            button_key=f"btn_mood_{m}",
            img_width=1,
            selected=(st.session_state["mood"] == m),
        )

if st.button("mood 초기화", key="reset_mood", type="secondary"):
    st.session_state["mood"] = None
    st.rerun()

st.divider()


# ---- 7) 현재 머리 길이
st.header("7) 현재 머리 길이 선택")
CUR_LEN_CHOICES = [("숏", "짧은 길이"), ("단발", "턱~목선"), ("중단발", "어깨선"), ("장발", "어깨 아래")]
cols = st.columns(4, gap="large")
for col, (name, desc) in zip(cols, CUR_LEN_CHOICES):
    with col:
        select_card(
            title=name,
            image_path=None,
            desc_md=desc,
            button_label=f"✨ {name}",
            on_click_value=name,
            session_key="current_length",
            button_key=f"btn_curlen_{name}",
            img_width=1,
            selected=(st.session_state["current_length"] == name),
        )

if st.button("current_length 초기화", key="reset_curlen", type="secondary"):
    st.session_state["current_length"] = None
    st.rerun()

st.divider()


# ---- 8) 앞머리 유무
st.header("8) 앞머리 유무 선택")
BANGS_CHOICES = [("앞머리 있음", "앞머리 있는 스타일 추구"), ("앞머리 없음","앞머리 없는 스타일 추구"), ("앞머리 만들 의향 있음","앞머리 도전 가능")]
cols = st.columns(3, gap="large")
for col, (name, desc) in zip(cols, BANGS_CHOICES):
    with col:
        select_card(
            title=name,
            image_path=None,
            desc_md=desc,
            button_label=f"✨ {name}",
            on_click_value=name,
            session_key="bangs",
            button_key=f"btn_bangs_{name}",
            img_width=1,
            selected=(st.session_state["bangs"] == name),
        )

if st.button("bangs 초기화", key="reset_bangs", type="secondary"):
    st.session_state["bangs"] = None
    st.rerun()

st.divider()


# ---- 9) 스타일링 난이도
st.header("9) 스타일링 난이도 선호")
STYLING_CHOICES = [
    ("스타일링 거의 안 함", "드라이/고데기 거의 X"),
    ("보통의 스타일링", "간단 드라이/고데기 사용"),
    ("고급 스타일링 가능", "드라이/고데기 +헤어제품 사용도 가능"),
]
cols = st.columns(3, gap="large")
for col, (name, desc) in zip(cols, STYLING_CHOICES):
    with col:
        select_card(
            title=name,
            image_path=None,
            desc_md=desc,
            button_label=f"✨ {name}",
            on_click_value=name,
            session_key="styling",
            button_key=f"btn_styling_{name}",
            img_width=1,
            selected=(st.session_state["styling"] == name),
        )

if st.button("styling 초기화", key="reset_styling", type="secondary"):
    st.session_state["styling"] = None
    st.rerun()

st.divider()


# =========================
# 10) GPT 추천 키워드 3개 + 이미지 + 근거(reason)
# =========================
st.header("10) 최종 추천 헤어스타일 + 염색 컬러")

debug_ui = st.toggle("디버그(선택값 표시)", value=False)

tone = st.session_state["tone"]
face_shape = st.session_state["face_shape"]
brow_shape = st.session_state["brow_shape"]
hair_type = st.session_state["hair_type"]
length_pref = st.session_state["length_pref"]
mood = st.session_state["mood"]
current_length = st.session_state["current_length"]
bangs = st.session_state["bangs"]
styling = st.session_state["styling"]

if debug_ui:
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("tone", tone or "-")
    a2.metric("face_shape", face_shape or "-")
    a3.metric("brow_shape", brow_shape or "-")
    a4.metric("hair_type", hair_type or "-")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("length_pref", length_pref or "-")
    b2.metric("mood", mood or "-")
    b3.metric("current_length", current_length or "-")
    b4.metric("bangs", bangs or "-")
    c1, _, _, _ = st.columns(4)
    c1.metric("styling", styling or "-")

all_selected = all([tone, face_shape, brow_shape, hair_type, length_pref, mood, current_length, bangs, styling])

hint_terms = build_auto_terms(
    app_face_shape=face_shape,
    brow_shape=brow_shape,
    hair_type=hair_type,
    current_length=current_length,
    bangs=bangs,
    mood=mood,
    styling=styling,
)

if "gpt_queries" not in st.session_state:
    st.session_state["gpt_queries"] = []
if "gpt_reasons" not in st.session_state:
    st.session_state["gpt_reasons"] = []

gpt_btn = st.button(
    "✨🪞거울에게 물어보기🪞✨",
    key="btn_make_gpt_queries",
    use_container_width=True,
    disabled=(not all_selected),
)

if gpt_btn:
    if not all_selected:
        st.error("tone/face_shape/brow_shape/hair_type/length_pref/mood/current_length/bangs/styling 를 모두 선택해주세요.")
    else:
        try:
            with st.spinner("🪞거울🪞이 헤어스타일 추천 3개와 근거를 생성하는 중..."):
                qs, rs = make_queries_with_openai(
                    api_key=OPENAI_API_KEY,
                    tone=tone,
                    face_shape=face_shape,
                    brow_shape=brow_shape,
                    hair_type=hair_type,
                    length_pref=length_pref,
                    mood=mood,
                    current_length=current_length,
                    bangs=bangs,
                    styling=styling,
                    hint_terms=hint_terms,
                )
                st.session_state["gpt_queries"] = qs
                st.session_state["gpt_reasons"] = rs
        except Exception as e:
            st.error(f"GPT 호출 오류: {e}")

def display_label(q: str) -> str:
    return re.sub(r"\s+", " ", (q or "").replace("미용실", "").strip())

chosen_query = ""
chosen_idx = 0

if st.session_state["gpt_queries"]:
    labels = [f"🪞추천 {i+1}: {display_label(q)}" for i, q in enumerate(st.session_state["gpt_queries"])]

    chosen_label = st.radio(
        "아래 추천 3개 중 하나를 선택하면 해당 검색어로 미용실 검색을 진행합니다.",
        options=labels,
        index=0,
        key="auto_query_radio",
    )
    chosen_idx = labels.index(chosen_label)
    chosen_query = st.session_state["gpt_queries"][chosen_idx]

    st.caption("※ 아래 이미지는 카카오 이미지 검색 결과이며 예시용입니다. 각 이미지의 출처를 확인하세요.")

    # ✅ 각 추천별: 제목 + 근거 + 이미지(3장)
    for i, q in enumerate(st.session_state["gpt_queries"], start=1):
        st.markdown(f"### 🪞추천 {i}: {display_label(q)}")
        r = st.session_state["gpt_reasons"][i - 1] if (i - 1) < len(st.session_state["gpt_reasons"]) else ""
        if r:
            st.info(f"🪞 추천 근거: {r}")
        render_3_images_for_reco_query(q,img_width=200)

else:
    st.warning("아직 🪞거울🪞이 헤어스타일을 추천하지 않았어요. 위 버튼을 눌러 생성해주세요.")

tone_now = st.session_state["tone"]
colors = []
if tone_now:
    colors = tone_color_suggestions(tone_now)
    if colors:
        st.subheader("🎨 톤 기반 염색 컬러 추천")

color_text = " / ".join(colors) if colors else ""

st.markdown(
    f"""
    <div style="font-size:22px; font-weight:700; margin-top:5px;">
        {color_text}
    </div>
    """,
    unsafe_allow_html=True
)
st.divider()

# ✅ [수정] 11) 후보군 검색 → 근거 수집 → 최종 추천(정석 RAG)
# - RAG 옵션(topn_for_rag, include_color_evidence) UI 숨김 + 값 고정
# - 검색 결과 옵션(auto_fallback, result_size) UI 숨김 + 값 고정
# - 반경은 3km 기본 + 필요 시 확장(앞서 제안한 UX 유지)

st.header("11) 미용실 추천")

address = st.text_input("내 위치(주소)를 입력해주세요 (예: 서울시 서대문구 연세로 50)", key="input_address")

# -------------------------
# ✅ 고정값(디자인 개선용)
# -------------------------
BASE_RADIUS = 3000              # 기본 3km 고정
TOPN_FOR_RAG_FIXED = 40         # 1) RAG 후보 N 고정(앱에 숨김)
INCLUDE_COLOR_EVIDENCE_FIXED = True  # (원하면 False로 변경 가능, 숨김)
AUTO_FALLBACK_FIXED = True      # 자동 완화 고정(앱에 숨김)
RESULT_SIZE_FIXED = 15          # 2) Kakao Local size 고정(앱에 숨김)

# -------------------------
# ✅ 반경 UX: 기본 3km + 필요 시 확장
# -------------------------
st.subheader("검색 반경")
st.write(f"기본 검색 반경: **{BASE_RADIUS/1000:.0f}km**")

RADIUS_PRESETS = [
    ("기본(3km)", 3000),
    ("5km", 5000),
    ("8km", 8000),
    ("10km", 10000),
]

if "radius_choice" not in st.session_state:
    st.session_state["radius_choice"] = BASE_RADIUS

with st.expander("검색 반경을 늘리고 싶어요"):
    preset_labels = [x[0] for x in RADIUS_PRESETS]
    preset_values = [x[1] for x in RADIUS_PRESETS]
    current_idx = preset_values.index(st.session_state["radius_choice"]) if st.session_state["radius_choice"] in preset_values else 0

    chosen_label = st.radio(
        "원하는 반경을 선택하세요",
        options=preset_labels,
        index=current_idx,
        horizontal=True,
        key="radius_preset_radio",
    )
    st.session_state["radius_choice"] = preset_values[preset_labels.index(chosen_label)]

radius = st.session_state["radius_choice"]

st.caption("※ 기본은 3km로 검색하며, 사용자가 원할 시 확장할 수 있어요.")

# -------------------------
# ✅ UI에서 사라진 옵션들(내부 고정)
# -------------------------
topn_for_rag = TOPN_FOR_RAG_FIXED
include_color_evidence = INCLUDE_COLOR_EVIDENCE_FIXED
auto_fallback = AUTO_FALLBACK_FIXED
result_size = RESULT_SIZE_FIXED
find_btn = st.button("📍 최적의 미용실 검색", key="btn_find_salon", use_container_width=True)

if find_btn:
    if not all_selected:
        st.error("tone/face_shape/brow_shape/hair_type/length_pref/mood/current_length/bangs/styling 를 모두 선택해주세요.")
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

        with st.spinner("1차: Kakao Local 후보군 검색 중..."):
            if auto_fallback:
                base_results, used_q, used_r = search_salons_with_fallback(
                    chosen_query=chosen_query,
                    x=x,
                    y=y,
                    radius_m=radius,
                    size=result_size,
                    sort="accuracy",
                )
            else:
                base_results = kakao_keyword_search(
                    query=chosen_query, x=x, y=y, radius_m=radius, size=result_size, page=1, sort="accuracy"
                )
                used_q, used_r = chosen_query, radius

        # ✅ 결과 없으면 반경 확장 재검색
        if not base_results:
            st.warning(f"{radius/1000:.0f}km 이내에서 검색 결과가 없어요. 반경을 늘려 다시 찾아볼까요?")

            c1, c2, c3 = st.columns(3)
            with c1:
                retry_5 = st.button("🔎 5km로 다시 검색", use_container_width=True)
            with c2:
                retry_8 = st.button("🔎 8km로 다시 검색", use_container_width=True)
            with c3:
                retry_10 = st.button("🔎 10km로 다시 검색", use_container_width=True)

            retry_radius = None
            if retry_5:
                retry_radius = 5000
            elif retry_8:
                retry_radius = 8000
            elif retry_10:
                retry_radius = 10000

            if retry_radius is None:
                st.stop()

            st.session_state["radius_choice"] = retry_radius
            radius = retry_radius

            with st.spinner(f"{radius/1000:.0f}km로 후보군을 다시 검색 중..."):
                if auto_fallback:
                    base_results, used_q, used_r = search_salons_with_fallback(
                        chosen_query=chosen_query,
                        x=x,
                        y=y,
                        radius_m=radius,
                        size=result_size,
                        sort="accuracy",
                    )
                else:
                    base_results = kakao_keyword_search(
                        query=chosen_query, x=x, y=y, radius_m=radius, size=result_size, page=1, sort="accuracy"
                    )
                    used_q, used_r = chosen_query, radius

            if not base_results:
                st.error(f"{radius/1000:.0f}km로도 결과가 없어요. 검색어를 바꾸거나 주소를 더 구체적으로 입력해 주세요.")
                st.stop()

        st.success(f"후보군 검색 성공: '{used_q}' / 반경 {used_r}m / 후보 {len(base_results)}개")

        # ✅ 후보 N개 고정
        candidates = base_results[:topn_for_rag]
        area_hint = " ".join(address.strip().split()[:3]) or address.strip()

        with st.spinner("정보 수집/청킹 중..."):
            evidence_chunks = build_evidence_chunks(
                salons=candidates,
                area_hint=area_hint,
                tone=tone,
                include_color=include_color_evidence,
                chosen_query=chosen_query,
                max_total_chunks=240,
            )

        if not evidence_chunks:
            st.warning("근거 수집이 부족해요(검색 결과/스니펫이 비어 있음). 그래도 후보 리스트는 보여줄게요.")
        else:
            st.info(f"근거 청크 수집 완료: {len(evidence_chunks)}개 (상한 240)")

        # 지도
        map_points = [
            {"lat": float(r["y"]), "lon": float(r["x"])}
            for r in base_results
            if r.get("x") and r.get("y")
        ]
        if map_points:
            st.map(map_points, zoom=13)

        # ✅ 최종 RAG 추천 (여기부터도 반드시 if find_btn 블록 안!)
        user_profile = {
            "tone": tone,
            "face_shape": face_shape,
            "brow_shape": brow_shape,
            "hair_type": hair_type,
            "length_preference": length_pref,
            "mood": mood,
            "current_length": current_length,
            "bangs": bangs,
            "styling_difficulty": styling,
        }

        st.subheader("🏆 최종 추천 Top 3")

        with st.spinner("최종 추천을 생성 중..."):
            if evidence_chunks:
                rag_result = final_rank_with_rag_openai(
                    api_key=OPENAI_API_KEY,
                    user_profile=user_profile,
                    salons=candidates,
                    evidence_chunks=evidence_chunks,
                    top_k=3,
                )
            else:
                rag_result = fallback_rank_top3(candidates, chosen_query)

        ev_by_id = {e["chunk_id"]: e for e in evidence_chunks} if evidence_chunks else {}

        if rag_result and isinstance(rag_result, dict):
            top_salons = rag_result.get("top_salons", [])
            if not isinstance(top_salons, list) or not top_salons:
                st.warning("최종 추천 결과가 비어 있어요. 아래 후보 리스트를 참고해주세요.")
            else:
                for item in top_salons:
                    if not isinstance(item, dict):
                        continue

                    rank = item.get("rank", "")
                    name = item.get("name", "")
                    why = item.get("why", "")
                    best_for = item.get("best_for", [])
                    evidence_ids = item.get("evidence_ids", [])

                    st.markdown(f"### {rank}위. {name}")
                    if best_for and isinstance(best_for, list):
                        st.write("- **잘 맞는 포인트:**", " / ".join([str(x) for x in best_for][:6]))
                    if why:
                        st.write("- **추천 이유:**", why)

                    matched = next((s for s in candidates if (s.get("place_name", "") == name)), None)
                    if matched:
                        dist = matched.get("distance", "")
                        addr = matched.get("road_address_name", "") or matched.get("address_name", "")
                        url = matched.get("place_url", "")
                        if dist:
                            st.write(f"- 거리: **{dist}m**")
                        if addr:
                            st.write(f"- 주소: {addr}")
                        if url:
                            st.write(f"- 카카오맵: {url}")

                    with st.expander("근거 보기 (EVIDENCE 인용)"):
                        if not evidence_ids:
                            st.write("정보 부족: 인용할 근거가 충분하지 않았습니다.")
                        else:
                            for eid in evidence_ids:
                                ev = ev_by_id.get(eid)
                                if not ev:
                                    st.write(f"- {eid}: (근거 청크를 찾지 못함)")
                                    continue
                                src = ev.get("source", "")
                                title = ev.get("title", "")
                                url = ev.get("url", "")
                                text = ev.get("text", "")
                                header = f"[{eid}] ({src})"
                                if title:
                                    header += f" {title}"
                                st.markdown(f"- **{header}**")
                                if url:
                                    st.markdown(f"  - 링크: {url}")
                                st.markdown(f"  - 내용: {text}")

        st.divider()

        # 후보 리스트(전체)
        st.subheader("후보 미용실 리스트 (Kakao Local)")
        for i, r in enumerate(base_results, start=1):
            name = r.get("place_name", "")
            road = r.get("road_address_name", "") or r.get("address_name", "")
            phone = r.get("phone", "")
            dist = r.get("distance", "")
            url = r.get("place_url", "")

            st.markdown(f"### {i}. {name}")
            if dist:
                st.write(f"- 거리: **{dist}m**")
            if road:
                st.write(f"- 주소: {road}")
            if phone:
                st.write(f"- 전화: {phone}")
            if url:
                st.write(f"- 카카오맵: {url}")

    except Exception as e:
        st.error(f"오류: {e}")

st.divider()


if st.button("전체 선택/결과 초기화", key="reset_all", type="secondary"):
    for k in STATE_KEYS:
        st.session_state[k] = None
    st.session_state["gpt_queries"] = []
    st.session_state["gpt_reasons"] = []
    st.rerun()
