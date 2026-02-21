-import streamlit as st
-import streamlit.components.v1 as components
-from openai import OpenAI
+from __future__ import annotations
+
 import json
-import pandas as pd
-import requests
 import re
-from datetime import datetime
-from urllib.parse import quote_plus
-from duckduckgo_search import DDGS
-
-
-ENTRY_REQUIREMENTS_BY_COUNTRY = {
-    "일본": {
-        "visa": "90일 이하 무비자",
-        "stay": "최대 90일 체류 가능",
-        "eta": "별도 ESTA/ETA 불필요",
-        "passport": "입국 시 유효한 전자여권 필요 (통상 6개월 이상 권장)",
-    },
-    "중국": {
-        "visa": "일반적으로 비자 필요 (경유/특정 정책 예외 가능)",
-        "stay": "비자 종류에 따라 상이",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "일반적으로 6개월 이상 유효기간 필요",
-    },
-    "대만": {
-        "visa": "90일 이하 무비자",
-        "stay": "최대 90일",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "입국 시 6개월 이상 권장",
-    },
-    "홍콩": {
-        "visa": "90일 이하 무비자",
-        "stay": "최대 90일",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "입국 시 1개월+ 체류기간을 초과하는 유효기간 권장",
-    },
-    "베트남": {
-        "visa": "45일 이하 무비자",
-        "stay": "최대 45일",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "일반적으로 6개월 이상 유효기간 필요",
-    },
-    "태국": {
-        "visa": "무비자 입국 가능",
-        "stay": "정책에 따라 60일 내외 (변동 가능)",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "일반적으로 6개월 이상 유효기간 필요",
-    },
-    "싱가포르": {
-        "visa": "90일 이하 무비자",
-        "stay": "최대 90일",
-        "eta": "전자입국신고(SG Arrival Card) 필요",
-        "passport": "입국 시 6개월 이상 유효기간 필요",
-    },
-    "말레이시아": {
-        "visa": "90일 이하 무비자",
-        "stay": "최대 90일",
-        "eta": "전자입국신고(MDAC) 필요",
-        "passport": "입국 시 6개월 이상 유효기간 필요",
-    },
-    "미국": {
-        "visa": "관광 목적 90일 이하는 ESTA 승인 시 무비자",
-        "stay": "최대 90일 (ESTA 기준)",
-        "eta": "ESTA 필수",
-        "passport": "전자여권 필요 (체류기간 동안 유효)",
-    },
-    "캐나다": {
-        "visa": "단기 체류 시 비자 면제",
-        "stay": "통상 최대 6개월",
-        "eta": "eTA 필수 (항공 입국 시)",
-        "passport": "입국 시 유효한 여권 필요",
-    },
-    "영국": {
-        "visa": "단기 방문 무비자",
-        "stay": "최대 6개월",
-        "eta": "ETA 필요",
-        "passport": "체류기간 동안 유효한 여권 필요",
-    },
-    "프랑스": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "독일": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "이탈리아": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "스페인": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "포르투갈": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "네덜란드": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "크로아티아": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "아이슬란드": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "튀르키예": {
-        "visa": "90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "입국일 기준 150일 이상 권장",
-    },
-    "아랍에미리트": {
-        "visa": "90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "일반적으로 6개월 이상 유효기간 필요",
-    },
-    "호주": {
-        "visa": "비자 필요",
-        "stay": "승인 비자 조건에 따름",
-        "eta": "ETA 또는 eVisitor 사전 신청 필요",
-        "passport": "체류기간 동안 유효한 전자여권 필요",
-    },
-    "뉴질랜드": {
-        "visa": "90일 이하 무비자",
-        "stay": "최대 90일",
-        "eta": "NZeTA 필수",
-        "passport": "출국일 기준 3개월 이상 유효기간 필요",
-    },
-    "몽골": {
-        "visa": "90일 이하 무비자",
-        "stay": "최대 90일",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "일반적으로 6개월 이상 유효기간 필요",
-    },
-    "라오스": {
-        "visa": "무비자 입국 가능",
-        "stay": "통상 30일 내외 (변동 가능)",
-        "eta": "전자비자(eVisa) 선택 가능",
-        "passport": "일반적으로 6개월 이상 유효기간 필요",
-    },
-    "이집트": {
-        "visa": "비자 필요",
-        "stay": "비자 조건에 따름",
-        "eta": "e-Visa 사전 신청 또는 도착비자 가능",
-        "passport": "일반적으로 6개월 이상 유효기간 필요",
-    },
-    "필리핀": {
-        "visa": "30일 이하 무비자",
-        "stay": "최대 30일",
-        "eta": "eTravel 등록 필요",
-        "passport": "입국일 기준 6개월 이상 유효기간 필요",
-    },
-    "인도네시아": {
-        "visa": "단기 관광 시 도착비자(VOA) 또는 e-VOA",
-        "stay": "통상 최대 30일 (연장 가능)",
-        "eta": "전자 세관신고(e-CD) 등 입국 전 절차 확인 권장",
-        "passport": "입국일 기준 6개월 이상 유효기간 필요",
-    },
-    "인도": {
-        "visa": "비자 필요",
-        "stay": "승인 비자 조건에 따름",
-        "eta": "e-Visa 사전 신청 가능",
-        "passport": "입국일 기준 6개월 이상 유효기간 필요",
-    },
-    "스위스": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "오스트리아": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "체코": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "헝가리": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "핀란드": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "노르웨이": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "덴마크": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "벨기에": {
-        "visa": "쉥겐 90일 이하 무비자",
-        "stay": "180일 중 최대 90일",
-        "eta": "ESTA/ETA 불필요 (ETIAS 시행 시 변경 가능)",
-        "passport": "출국예정일 기준 3개월 이상 + 발급 후 10년 이내",
-    },
-    "아일랜드": {
-        "visa": "단기 방문 무비자",
-        "stay": "통상 최대 90일",
-        "eta": "향후 ETA 시행 가능, 최신 공지 확인 필요",
-        "passport": "체류기간 동안 유효한 여권 필요",
-    },
-    "멕시코": {
-        "visa": "무비자 입국 가능",
-        "stay": "통상 최대 180일 (심사관 재량)",
-        "eta": "ESTA/ETA 불필요",
-        "passport": "체류기간 동안 유효한 여권 필요",
-    },
-}
-
+from collections import Counter
+from pathlib import Path
+from typing import Dict, List, Tuple
 
-REPRESENTATIVE_FOOD_BY_DESTINATION = {
-    "일본": "라멘",
-    "오사카": "타코야키",
-    "도쿄": "스시",
-    "중국": "샤오룽바오",
-    "대만": "우육면",
-    "홍콩": "딤섬",
-    "베트남": "쌀국수",
-    "태국": "팟타이",
-    "싱가포르": "칠리 크랩",
-    "미국": "바비큐",
-    "프랑스": "크루아상",
-    "이탈리아": "피자",
-    "스페인": "빠에야",
-    "튀르키예": "케밥",
-    "호주": "미트파이",
-    "멕시코": "타코",
-}
+import requests
+import streamlit as st
+from openai import OpenAI
 
 
-ZONE_CLIMATE_STATS = {
-    "열대몬순": {
-        "temp": [27, 28, 29, 30, 30, 29, 29, 29, 29, 29, 28, 27],
-        "rain": [20, 30, 50, 90, 220, 180, 170, 190, 300, 240, 80, 30],
-        "rainy_season": [5, 6, 7, 8, 9, 10],
-        "typhoon_season": [],
-        "notes": "스콜성 소나기가 잦아 우산/방수 신발이 유용합니다.",
-    },
-    "동아시아해양": {
-        "temp": [6, 7, 11, 16, 21, 24, 28, 29, 25, 20, 14, 8],
-        "rain": [55, 60, 95, 120, 135, 180, 210, 190, 170, 120, 85, 55],
-        "rainy_season": [6, 7],
-        "typhoon_season": [8, 9, 10],
-        "notes": "장마/태풍 시기엔 항공·페리 지연 가능성을 감안해야 합니다.",
-    },
-    "지중해": {
-        "temp": [8, 9, 12, 16, 20, 25, 29, 29, 25, 20, 14, 10],
-        "rain": [80, 70, 60, 55, 40, 20, 8, 15, 40, 85, 95, 90],
-        "rainy_season": [11, 12, 1, 2],
-        "typhoon_season": [],
-        "notes": "여름철은 덥고 건조해 한낮 야외활동 난도가 높습니다.",
-    },
-    "온대대륙": {
-        "temp": [-1, 1, 6, 12, 18, 22, 25, 24, 19, 13, 6, 1],
-        "rain": [45, 40, 45, 55, 70, 75, 70, 65, 55, 50, 50, 45],
-        "rainy_season": [6, 7, 8],
-        "typhoon_season": [],
-        "notes": "겨울엔 결빙/한파, 여름엔 소나기 가능성을 고려하세요.",
-    },
-    "사막": {
-        "temp": [19, 21, 25, 30, 34, 36, 39, 39, 35, 31, 26, 21],
-        "rain": [15, 20, 15, 8, 3, 1, 1, 1, 1, 2, 6, 12],
-        "rainy_season": [],
-        "typhoon_season": [],
-        "notes": "한낮 폭염과 큰 일교차를 감수해야 하며 수분 보충이 중요합니다.",
-    },
+# =========================
+# 기본 설정
+# =========================
+APP_VERSION = "2026.02.21-hotfix1"
+
+st.set_page_config(page_title="얼굴형 기반 헤어스타일 추천", layout="wide")
+st.title("얼굴형 기반 헤어스타일 + 미용실 추천")
+st.caption("자가진단 선택 → GPT 추천 키워드 3개 → (웹 후기 기반 확장검색) → 근처 미용실 추천")
+st.caption(f"앱 버전: {APP_VERSION}")
+
+
+# =========================
+# ✅ 실존 헤어스타일/시술 용어 화이트리스트
+# =========================
+STYLE_TERMS = [
+    "단발", "중단발", "장발", "숏컷", "보브컷", "허쉬컷", "레이어드컷", "샤기컷",
+    "리프컷", "가일컷", "투블럭", "댄디컷", "크롭컷",
+    "C컬펌", "S컬펌", "빌드펌", "히피펌", "쉐도우펌", "가르마펌", "애즈펌",
+    "리젠트펌", "아이롱펌", "볼륨펌", "디지털펌", "셋팅펌",
+    "볼륨매직", "매직", "매직셋팅",
+    "염색", "탈색", "뿌리염색", "옴브레", "발레아쥬",
+    "애쉬브라운", "애쉬그레이", "애쉬블루",
+    "핑크브라운", "초코브라운", "카키브라운",
+    "다운펌", "두피케어", "클리닉",
+    "시스루뱅", "처피뱅", "풀뱅", "애교머리",
+]
+STYLE_STOP = {"미용실", "헤어", "컷", "펌", "염색"}
+
+TONE_COLOR_RECO = {
+    "웜": ["초코브라운", "카키브라운", "핑크브라운"],
+    "쿨": ["애쉬브라운", "애쉬그레이", "애쉬블루"],
 }
 
-
-COUNTRY_CLIMATE_ZONE = {
-    "태국": "열대몬순",
-    "베트남": "열대몬순",
-    "싱가포르": "열대몬순",
-    "말레이시아": "열대몬순",
-    "대만": "동아시아해양",
-    "일본": "동아시아해양",
-    "홍콩": "동아시아해양",
-    "중국": "온대대륙",
-    "미국": "온대대륙",
-    "캐나다": "온대대륙",
-    "영국": "온대대륙",
-    "프랑스": "지중해",
-    "이탈리아": "지중해",
-    "스페인": "지중해",
-    "포르투갈": "지중해",
-    "독일": "온대대륙",
-    "네덜란드": "온대대륙",
-    "튀르키예": "지중해",
-    "아랍에미리트": "사막",
-    "호주": "온대대륙",
-    "뉴질랜드": "온대대륙",
+MOOD_CHOICES = ["청순", "시크", "힙한", "단정한", "귀여운", "세련된", "동안 느낌", "성숙한 느낌"]
+
+MOOD_COLOR_BIAS = {
+    "청순": ["핑크브라운", "초코브라운"],
+    "시크": ["애쉬그레이", "애쉬브라운"],
+    "힙한": ["애쉬블루", "발레아쥬"],
+    "단정한": ["초코브라운", "카키브라운"],
+    "귀여운": ["핑크브라운", "초코브라운"],
+    "세련된": ["애쉬브라운", "카키브라운"],
+    "동안 느낌": ["핑크브라운", "초코브라운"],
+    "성숙한 느낌": ["카키브라운", "애쉬브라운"],
 }
 
 
-# 1. 페이지 설정 (유지)
-st.set_page_config(page_title="NoRegret Trip", page_icon="✈️", layout="wide")
-
-st.title("✈️ NoRegret Trip")
-st.subheader("여행 가자 ^~^")
-
-st.markdown(
-    """
-    <style>
-    .cloud-chat-helper {
-        position: fixed;
-        right: 16px;
-        bottom: 132px;
-        z-index: 1001;
-        background: #ffffff;
-        color: #2f3e46;
-        border: 1px solid #d0d7de;
-        border-radius: 16px;
-        padding: 8px 12px;
-        font-size: 14px;
-        font-weight: 600;
-        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.14);
-    }
-    .cloud-chat-helper::after {
-        content: "";
-        position: absolute;
-        right: 18px;
-        bottom: -8px;
-        width: 14px;
-        height: 14px;
-        background: #ffffff;
-        border-right: 1px solid #d0d7de;
-        border-bottom: 1px solid #d0d7de;
-        transform: rotate(45deg);
-    }
-    .st-key-cloud_chat_icon {
-        position: fixed;
-        right: 16px;
-        bottom: 72px;
-        z-index: 1000;
-    }
-    .st-key-cloud_chat_icon button {
-        border-radius: 999px;
-        width: 44px;
-        height: 44px;
-        padding: 0;
-        font-size: 28px;
-        border: 1px solid #cfd8dc;
-        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.18);
-    }
-    .st-key-cloud_chat_popup {
-        position: fixed;
-        right: 16px;
-        bottom: 128px;
-        width: min(380px, calc(100vw - 32px));
-        max-height: 70vh;
-        overflow-y: auto;
-        background: #ffffff;
-        border-radius: 16px;
-        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.2);
-        z-index: 999;
-        padding: 4px;
-    }
-    </style>
-    """,
-    unsafe_allow_html=True,
-)
-
-if "latest_destinations" not in st.session_state:
-    st.session_state.latest_destinations = []
-if "chat_open" not in st.session_state:
-    st.session_state.chat_open = False
-if "chat_messages" not in st.session_state:
-    st.session_state.chat_messages = [
-        {
-            "role": "assistant",
-            "content": "안녕하세요! ☁️ 추천이 마음에 안 들면 어떤 점이 별로였는지 말해 주세요. 더 잘 맞는 후보를 짧게 다시 추천해 드릴게요.",
-        }
-    ]
-
-
-def get_followup_recommendations(api_key: str, user_message: str, destinations, profile_summary: str):
-    """재추천·일정·관광지 제안을 포함한 여행 챗봇 응답을 생성합니다."""
-    if not api_key:
-        return "사이드바에 OpenAI API Key를 입력하면 바로 다시 추천해 드릴 수 있어요."
-
-    destination_summary = "\n".join(
-        [f"- {d.get('name_kr', '')}: {d.get('reason', '')}" for d in destinations[:3]]
-    ) or "- 아직 추천 결과 없음"
-
-    client = OpenAI(api_key=api_key)
-    response = client.chat.completions.create(
-        model="gpt-4o-mini",
-        temperature=0.8,
-        messages=[
-            {
-                "role": "system",
-                "content": (
-                    "당신은 여행 도우미 챗봇입니다. "
-                    "사용자의 의도를 먼저 파악해 아래 원칙으로 한국어로 답하세요. "
-                    "1) 추천이 마음에 들지 않는다고 하면 공감 1문장 + 대체 여행지 2곳을 불릿으로 짧게 제안. "
-                    "2) 추천이 마음에 들어 일정/관광지 요청을 하면 사용자의 요구를 반영한 일정 또는 관광지 리스트를 불릿으로 제안. "
-                    "3) 정보가 부족하면 최대 2개의 짧은 확인 질문을 먼저 제시. "
-                    "과도한 설명은 줄이고 바로 실행 가능한 제안을 중심으로 답하세요."
-                ),
-            },
-            {
-                "role": "user",
-                "content": (
-                    f"[사용자 여행 프로필]\n{profile_summary}\n\n"
-                    f"[직전 추천]\n{destination_summary}\n\n"
-                    f"[사용자 피드백]\n{user_message}"
-                ),
-            },
-        ],
-    )
+# =========================
+# 필요한 이미지 파일 체크
+# =========================
+REQUIRED_IMAGES = [
+    "웜톤.jpg",
+    "쿨톤.jpg",
+    "계란형.png",
+    "마름모형.png",
+    "하트형.png",
+    "땅콩형.png",
+    "육각형.png",
+    "둥근형.png",
+    "직모.png",
+    "곱슬.png",
+]
+
+
+def must_exist(path: str) -> None:
+    if not Path(path).exists():
+        st.error(
+            f"이미지를 찾을 수 없어요: {path}\n\n"
+            f"app.py와 같은 폴더에 '{path}' 파일이 있는지 확인해주세요."
+        )
+        st.stop()
 
-    return response.choices[0].message.content
 
+for p in REQUIRED_IMAGES:
+    must_exist(p)
 
-st.markdown('<div class="cloud-chat-helper">내가 도와줄게...</div>', unsafe_allow_html=True)
 
-if st.button("☁️", key="cloud_chat_icon", help="재추천/일정 상담 챗봇 열기·닫기 (☁️ 버튼 클릭)"):
-    st.session_state.chat_open = not st.session_state.chat_open
+# =========================
+# API Key 입력
+# =========================
+st.sidebar.header("🔑 API Key 설정")
+st.sidebar.info("🔐 키는 서버에 저장되지 않으며, 새로고침하면 다시 입력해야 할 수 있어요.")
 
+if "KAKAO_REST_API_KEY" not in st.session_state:
+    st.session_state["KAKAO_REST_API_KEY"] = (st.secrets.get("KAKAO_REST_API_KEY", "") or "").strip()
 
-def _extract_destination_keywords(query: str):
-    """도시명(국가명) 형태 문자열에서 검색용 키워드를 추출합니다."""
-    base = query.strip()
-    if "(" in base:
-        base = base.split("(")[0].strip()
-    return [query, base]
+kakao_input = st.sidebar.text_input(
+    "Kakao REST API Key (필수)",
+    value=st.session_state["KAKAO_REST_API_KEY"],
+    type="password",
+)
+st.session_state["KAKAO_REST_API_KEY"] = (kakao_input or "").strip()
+KAKAO_REST_API_KEY = st.session_state["KAKAO_REST_API_KEY"]
 
+if "OPENAI_API_KEY" not in st.session_state:
+    st.session_state["OPENAI_API_KEY"] = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()
 
-def _extract_country_name(query: str):
-    """도시명(국가명) 형태 문자열에서 국가명만 분리합니다."""
-    match = re.search(r"\((.*?)\)", query)
-    if match:
-        return match.group(1).strip()
-    return ""
+openai_input = st.sidebar.text_input(
+    "OpenAI API Key (필수)",
+    value=st.session_state["OPENAI_API_KEY"],
+    type="password",
+)
+st.session_state["OPENAI_API_KEY"] = (openai_input or "").strip()
+OPENAI_API_KEY = st.session_state["OPENAI_API_KEY"]
+
+st.sidebar.caption("Kakao 키가 없으면 미용실 검색이 불가합니다. OpenAI 키가 없으면 GPT 추천/후기 분석이 불가합니다.")
+
+if not KAKAO_REST_API_KEY:
+    st.warning("카카오 REST API Key를 사이드바에 입력해주세요.")
+    st.stop()
+
+if not OPENAI_API_KEY:
+    st.warning("OpenAI API Key를 사이드바에 입력해주세요.")
+    st.stop()
+
+
+# =========================
+# UI 카드 렌더 유틸
+# =========================
+def select_card(
+    *,
+    title: str,
+    image_path: str,
+    button_label: str,
+    on_click_value: str,
+    session_key: str,
+    button_key: str,
+    desc_md: str | None = None,
+    img_width: int = 160,
+    selected: bool = False,
+) -> None:
+    st.subheader(title)
+    st.image(image_path, width=img_width)
+    if desc_md:
+        st.markdown(desc_md)
+
+    btn_type = "primary" if selected else "secondary"
+    if st.button(button_label, key=button_key, use_container_width=True, type=btn_type):
+        st.session_state[session_key] = on_click_value
+        st.rerun()
 
 
-def _get_wikipedia_image(query: str):
-    """Wikipedia 요약 API를 이용해 대표 이미지를 보조 조회합니다."""
-    for keyword in _extract_destination_keywords(query):
-        try:
-            endpoint = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{keyword}"
-            res = requests.get(endpoint, timeout=8)
-            if res.status_code != 200:
-                continue
-            data = res.json()
-            thumb = data.get("thumbnail", {}).get("source")
-            original = data.get("originalimage", {}).get("source")
-            if original or thumb:
-                return original or thumb
-        except requests.RequestException:
-            continue
-    return None
+# =========================
+# 얼굴형 힌트 용어
+# =========================
+FACE_SHAPE_TO_KEYWORDS: Dict[str, List[str]] = {
+    "둥근얼굴형": ["레이어드컷", "S컬펌", "C컬펌", "시스루뱅"],
+    "긴얼굴형": ["단발", "중단발", "C컬펌", "히피펌"],
+    "각진 얼굴형": ["레이어드컷", "S컬펌", "볼륨펌"],
+    "역삼각형 얼굴": ["단발", "C컬펌", "볼륨매직"],
+    "계란형 얼굴": ["단발", "중단발", "레이어드컷", "S컬펌"],
+}
 
+APP_FACE_TO_RECO_FACE: Dict[str, str] = {
+    "둥근형": "둥근얼굴형",
+    "계란형": "계란형 얼굴",
+    "하트형": "역삼각형 얼굴",
+    "육각형": "각진 얼굴형",
+    "마름모형": "긴얼굴형",
+    "땅콩형": "각진 얼굴형",
+}
 
-def _get_unsplash_image(query: str):
-    """Unsplash Source URL을 이용해 검색어 기반 이미지를 반환합니다."""
-    keywords = _extract_destination_keywords(query)
 
-    for keyword in keywords:
-        try:
-            encoded_query = requests.utils.quote(keyword)
-            candidate_url = f"https://source.unsplash.com/1600x900/?{encoded_query}"
-            response = requests.get(candidate_url, timeout=8, allow_redirects=True)
-            response.raise_for_status()
-            if "images.unsplash.com" in response.url:
-                return response.url
-        except requests.RequestException:
-            continue
+def build_auto_terms(app_face_shape: str, preferred_length: str, mood: str, max_terms: int = 6) -> List[str]:
+    reco_face = APP_FACE_TO_RECO_FACE.get(app_face_shape, "계란형 얼굴")
+    terms = FACE_SHAPE_TO_KEYWORDS.get(reco_face, ["레이어드컷", "C컬펌", "S컬펌"]).copy()
+
+    if preferred_length == "짧게":
+        terms = ["숏컷", "보브컷", *terms]
+    elif preferred_length == "길게":
+        terms = ["중단발", "장발", *terms]
+
+    if mood in {"단정한", "세련된"}:
+        terms.append("C컬펌")
+    if mood in {"힙한", "시크"}:
+        terms.extend(["허쉬컷", "레이어드컷"])
+    if mood in {"귀여운", "청순", "동안 느낌"}:
+        terms.extend(["시스루뱅", "S컬펌"])
+
+    uniq = []
+    seen = set()
+    for t in terms:
+        if t in STYLE_TERMS and t not in seen:
+            seen.add(t)
+            uniq.append(t)
+    return uniq[:max_terms]
+
+
+
+def build_color_recommendations(tone: str, mood: str) -> List[Tuple[str, str]]:
+    base_colors = TONE_COLOR_RECO.get(tone, [])
+    mood_bias = MOOD_COLOR_BIAS.get(mood, [])
+
+    ordered: List[str] = []
+    for c in mood_bias + base_colors:
+        if c in STYLE_TERMS and c not in ordered:
+            ordered.append(c)
+
+    reason_map = {
+        "애쉬브라운": "쿨톤/세련 무드에 잘 맞아 얼굴톤을 맑게 보이게 해줘요.",
+        "애쉬그레이": "시크한 분위기를 강화하고 스타일 포인트를 살려줘요.",
+        "애쉬블루": "힙하고 개성 있는 무드를 강조하기 좋아요.",
+        "핑크브라운": "청순/귀여운 분위기에 부드럽고 생기 있는 인상을 줘요.",
+        "초코브라운": "부담 없이 단정하고 자연스러운 이미지를 만들기 좋아요.",
+        "카키브라운": "성숙하고 차분한 무드에 잘 어울리며 톤 정리가 쉬워요.",
+        "발레아쥬": "입체감을 더해 힙한 스타일 연출에 유리해요.",
+    }
 
-    return None
+    picks = ordered[:3]
+    return [(c, reason_map.get(c, "톤/무드와 조화가 좋아 추천해요.")) for c in picks]
+
+
+# =========================
+# GPT 추천(3개) - 실존 용어만
+# =========================
+def safe_json_extract(text: str) -> str:
+    raw = (text or "").strip()
+    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
+    raw = re.sub(r"\s*```$", "", raw)
+    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
+    return m.group(0) if m else raw
+
+
+def normalize_query(q: str) -> str:
+    q = (q or "").replace("\n", " ").strip()
+    q = re.sub(r"\s+", " ", q)
+    if "미용실" not in q:
+        q = f"{q} 미용실".strip()
+    return q
+
+
+def enforce_style_whitelist(query: str, allowed_terms: List[str]) -> str:
+    q = query.replace("미용실", "").strip()
+    terms_sorted = sorted(allowed_terms, key=len, reverse=True)
+    picked: List[str] = []
+    for t in terms_sorted:
+        if t in q and t not in picked:
+            picked.append(t)
+
+    if not picked:
+        picked = [allowed_terms[0]] if allowed_terms else ["레이어드컷"]
+
+    picked = picked[:2]
+    return normalize_query(" ".join(picked))
+
+
+def make_queries_with_openai(
+    *,
+    api_key: str,
+    tone: str,
+    face_shape: str,
+    hair_type: str,
+    preferred_length: str,
+    mood: str,
+    current_hair_length: str,
+    bangs_status: str,
+    styling_level: str,
+    hint_terms: List[str],
+    color_candidates: List[str],
+) -> Tuple[List[str], List[str]]:
+    client = OpenAI(api_key=api_key)
 
+    prompt = f"""
+너는 한국 헤어디자이너야.
+사용자 정보를 바탕으로 카카오 로컬에서 검색 가능한 "미용실 검색 키워드 3개"를 추천해줘.
+
+중요 규칙:
+- 각 query에는 반드시 '미용실' 포함
+- query는 반드시 허용된 스타일 용어 목록에서만 골라 조합
+- 허용 목록 밖 단어 절대 금지
+- (스타일용어 1~2개 + '미용실')로 간결하게
+
+[사용자 정보]
+- tone: {tone}
+- face_shape: {face_shape}
+- hair_type: {hair_type}
+- preferred_length: {preferred_length}
+- mood: {mood}
+- current_hair_length: {current_hair_length}
+- bangs_status: {bangs_status}
+- styling_level: {styling_level}
+
+[추천 힌트]
+{json.dumps(hint_terms, ensure_ascii=False)}
+
+[톤/무드 기반 염색 컬러 후보]
+{json.dumps(color_candidates, ensure_ascii=False)}
+
+[허용된 스타일 용어 목록]
+{json.dumps(STYLE_TERMS, ensure_ascii=False)}
+
+출력(JSON만):
+{{
+  "recommendations": [
+    {{"query":"... 미용실","reason":"..."}},
+    {{"query":"... 미용실","reason":"..."}},
+    {{"query":"... 미용실","reason":"..."}}
+  ]
+}}
+""".strip()
+
+    resp = client.chat.completions.create(
+        model="gpt-4o-mini",
+        messages=[{"role": "user", "content": prompt}],
+        temperature=0.2,
+    )
 
-def get_landmark_image(query: str):
-    """Unsplash + DuckDuckGo + Wikipedia 순으로 대표 이미지를 가져옵니다."""
-    unsplash_image = _get_unsplash_image(f"{query} landmark")
-    if unsplash_image:
-        return unsplash_image, None
+    raw = safe_json_extract(resp.choices[0].message.content or "")
+    queries: List[str] = []
+    reasons: List[str] = []
 
     try:
-        with DDGS() as ddgs:
-            results = list(
-                ddgs.images(
-                    keywords=f"{query} landmark",
-                    region="kr-kr",
-                    safesearch="moderate",
-                    size="Large",
-                    max_results=1,
-                )
-            )
-
-        if results:
-            image_url = (
-                results[0].get("image")
-                or results[0].get("thumbnail")
-                or results[0].get("url")
-            )
-            if image_url:
-                return image_url, None
-
-        wiki_image = _get_wikipedia_image(query)
-        if wiki_image:
-            return wiki_image, None
-
-        return None, "대표 이미지를 찾지 못했어요."
+        obj = json.loads(raw)
+        recs = obj.get("recommendations", [])
+        if isinstance(recs, list):
+            for it in recs:
+                if isinstance(it, dict):
+                    queries.append(str(it.get("query", "")).strip())
+                    reasons.append(str(it.get("reason", "")).strip())
     except Exception:
-        wiki_image = _get_wikipedia_image(query)
-        if wiki_image:
-            return wiki_image, None
-        return None, "Unsplash 또는 보조 이미지 서비스 접근이 제한되어 이미지를 불러오지 못했어요."
-
-
-def get_representative_food(query: str):
-    """도시/국가 기준 대표 먹거리 이름과 이미지를 반환합니다."""
-    keywords = _extract_destination_keywords(query)
-    country_name = _extract_country_name(query)
-    if country_name:
-        keywords.append(country_name)
-
-    food_name = None
-    for keyword in keywords:
-        if keyword in REPRESENTATIVE_FOOD_BY_DESTINATION:
-            food_name = REPRESENTATIVE_FOOD_BY_DESTINATION[keyword]
+        queries, reasons = [], []
+
+    final_q: List[str] = []
+    final_r: List[str] = []
+    seen = set()
+
+    for q, r in zip(queries, reasons):
+        fixed = enforce_style_whitelist(q, allowed_terms=STYLE_TERMS)
+        if fixed and fixed not in seen:
+            seen.add(fixed)
+            final_q.append(fixed)
+            final_r.append(r)
+        if len(final_q) >= 3:
             break
 
-    if not food_name:
-        food_name = "현지 대표 요리"
-
-    image_query = food_name if food_name != "현지 대표 요리" else f"{keywords[0]} 대표 음식"
-
-    unsplash_image = _get_unsplash_image(image_query)
-    if unsplash_image:
-        return food_name, unsplash_image, None
-
-    try:
-        with DDGS() as ddgs:
-            results = list(
-                ddgs.images(
-                    keywords=image_query,
-                    region="kr-kr",
-                    safesearch="moderate",
-                    size="Medium",
-                    max_results=1,
-                )
-            )
-
-        if results and results[0].get("image"):
-            return food_name, results[0]["image"], None
-    except Exception:
-        pass
-
-    food_image = _get_wikipedia_image(food_name)
-    if food_image:
-        return food_name, food_image, None
-
-    return food_name, None, "대표 먹거리 이미지를 찾지 못했어요."
-
-
-def get_best_travel_season(latitude: float):
-    """위도 기반으로 여행하기 좋은 시기를 추천합니다."""
-    abs_lat = abs(latitude)
-
-    if abs_lat < 15:
-        return "연중 여행 가능 (우기/건기 확인 권장)"
-
-    if latitude >= 0:
-        return "4~6월, 9~10월 (기온이 온화하고 이동이 편한 시기)"
-
-    return "10~12월, 3~4월 (남반구 기준 쾌적한 계절)"
-
-
-def _get_trip_months(travel_dates):
-    """선택된 여행 날짜 범위에서 포함된 월 목록을 계산합니다."""
-    if not travel_dates:
-        return [datetime.now().month]
-
-    if isinstance(travel_dates, (list, tuple)) and len(travel_dates) == 2:
-        start_date, end_date = travel_dates
-        if start_date > end_date:
-            start_date, end_date = end_date, start_date
-    else:
-        start_date = end_date = travel_dates
-
-    months = []
-    cursor = datetime(start_date.year, start_date.month, 1)
-    end_cursor = datetime(end_date.year, end_date.month, 1)
-
-    while cursor <= end_cursor:
-        months.append(cursor.month)
-        if cursor.month == 12:
-            cursor = datetime(cursor.year + 1, 1, 1)
-        else:
-            cursor = datetime(cursor.year, cursor.month + 1, 1)
-
-    return months or [datetime.now().month]
-
-
-def get_seasonal_travel_note(destination_name: str, latitude: float, travel_dates):
-    """여행 기간 평균 기후와 우기/태풍 시즌 경고를 반환합니다."""
-    country = extract_country_from_destination(destination_name)
-    zone = COUNTRY_CLIMATE_ZONE.get(country)
-
-    if not zone:
-        zone = "온대대륙" if abs(latitude) >= 20 else "열대몬순"
-
-    climate = ZONE_CLIMATE_STATS[zone]
-    months = _get_trip_months(travel_dates)
-    month_indexes = [month - 1 for month in months]
-
-    avg_temp = sum(climate["temp"][idx] for idx in month_indexes) / len(month_indexes)
-    avg_rain = sum(climate["rain"][idx] for idx in month_indexes) / len(month_indexes)
-
-    rainy_overlap = [m for m in months if m in climate["rainy_season"]]
-    typhoon_overlap = [m for m in months if m in climate["typhoon_season"]]
-
-    cautions = []
-    if rainy_overlap:
-        cautions.append(
-            f"⚠️ {', '.join(map(str, rainy_overlap))}월은 우기/강수 집중 구간입니다. {climate['notes']}"
-        )
-    if typhoon_overlap:
-        cautions.append(
-            f"⚠️ {', '.join(map(str, typhoon_overlap))}월은 태풍 영향 가능성이 있습니다. 일정 변동 가능성을 꼭 감안하세요."
-        )
-
-    if not cautions:
-        cautions.append("✅ 선택한 기간은 계절 리스크가 비교적 낮은 편입니다.")
-
-    tradeoff = "지금 가면 이런 점은 감수해야 합니다: "
-    if avg_rain >= 150:
-        tradeoff += "실외 일정 중 갑작스러운 비로 동선이 자주 끊길 수 있어요."
-    elif avg_temp >= 32:
-        tradeoff += "낮 시간대 야외 활동 피로도가 높아질 수 있어요."
-    elif avg_temp <= 3:
-        tradeoff += "일몰 후 체감온도가 낮아 방한 준비가 필수예요."
-    else:
-        tradeoff += "관광 밀집 시간대와 일교차를 고려해 일정에 여유를 두는 것이 좋아요."
-
-    return (
-        f"여행 기간 평균 기온은 **약 {avg_temp:.1f}°C**, 평균 강수량은 **약 {avg_rain:.0f}mm/월**입니다.\n"
-        + "\n".join(cautions)
-        + f"\n\n💬 {tradeoff}"
-    )
-
-
-def get_weather_summary(latitude: float, longitude: float, weather_api_key: str):
-    """OpenWeather API로 현재 날씨 + 단기 예보를 요약합니다."""
-    if not weather_api_key:
-        return "OpenWeather API Key를 입력하면 현재 날씨를 볼 수 있어요."
-
-    current_endpoint = "https://api.openweathermap.org/data/2.5/weather"
-    forecast_endpoint = "https://api.openweathermap.org/data/2.5/forecast"
-    base_params = {
-        "lat": latitude,
-        "lon": longitude,
-        "appid": weather_api_key,
-        "units": "metric",
-        "lang": "kr",
+    if len(final_q) < 3:
+        fallback_pool = []
+        for t in hint_terms:
+            if t in STYLE_TERMS:
+                fallback_pool.append(normalize_query(f"{t} 미용실"))
+        for t in STYLE_TERMS:
+            fallback_pool.append(normalize_query(f"{t} 미용실"))
+
+        for q in fallback_pool:
+            if q not in seen:
+                seen.add(q)
+                final_q.append(q)
+                final_r.append("화이트리스트 기반 보완 추천")
+            if len(final_q) >= 3:
+                break
+
+    return final_q[:3], final_r[:3]
+
+
+# =========================
+# Kakao Local + Kakao Search 유틸
+# =========================
+def kakao_headers() -> Dict[str, str]:
+    return {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
+
+
+@st.cache_data(show_spinner=False, ttl=3600)
+def kakao_address_to_xy(address: str) -> Tuple[float, float]:
+    url = "https://dapi.kakao.com/v2/local/search/address.json"
+    r = requests.get(url, headers=kakao_headers(), params={"query": address}, timeout=10)
+    r.raise_for_status()
+    docs = r.json().get("documents", [])
+    if not docs:
+        raise ValueError("주소를 찾지 못했어요. 더 자세한 주소로 입력해 주세요.")
+    return float(docs[0]["x"]), float(docs[0]["y"])
+
+
+@st.cache_data(show_spinner=False, ttl=600)
+def kakao_keyword_search(query: str, x: float, y: float, radius_m: int = 3000, size: int = 15, page: int = 1) -> List[dict]:
+    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
+    params = {
+        "query": query,
+        "x": str(x),
+        "y": str(y),
+        "radius": str(radius_m),
+        "size": str(size),
+        "page": str(page),
+        "sort": "distance",
     }
-
-    try:
-        current_res = requests.get(current_endpoint, params=base_params, timeout=12)
-        current_res.raise_for_status()
-        current_data = current_res.json()
-
-        forecast_res = requests.get(forecast_endpoint, params=base_params, timeout=12)
-        forecast_res.raise_for_status()
-        forecast_data = forecast_res.json().get("list", [])
-
-        current_weather = current_data.get("weather", [{}])[0].get("description", "날씨 정보 없음")
-        current_temp = current_data.get("main", {}).get("temp")
-        feels_like = current_data.get("main", {}).get("feels_like")
-
-        rainy_slots = 0
-        for slot in forecast_data[:16]:  # 약 2일치(3시간 간격)
-            rain_probability = slot.get("pop", 0)
-            if rain_probability >= 0.6:
-                rainy_slots += 1
-
-        season_tip = get_best_travel_season(latitude)
-
-        return (
-            f"현재 날씨는 **{current_weather}**, 기온은 **{current_temp:.1f}°C** "
-            f"(체감 **{feels_like:.1f}°C**) 입니다. "
-            f"향후 48시간 기준 비 가능성이 높은 시간대는 약 {rainy_slots}회예요.\n\n"
-            f"✈️ **여행 추천 시기**: {season_tip}"
-        )
-    except requests.HTTPError as exc:
-        return f"OpenWeather 요청이 실패했어요. API Key를 확인해 주세요: {exc}"
-    except requests.RequestException as exc:
-        return f"날씨 정보를 가져오지 못했어요: {exc}"
-
-
-def build_regret_summary(regret_risk_warnings):
-    """후회 가능성 경고 목록을 상단 요약용 추천도 별점/한줄로 변환합니다."""
-    warning_count = len(regret_risk_warnings)
-    recommended_stars = max(1, 5 - warning_count)
-    star_rating = "".join(["⭐" for _ in range(recommended_stars)] + ["☆" for _ in range(5 - recommended_stars)])
-    if warning_count:
-        one_liner = regret_risk_warnings[0]
-    else:
-        one_liner = "전반적으로 잘 맞는 여행지지만, 완벽한 여행지는 없어서 소소한 불편은 있을 수 있어요."
-    return star_rating, one_liner
+    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
+    r.raise_for_status()
+    return r.json().get("documents", [])
 
 
-def ensure_minimum_regret_warning(regret_risk_warnings):
-    """후회 가능성 상세에 항상 최소 1개 경고가 노출되도록 보정합니다."""
-    if regret_risk_warnings:
-        return regret_risk_warnings
-    return ["⚠️ 완벽한 여행지는 없어요. 숙소/자연환경에 따라 벌레가 보일 수 있으니 방충 대비를 챙기세요."]
+def strip_html(text: str) -> str:
+    text = re.sub(r"<[^>]+>", " ", text)
+    return re.sub(r"\s+", " ", text).strip()
 
 
-def build_weather_core_summary(weather_summary: str):
-    """날씨 상세 텍스트에서 상단 요약용 핵심 정보를 추출합니다."""
-    if "현재 날씨는" not in weather_summary:
-        return weather_summary
-
-    weather_match = re.search(
-        r"현재 날씨는 \*\*(.*?)\*\*, 기온은 \*\*([\d\.-]+°C)\*\* \(체감 \*\*([\d\.-]+°C)\*\*\).+?약 (\d+)회",
-        weather_summary,
-    )
-    if not weather_match:
-        return weather_summary
-
-    current_weather, current_temp, feels_like, rainy_slots = weather_match.groups()
-    rainy_slots = int(rainy_slots)
-    rainy_flag = "우산 준비" if rainy_slots >= 4 else "우기 아님"
-    return f"{current_weather} / {current_temp} / 체감 {feels_like} / {rainy_flag}"
-
-
-def build_weather_emoji_display(weather_summary: str):
-    """날씨 핵심 문구를 이모지+설명으로 변환합니다."""
-    weather_core = build_weather_core_summary(weather_summary)
-    lower_text = weather_core.lower()
-
-    if any(keyword in lower_text for keyword in ["비", "소나기", "rain", "drizzle"]):
-        weather_emoji = "🌧️"
-    elif any(keyword in lower_text for keyword in ["눈", "snow"]):
-        weather_emoji = "❄️"
-    elif any(keyword in lower_text for keyword in ["흐림", "구름", "cloud"]):
-        weather_emoji = "☁️"
-    elif any(keyword in lower_text for keyword in ["천둥", "storm", "번개"]):
-        weather_emoji = "⛈️"
-    else:
-        weather_emoji = "☀️"
-
-    return weather_emoji, weather_core
-
-
-def build_budget_range_summary(total_budget_text: str):
-    """총 예산 문구에서 ± 범위를 추정해 요약합니다."""
-    numbers = [int(value.replace(",", "")) for value in re.findall(r"\d[\d,]*", total_budget_text)]
-    if not numbers:
-        return total_budget_text
-
-    if len(numbers) >= 2:
-        low, high = min(numbers), max(numbers)
-        center = (low + high) / 2
-        spread = (high - low) / 2
-    else:
-        center = numbers[0]
-        spread = center * 0.2
+@st.cache_data(show_spinner=False, ttl=1800)
+def kakao_search_blog(query: str, size: int = 5) -> List[dict]:
+    url = "https://dapi.kakao.com/v2/search/blog"
+    params = {"query": query, "size": size, "sort": "accuracy"}
+    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
+    r.raise_for_status()
+    return r.json().get("documents", [])
 
-    center_manwon = center / 10000
-    spread_manwon = spread / 10000
-    return f"약 {center_manwon:,.0f}만원 (±{spread_manwon:,.0f}만원)"
 
+@st.cache_data(show_spinner=False, ttl=1800)
+def kakao_search_web(query: str, size: int = 5) -> List[dict]:
+    url = "https://dapi.kakao.com/v2/search/web"
+    params = {"query": query, "size": size, "sort": "accuracy"}
+    r = requests.get(url, headers=kakao_headers(), params=params, timeout=10)
+    r.raise_for_status()
+    return r.json().get("documents", [])
 
-def to_manwon_text(raw_text: str):
-    """숫자/원 단위 텍스트를 만원 단위 텍스트로 변환합니다."""
-    numbers = [int(value.replace(",", "")) for value in re.findall(r"\d[\d,]*", raw_text)]
-    if not numbers:
-        return raw_text
 
-    manwon_values = [f"{number / 10000:,.0f}만원" for number in numbers]
+def build_review_snippet_for_place(place_name: str, area_hint: str) -> str:
+    q = f"{place_name} {area_hint} 미용실 후기 펌 컷"
+    try:
+        blog_docs = kakao_search_blog(q, size=5)
+    except Exception:
+        blog_docs = []
+    try:
+        web_docs = kakao_search_web(q, size=5)
+    except Exception:
+        web_docs = []
 
-    if len(manwon_values) == 1:
-        return f"약 {manwon_values[0]}"
-    return " ~ ".join(manwon_values)
+    parts: List[str] = []
+    for d in blog_docs[:5]:
+        parts.append(f"[블로그] {strip_html(d.get('title', ''))} - {strip_html(d.get('contents', ''))}")
+    for d in web_docs[:5]:
+        parts.append(f"[웹] {strip_html(d.get('title', ''))} - {strip_html(d.get('contents', ''))}")
 
+    return " | ".join([p for p in parts if p.strip()])[:2500]
 
-def build_primary_caution(regret_risk_warnings, seasonal_note: str):
-    """상단 요약에 노출할 1줄 주의문을 반환합니다."""
-    if regret_risk_warnings:
-        return regret_risk_warnings[0]
 
-    seasonal_alerts = [line.strip() for line in seasonal_note.splitlines() if line.strip().startswith("⚠️")]
-    if seasonal_alerts:
-        return seasonal_alerts[0]
+def analyze_styles_from_reviews_with_openai(
+    *,
+    api_key: str,
+    chosen_query: str,
+    places: List[dict],
+    review_snippets: Dict[str, str],
+) -> Dict[str, Dict]:
+    client = OpenAI(api_key=api_key)
 
-    return "⚠️ 일교차와 야간 기온을 고려해 얇은 겉옷을 챙기세요."
+    payload = []
+    for p in places:
+        name = p.get("place_name", "")
+        addr = p.get("road_address_name", "") or p.get("address_name", "")
+        payload.append({"name": name, "address": addr, "snippet": review_snippets.get(name, "")})
 
+    prompt = f"""
+너는 한국 헤어/미용실 리뷰 분석가야.
+사용자의 의도 키워드와 각 미용실의 웹 후기 스니펫을 보고,
+각 미용실이 유명한 시술/스타일 태그를 뽑아줘.
 
-def get_festival_summary(query: str):
-    """DuckDuckGo 텍스트 검색으로 축제/이벤트 정보 요약을 반환합니다."""
-    current_year = datetime.now().year
+규칙:
+- tags는 반드시 아래 허용 목록에서만 선택
+- snippet이 빈 경우 tags=[], summary="정보 부족"
+- JSON만 출력
 
-    try:
-        with DDGS() as ddgs:
-            items = list(
-                ddgs.text(
-                    keywords=f"{query} festival event {current_year}",
-                    region="kr-kr",
-                    safesearch="moderate",
-                    max_results=3,
-                )
-            )
+[chosen_query] {chosen_query}
+[허용된 스타일 용어 목록] {json.dumps(STYLE_TERMS, ensure_ascii=False)}
+[데이터] {json.dumps(payload, ensure_ascii=False)}
 
-        if not items:
-            return "검색 결과 기준, 근시일 내 확인 가능한 대표 축제 정보를 찾지 못했어요."
-
-        summaries = []
-        for item in items[:2]:
-            title = item.get("title", "이벤트")
-            snippet = item.get("body", "일정 정보는 링크에서 확인해 주세요.")
-            summaries.append(f"- **{title}**: {snippet}")
-
-        return "\n".join(summaries)
-    except Exception as exc:
-        return f"축제 정보를 가져오지 못했어요: {exc}"
-
-
-def get_destination_bgm(name_kr: str):
-    """여행지 분위기/지역성을 반영한 유튜브 BGM 플레이리스트를 반환합니다."""
-    city = name_kr.split("(")[0].strip()
-    country = extract_country_from_destination(name_kr)
-
-    city_bgm_map = {
-        "파리": ("파리 재즈 카페 & 샹송 무드", "https://www.youtube.com/watch?v=cTLTG4FTNBQ"),
-        "도쿄": ("도쿄 시티팝 드라이브", "https://www.youtube.com/watch?v=3bNITQR4Uso"),
-        "오사카": ("오사카 네온 스트리트 시티팝", "https://www.youtube.com/watch?v=3bNITQR4Uso"),
-        "교토": ("교토 전통 악기 힐링 무드", "https://www.youtube.com/watch?v=4zG7WcW2nQ4"),
-        "치앙마이": ("치앙마이 카페 감성 로파이", "https://www.youtube.com/watch?v=5qap5aO4i9A"),
-        "방콕": ("방콕 루프탑 나이트 무드", "https://www.youtube.com/watch?v=JfVOs4VSpmA"),
-        "다낭": ("다낭 해변 선셋 칠 음악", "https://www.youtube.com/watch?v=DWcJFNfaw9c"),
-        "하노이": ("하노이 올드쿼터 베트남 감성", "https://www.youtube.com/watch?v=uaf4iR5Vw9s"),
-        "뉴올리언스": ("뉴올리언스 스트리트 재즈", "https://www.youtube.com/watch?v=Dx5qFachd3A"),
-        "리스본": ("리스본 파두(Fado) 감성", "https://www.youtube.com/watch?v=QhBwrn7fG9k"),
-        "세비야": ("세비야 플라멩코 무드", "https://www.youtube.com/watch?v=t4H_Zoh7G5A"),
-        "이비사": ("이비사 비치 하우스 뮤직", "https://www.youtube.com/watch?v=1bJY4wF2J3A"),
-        "두바이": ("사막 드라이브 아라비안 라운지", "https://www.youtube.com/watch?v=4jP06Wk6M4Q"),
-        "카이로": ("카이로 아라빅 오리엔탈 무드", "https://www.youtube.com/watch?v=_O6fQkS3SIA"),
-        "울란바토르": ("몽골 초원 & 호미(Hoomei) 무드", "https://www.youtube.com/watch?v=9e9v4M9RjvY"),
-    }
+출력:
+{{"salons":[{{"name":"...","tags":["..."],"summary":"..."}}, ...]}}
+""".strip()
 
-    country_bgm_map = {
-        "일본": ("일본 여행 무드 시티팝/재즈", "https://www.youtube.com/watch?v=3bNITQR4Uso"),
-        "중국": ("중국 전통 악기 + 현대 퓨전 무드", "https://www.youtube.com/watch?v=9U8kbM_BhWc"),
-        "대만": ("대만 야시장 감성 인디팝", "https://www.youtube.com/watch?v=qM4vYf6A5LQ"),
-        "홍콩": ("홍콩 야경 시네마틱 무드", "https://www.youtube.com/watch?v=AD8G7f8J6Vg"),
-        "베트남": ("베트남 로컬 감성 어쿠스틱", "https://www.youtube.com/watch?v=uaf4iR5Vw9s"),
-        "태국": ("태국 트로피컬 칠 & 로컬 무드", "https://www.youtube.com/watch?v=JfVOs4VSpmA"),
-        "싱가포르": ("싱가포르 마리나 베이 라운지", "https://www.youtube.com/watch?v=6zXDo4dL7SU"),
-        "미국": ("미국 로드트립 클래식 플레이리스트", "https://www.youtube.com/watch?v=gEPmA3USJdI"),
-        "영국": ("런던 브릿팝 & 인디 감성", "https://www.youtube.com/watch?v=VbfpW0pbvaU"),
-        "프랑스": ("프랑스 샹송 & 파리지앵 재즈", "https://www.youtube.com/watch?v=cTLTG4FTNBQ"),
-        "스페인": ("스페인 플라멩코 & 기타 무드", "https://www.youtube.com/watch?v=t4H_Zoh7G5A"),
-        "포르투갈": ("포르투갈 파두(Fado) 감성", "https://www.youtube.com/watch?v=QhBwrn7fG9k"),
-        "튀르키예": ("이스탄불 보스포루스 오리엔탈 무드", "https://www.youtube.com/watch?v=T4k_qws0k4E"),
-        "아랍에미리트": ("중동 라운지 & 아라비안 나이트", "https://www.youtube.com/watch?v=4jP06Wk6M4Q"),
-        "이집트": ("이집트 전통 리듬 & 오리엔탈 무드", "https://www.youtube.com/watch?v=_O6fQkS3SIA"),
-        "몽골": ("몽골 전통/초원 무드 사운드", "https://www.youtube.com/watch?v=9e9v4M9RjvY"),
-    }
-
-    fallback_candidates = [
-        ("잔잔한 여행 로파이 라이브", "https://www.youtube.com/watch?v=jfKfPfyJRdk"),
-        ("여행 브이로그용 감성 BGM 모음", "https://www.youtube.com/watch?v=DWcJFNfaw9c"),
-    ]
-
-    for keyword, bgm_info in city_bgm_map.items():
-        if keyword in city:
-            return pick_available_bgm([bgm_info], f"{city} travel bgm playlist")
-
-    for keyword, bgm_info in country_bgm_map.items():
-        if keyword in country:
-            return pick_available_bgm([bgm_info], f"{country} travel bgm playlist")
-
-    return pick_available_bgm(
-        [
-            (f"{country} 여행 분위기에 어울리는 로컬/무드 음악", "https://www.youtube.com/watch?v=2OEL4P1Rz04"),
-            *fallback_candidates,
-        ],
-        f"{country} travel bgm playlist",
+    resp = client.chat.completions.create(
+        model="gpt-4o-mini",
+        messages=[{"role": "user", "content": prompt}],
+        temperature=0.2,
     )
 
-
-@st.cache_data(ttl=3600)
-def is_youtube_video_available(url: str):
-    """YouTube oEmbed 응답으로 재생 가능한 영상인지 확인합니다."""
+    raw = safe_json_extract(resp.choices[0].message.content or "")
+    result: Dict[str, Dict] = {}
     try:
-        response = requests.get(
-            "https://www.youtube.com/oembed",
-            params={"url": url, "format": "json"},
-            timeout=4,
-        )
-        return response.status_code == 200
+        obj = json.loads(raw)
+        salons = obj.get("salons", [])
+        if isinstance(salons, list):
+            for s in salons:
+                if not isinstance(s, dict):
+                    continue
+                name = str(s.get("name", "")).strip()
+                tags = s.get("tags", [])
+                summary = str(s.get("summary", "")).strip()
+                if isinstance(tags, list):
+                    tags = [str(t).strip() for t in tags if str(t).strip() in STYLE_TERMS]
+                else:
+                    tags = []
+                if name:
+                    result[name] = {"tags": tags[:6], "summary": summary}
     except Exception:
-        return False
-
-
-def pick_available_bgm(candidates, search_query: str):
-    """후보 링크 중 재생 가능한 BGM을 우선 선택하고, 없으면 검색 결과에서 대체합니다."""
-    for title, url in candidates:
-        if is_youtube_video_available(url):
-            return title, url
-
-    try:
-        with DDGS() as ddgs:
-            items = list(
-                ddgs.text(
-                    keywords=f"site:youtube.com {search_query}",
-                    region="wt-wt",
-                    safesearch="moderate",
-                    max_results=8,
-                )
+        result = {}
+    return result
+
+
+def build_expanded_queries_from_tags(chosen_query: str, style_map: Dict[str, Dict], max_queries: int = 3) -> List[str]:
+    counter = Counter()
+    for v in style_map.values():
+        for t in v.get("tags", []):
+            if t and t not in STYLE_STOP:
+                counter[t] += 1
+
+    ranked = [t for t, _ in counter.most_common()]
+    chosen_words = set(re.findall(r"[가-힣A-Za-z0-9]+", chosen_query))
+    ranked = [t for t in ranked if t not in chosen_words]
+
+    expanded = [normalize_query(f"{t} 미용실") for t in ranked[:max_queries]]
+
+    uniq, seen = [], set()
+    for q in expanded:
+        if q not in seen:
+            seen.add(q)
+            uniq.append(q)
+    return uniq[:max_queries]
+
+
+def merge_places(*lists: List[dict]) -> List[dict]:
+    merged = []
+    seen = set()
+    for lst in lists:
+        for p in lst:
+            key = p.get("place_url") or (p.get("place_name", "") + "|" + (p.get("road_address_name", "") or p.get("address_name", "")))
+            if key and key not in seen:
+                seen.add(key)
+                merged.append(p)
+    return merged
+
+
+def build_fallback_queries(chosen_query: str) -> List[str]:
+    q = (chosen_query or "").strip()
+    q_no = q.replace("미용실", "").strip()
+    fallbacks = [q] if q else []
+    if q_no:
+        fallbacks.extend([q_no, f"{q_no} 헤어", f"{q_no} 헤어샵"])
+    fallbacks.append("미용실")
+
+    uniq, seen = [], set()
+    for x in fallbacks:
+        x = re.sub(r"\s+", " ", x).strip()
+        if x and x not in seen:
+            seen.add(x)
+            uniq.append(x)
+    return uniq
+
+
+def search_salons_with_fallback(*, chosen_query: str, x: float, y: float, radius_m: int, size: int = 15) -> Tuple[List[dict], str, int]:
+    queries = build_fallback_queries(chosen_query)
+    radius_try = [radius_m, min(radius_m * 2, 20000)]
+
+    for r in radius_try:
+        for q in queries:
+            res1 = kakao_keyword_search(query=q, x=x, y=y, radius_m=r, size=size, page=1)
+            res2 = kakao_keyword_search(query=q, x=x, y=y, radius_m=r, size=size, page=2) if res1 else []
+            res = merge_places(res1, res2)
+            if res:
+                return res, q, r
+
+    return [], queries[0] if queries else chosen_query, radius_m
+
+
+# =========================
+# 1) 선택 UI
+# =========================
+keys = (
+    "tone",
+    "face_shape",
+    "hair_type",
+    "preferred_length",
+    "mood",
+    "current_hair_length",
+    "bangs_status",
+    "styling_level",
+)
+for k in keys:
+    if k not in st.session_state:
+        st.session_state[k] = None
+
+steps_done = sum(1 for k in keys if st.session_state[k] is not None)
+st.progress(steps_done / len(keys))
+
+st.header("1) 웜톤 / 쿨톤 선택 (염색 컬러 추천용)")
+tone_cols = st.columns(2, gap="large")
+with tone_cols[0]:
+    select_card(
+        title="웜톤",
+        image_path="웜톤.jpg",
+        desc_md="**자가진단**\n1. 팔목 혈관이 **초록빛**\n2. 피부에 **노란기**가 많음",
+        button_label="✅ 웜톤 선택",
+        on_click_value="웜",
+        session_key="tone",
+        button_key="btn_tone_warm",
+        img_width=130,
+        selected=(st.session_state["tone"] == "웜"),
+    )
+with tone_cols[1]:
+    select_card(
+        title="쿨톤",
+        image_path="쿨톤.jpg",
+        desc_md="**자가진단**\n1. 팔목 혈관이 **파란빛**\n2. 피부에 **붉은기**가 많음",
+        button_label="✅ 쿨톤 선택",
+        on_click_value="쿨",
+        session_key="tone",
+        button_key="btn_tone_cool",
+        img_width=130,
+        selected=(st.session_state["tone"] == "쿨"),
+    )
+if st.button("tone 초기화", key="reset_tone", type="secondary"):
+    st.session_state["tone"] = None
+    st.rerun()
+
+st.divider()
+
+st.header("2) 얼굴형 선택")
+FACE_CHOICES = [
+    ("계란형", "계란형.png", "광대 X, 턱 X - 광대와 턱 골격이 두드러지지 않음"),
+    ("마름모형", "마름모형.png", "광대 O, 턱 X - 광대가 부각됨"),
+    ("하트형", "하트형.png", "광대 O 턱 △ - 광대가 넓고 턱이 상대적으로 좁음"),
+    ("땅콩형", "땅콩형.png", "광대 O 턱 O - 광대와 턱 골격이 모두 있음"),
+    ("육각형", "육각형.png", "광대 X 턱 O - 턱선이 각진 편"),
+    ("둥근형", "둥근형.png", "광대 X 턱 X - 전체적으로 둥근 인상"),
+]
+rows = [FACE_CHOICES[:3], FACE_CHOICES[3:]]
+for r_i, r in enumerate(rows):
+    cols = st.columns(3, gap="large")
+    for col, (name, img, desc) in zip(cols, r):
+        with col:
+            select_card(
+                title=name,
+                image_path=img,
+                desc_md=desc,
+                button_label=f"✅ {name} 선택",
+                on_click_value=name,
+                session_key="face_shape",
+                button_key=f"btn_face_{r_i}_{name}",
+                img_width=160,
+                selected=(st.session_state["face_shape"] == name),
             )
+if st.button("face_shape 초기화", key="reset_face", type="secondary"):
+    st.session_state["face_shape"] = None
+    st.rerun()
+
+st.divider()
+
+st.header("3) 모발 타입 선택")
+hair_cols = st.columns(2, gap="large")
+with hair_cols[0]:
+    select_card(
+        title="직모",
+        image_path="직모.png",
+        button_label="✅ 직모 선택",
+        on_click_value="직모",
+        session_key="hair_type",
+        button_key="btn_hair_straight",
+        img_width=100,
+        selected=(st.session_state["hair_type"] == "직모"),
+    )
+with hair_cols[1]:
+    select_card(
+        title="곱슬",
+        image_path="곱슬.png",
+        button_label="✅ 곱슬 선택",
+        on_click_value="곱슬",
+        session_key="hair_type",
+        button_key="btn_hair_curly",
+        img_width=100,
+        selected=(st.session_state["hair_type"] == "곱슬"),
+    )
+if st.button("hair_type 초기화", key="reset_hair", type="secondary"):
+    st.session_state["hair_type"] = None
+    st.rerun()
+
+st.divider()
+
+st.header("4) 기장 선호도 선택")
+st.session_state["preferred_length"] = st.radio(
+    "원하는 전체 기장 느낌을 선택하세요.",
+    options=["짧게", "중간", "길게"],
+    index=["짧게", "중간", "길게"].index(st.session_state["preferred_length"]) if st.session_state["preferred_length"] else 1,
+    horizontal=True,
+)
 
-        for item in items:
-            title = item.get("title", "추천 BGM")
-            href = item.get("href", "")
-            if "youtube.com/watch" in href and is_youtube_video_available(href):
-                return f"{title} (자동 추천)", href
-    except Exception:
-        pass
-
-    return "재생 가능한 BGM을 찾지 못해 기본 라이브를 대신 재생합니다", "https://www.youtube.com/watch?v=jfKfPfyJRdk"
-
-
-def extract_country_from_destination(name_kr: str):
-    """도시명 (국가명) 문자열에서 국가명만 추출합니다."""
-    if "(" in name_kr and ")" in name_kr:
-        return name_kr.split("(")[-1].replace(")", "").strip()
-    return name_kr.strip()
+st.header("5) 원하는 이미지/무드 선택")
+st.session_state["mood"] = st.selectbox(
+    "원하는 분위기를 선택하세요.",
+    options=MOOD_CHOICES,
+    index=MOOD_CHOICES.index(st.session_state["mood"]) if st.session_state["mood"] in MOOD_CHOICES else 0,
+)
 
+st.header("6) 현재 머리 길이")
+length_options = ["숏", "단발", "중단발", "장발"]
+st.session_state["current_hair_length"] = st.radio(
+    "현재 길이를 선택하세요.",
+    options=length_options,
+    index=length_options.index(st.session_state["current_hair_length"]) if st.session_state["current_hair_length"] in length_options else 1,
+    horizontal=True,
+)
 
-def get_regret_risk_warnings(style: str, destination_name: str, reason_text: str):
-    """여행 스타일 미스매치 + 목적지의 보편적 리스크를 후회 가능성 경고로 반환합니다."""
-    text = f"{destination_name} {reason_text}".lower()
-    city = destination_name.split("(")[0].strip()
-    destination_traits = {
-        "쇼핑/도시": ["쇼핑", "야경", "도시", "몰", "백화점", "city", "nightlife"],
-        "휴양/바다": ["휴양", "리조트", "해변", "바다", "비치", "beach"],
-        "관광/유적": ["관광", "유적", "박물관", "역사", "궁전", "성당", "heritage"],
-        "대자연/트레킹": ["대자연", "트레킹", "하이킹", "산", "국립공원", "빙하", "safari"],
-        "미식/로컬푸드": ["미식", "로컬푸드", "야시장", "맛집", "레스토랑", "gourmet"],
-    }
-    mismatch_messages = {
-        "휴양/바다 (물놀이)": {
-            "쇼핑/도시": "⚠️ 이 도시는 쇼핑/야경 중심이라 물놀이·휴양 비중이 기대보다 낮을 수 있어요.",
-            "관광/유적": "⚠️ 이 여행지는 역사·도보 관광 비중이 있어 완전 휴양형 여행과는 결이 다를 수 있어요.",
-        },
-        "관광/유적 (많이 걷기)": {
-            "쇼핑/도시": "⚠️ 이 도시는 쇼핑/야경 중심이라 관광지를 많이 보는 스타일과는 맞지 않을 수 있습니다.",
-            "휴양/바다": "⚠️ 휴양 중심 동선이면 유적·역사 탐방 밀도가 낮아 아쉬울 수 있어요.",
-        },
-        "쇼핑/도시": {
-            "대자연/트레킹": "⚠️ 이 목적지는 자연/트레킹 중심이라 쇼핑 인프라가 제한적일 수 있어요.",
-            "휴양/바다": "⚠️ 휴양지 특성상 대형 쇼핑 스폿이 적어 도시형 쇼핑 여행과 결이 다를 수 있어요.",
-        },
-        "대자연/트레킹": {
-            "쇼핑/도시": "⚠️ 도시/쇼핑 비중이 높아 대자연 체험 시간을 충분히 확보하기 어려울 수 있어요.",
-            "휴양/바다": "⚠️ 해변 휴양 중심 일정이면 트레킹 강도가 기대보다 약할 수 있어요.",
-        },
-        "미식/로컬푸드": {
-            "대자연/트레킹": "⚠️ 자연/트레킹 위주 여행지는 식도락 선택지가 제한될 수 있어요.",
-        },
-    }
+st.header("7) 앞머리 유무")
+bang_options = ["앞머리 있음", "앞머리 없음", "만들 의향 있음"]
+st.session_state["bangs_status"] = st.radio(
+    "앞머리 상태를 선택하세요.",
+    options=bang_options,
+    index=bang_options.index(st.session_state["bangs_status"]) if st.session_state["bangs_status"] in bang_options else 0,
+    horizontal=True,
+)
 
-    generic_risk_rules = [
-        {
-            "keywords": ["스위스", "아이슬란드", "두바이", "런던", "뉴욕", "파리", "싱가포르"],
-            "message": "⚠️ 현지 물가가 높은 편이라 식비·교통비·입장료가 예상보다 커질 수 있어요.",
-        },
-        {
-            "keywords": ["런던", "파리", "암스테르담", "아이슬란드", "영국"],
-            "message": "⚠️ 비·강풍 등 변덕스러운 날씨로 실외 일정이 자주 바뀔 수 있어요.",
-        },
-        {
-            "keywords": ["로마", "바르셀로나", "파리", "방콕"],
-            "message": "⚠️ 관광객이 많은 지역은 소매치기·잡상인 이슈가 있어 동선별 주의가 필요해요.",
-        },
-    ]
-
-    distance_risk_rules = [
-        {
-            "keywords": ["미국", "캐나다", "영국", "프랑스", "독일", "스페인", "포르투갈", "이탈리아", "아이슬란드"],
-            "message": "⚠️ 장거리 노선은 비행시간이 길고 시차 적응이 필요해, 실제 관광 가능한 시간이 예상보다 줄 수 있어요.",
-        },
-        {
-            "keywords": ["이집트", "크로아티아", "포르투갈", "핀란드", "체코", "헝가리", "오스트리아", "노르웨이"],
-            "message": "⚠️ 출발일/도시 조합에 따라 직항이 없거나 좌석이 적어 경유 대기시간이 길어질 수 있어요.",
-        },
-    ]
-
-    local_adaptation_rules = [
-        {
-            "keywords": ["인도", "이집트", "몽골", "라오스", "베트남", "태국"],
-            "message": "⚠️ 향신료·조리 방식·수질 차이로 음식이 낯설 수 있어 첫날은 무난한 메뉴로 적응하는 편이 안전해요.",
-        },
-        {
-            "keywords": ["두바이", "아랍에미리트", "카이로", "울란바토르"],
-            "message": "⚠️ 기온 편차(한낮 고온/야간 저온)나 건조한 공기로 컨디션이 흔들릴 수 있어 복장/보습 대비가 필요해요.",
-        },
-        {
-            "keywords": ["런던", "암스테르담", "아이슬란드", "뉴질랜드"],
-            "message": "⚠️ 날씨 변동 폭이 큰 지역이라 같은 날에도 비·바람이 반복될 수 있어 실내 대안 동선을 준비해 두세요.",
-        },
-    ]
-
-    city_specific_risks = {
-        "뉴욕": "⚠️ 맨해튼 중심 숙소/교통비가 높아 보이는 예산보다 현지 지출이 빠르게 커질 수 있어요.",
-        "파리": "⚠️ 주요 관광지는 대기줄이 길어 사전 예약이 없으면 하루 동선이 크게 밀릴 수 있어요.",
-        "런던": "⚠️ 지하철 파업·공사 이슈가 간헐적으로 있어 이동 동선 플랜B를 준비하는 것이 좋아요.",
-        "방콕": "⚠️ 출퇴근 시간대 교통체증이 심해, 지도상 거리보다 이동시간이 2배 이상 걸릴 수 있어요.",
-        "도쿄": "⚠️ 러시아워 전철 혼잡도가 높아 캐리어 이동은 피크 시간을 피하는 편이 좋아요.",
-        "로마": "⚠️ 인기 유적지는 휴관일·예약 슬롯 변동이 잦아 일정 확정 전에 운영시간 재확인이 필요해요.",
-    }
+st.header("8) 스타일링 난이도 선호")
+styling_options = ["손질 거의 안 함", "보통", "스타일링 가능"]
+st.session_state["styling_level"] = st.radio(
+    "평소 스타일링 가능 수준을 선택하세요.",
+    options=styling_options,
+    index=styling_options.index(st.session_state["styling_level"]) if st.session_state["styling_level"] in styling_options else 1,
+    horizontal=True,
+)
 
-    detected_traits = {
-        trait
-        for trait, keywords in destination_traits.items()
-        if any(keyword in text for keyword in keywords)
-    }
+st.divider()
+
+
+# =========================
+# 5) GPT 추천(3개)
+# =========================
+st.header("9) GPT 추천 키워드 3개(실존 스타일 용어)")
+
+tone = st.session_state["tone"]
+face_shape = st.session_state["face_shape"]
+hair_type = st.session_state["hair_type"]
+preferred_length = st.session_state["preferred_length"]
+mood = st.session_state["mood"]
+current_hair_length = st.session_state["current_hair_length"]
+bangs_status = st.session_state["bangs_status"]
+styling_level = st.session_state["styling_level"]
+
+m1, m2, m3, m4 = st.columns(4)
+m1.metric("tone", tone or "-")
+m2.metric("face_shape", face_shape or "-")
+m3.metric("hair_type", hair_type or "-")
+m4.metric("mood", mood or "-")
+
+color_recommendations = build_color_recommendations(tone or "", mood or "")
+color_candidates = [c for c, _ in color_recommendations]
+
+if tone:
+    st.subheader("🎨 헤어스타일과 어울리는 염색 컬러 추천")
+    if color_recommendations:
+        for color, reason in color_recommendations:
+            st.write(f"- **{color}**: {reason}")
+    else:
+        st.info("톤/무드 선택 후 컬러 추천이 표시됩니다.")
 
-    warnings = []
-    for trait in detected_traits:
-        warning = mismatch_messages.get(style, {}).get(trait)
-        if warning and warning not in warnings:
-            warnings.append(warning)
-
-    for rule in generic_risk_rules:
-        if any(keyword.lower() in text for keyword in rule["keywords"]):
-            if rule["message"] not in warnings:
-                warnings.append(rule["message"])
-
-    for rule in distance_risk_rules:
-        if any(keyword.lower() in text for keyword in rule["keywords"]):
-            if rule["message"] not in warnings:
-                warnings.append(rule["message"])
-
-    for rule in local_adaptation_rules:
-        if any(keyword.lower() in text for keyword in rule["keywords"]):
-            if rule["message"] not in warnings:
-                warnings.append(rule["message"])
-
-    for keyword, message in city_specific_risks.items():
-        if keyword in city and message not in warnings:
-            warnings.append(message)
-
-    fallback_messages = [
-        "⚠️ 성수기에는 항공권·숙소 가격이 급등해 같은 예산으로 체감 퀄리티가 낮아질 수 있어요.",
-        "⚠️ 관광지 오픈시간/휴무일이 수시로 바뀌므로 핵심 스팟은 공식 사이트에서 재확인하세요.",
-        "⚠️ 현지 교통 파업·행사·우천 변수로 당일 동선이 바뀔 수 있어 대체 코스를 미리 정해두는 게 좋아요.",
-    ]
-
-    for message in fallback_messages:
-        if len(warnings) >= 3:
-            break
-        if message not in warnings:
-            warnings.append(message)
+all_selected = all([
+    tone,
+    face_shape,
+    hair_type,
+    preferred_length,
+    mood,
+    current_hair_length,
+    bangs_status,
+    styling_level,
+])
 
-    return warnings
+hint_terms = build_auto_terms(face_shape or "", preferred_length or "중간", mood or "단정한")
 
+if "gpt_queries" not in st.session_state:
+    st.session_state["gpt_queries"] = []
+if "gpt_reasons" not in st.session_state:
+    st.session_state["gpt_reasons"] = []
 
-def get_destination_issue_summary(destination_name: str):
-    """검색 결과 스니펫을 바탕으로 여행지의 자주 언급되는 이슈를 요약합니다."""
-    search_query = f"{destination_name} 여행 단점 문제점 주의할 점"
+gpt_btn = st.button("✨ GPT 추천 검색어 3개 만들기", key="btn_make_gpt_queries", use_container_width=True, disabled=(not all_selected))
 
+if gpt_btn:
     try:
-        with DDGS() as ddgs:
-            items = list(
-                ddgs.text(
-                    keywords=search_query,
-                    region="kr-kr",
-                    safesearch="moderate",
-                    max_results=4,
-                )
+        with st.spinner("GPT가 검색어 3개를 추천하는 중..."):
+            qs, rs = make_queries_with_openai(
+                api_key=OPENAI_API_KEY,
+                tone=tone,
+                face_shape=face_shape,
+                hair_type=hair_type,
+                preferred_length=preferred_length,
+                mood=mood,
+                current_hair_length=current_hair_length,
+                bangs_status=bangs_status,
+                styling_level=styling_level,
+                hint_terms=hint_terms,
+                color_candidates=color_candidates,
             )
-
-        if not items:
-            return ["검색 기반 문제점을 찾지 못했어요. 최신 후기는 출발 전 다시 확인해 주세요."], None
-
-        issue_summaries = []
-        for item in items[:3]:
-            title = item.get("title", "검색 결과")
-            snippet = item.get("body", "요약 정보 없음")
-            issue_summaries.append(f"- **{title}**: {snippet}")
-
-        source = items[0].get("href")
-        return issue_summaries, source
-    except Exception as exc:
-        return [f"문제점 검색 요약을 가져오지 못했어요: {exc}"], None
-
-
-def _summarize_entry_requirement_from_search(country: str):
-    """검색 결과 스니펫을 바탕으로 비자/입국 요건을 요약합니다."""
-    search_query = f"{country} 대한민국 여권 비자 체류 기간 ETA ESTA 여권 유효기간"
-    search_results_url = f"https://duckduckgo.com/?q={quote_plus(search_query)}"
-
-    fallback = {
-        "visa": "검색 결과 기준 최신 정책 확인 필요",
-        "stay": "검색 결과에서 체류기간 확인 필요",
-        "eta": "검색 결과에서 ETA/ESTA 여부 확인 필요",
-        "passport": "대부분 국가에서 6개월 이상 유효기간 권장",
-        "source": search_results_url,
-    }
+            st.session_state["gpt_queries"] = qs
+            st.session_state["gpt_reasons"] = rs
+    except Exception as e:
+        st.error(f"GPT 호출 오류: {e}")
+
+chosen_query = ""
+chosen_idx = 0
+if st.session_state["gpt_queries"]:
+    options = [f"🤖 GPT 추천 {i + 1}: {q}" for i, q in enumerate(st.session_state["gpt_queries"])]
+    chosen = st.radio("아래 GPT 추천 키워드(3개) 중 하나로 1차 검색합니다.", options=options, index=0, key="auto_query_radio")
+    chosen_idx = options.index(chosen)
+    chosen_query = st.session_state["gpt_queries"][chosen_idx]
+
+    reason = st.session_state["gpt_reasons"][chosen_idx] if chosen_idx < len(st.session_state["gpt_reasons"]) else ""
+    if reason:
+        st.info(f"GPT 추천 이유: {reason}")
+else:
+    st.warning("아직 GPT 추천 키워드가 없어요. 위 버튼을 눌러 생성해주세요.")
+
+st.divider()
+
+
+# =========================
+# 6) Kakao Local 검색 + 웹후기 기반 확장검색
+# =========================
+st.header("10) (웹 후기 분석)으로 유명 스타일을 찾고 확장 검색하기")
+
+address = st.text_input("내 위치(주소)를 입력해주세요 (예: 서울시 서대문구 연세로 50)", key="input_address")
+radius = st.slider("검색 반경(미터)", 500, 10000, 3000, step=500, key="radius_slider")
+
+use_review_expansion = st.toggle("웹 후기 기반 확장검색 사용", value=True)
+topn_for_review = st.slider("후기 분석할 후보 개수(상위 N개)", 3, 15, 10, step=1)
+expansion_queries_n = st.slider("확장 검색어 개수", 1, 3, 3, step=1)
+
+auto_fallback = st.toggle("검색어 자동 완화(fallback) 사용", value=True)
+result_size = st.slider("검색 결과 개수(size)", 5, 20, 15, step=1)
+
+find_btn = st.button("📍 (1차+확장) 근처 미용실 찾기", key="btn_find_salon", use_container_width=True)
+
+if find_btn:
+    if not all_selected:
+        st.error("모든 사용자 선택 항목을 완료해주세요.")
+        st.stop()
+    if not st.session_state["gpt_queries"] or not chosen_query.strip():
+        st.error("먼저 GPT 추천 검색어(3개)를 생성하고 하나를 선택해주세요.")
+        st.stop()
+    if not address.strip():
+        st.error("주소를 입력해주세요.")
+        st.stop()
 
     try:
-        with DDGS() as ddgs:
-            items = list(
-                ddgs.text(
-                    keywords=search_query,
-                    region="kr-kr",
-                    safesearch="moderate",
-                    max_results=5,
-                )
-            )
-
-        if not items:
-            return fallback
-
-        text_blob = " ".join(
-            [item.get("title", "") + " " + item.get("body", "") for item in items]
-        )
-
-        visa = fallback["visa"]
-        if "무비자" in text_blob:
-            visa = "무비자 가능 (검색 결과 기반)"
-        elif "비자 필요" in text_blob or "사증" in text_blob:
-            visa = "비자 필요 가능성 높음 (검색 결과 기반)"
-
-        stay = fallback["stay"]
-        stay_match = re.search(r"(\d{1,3})\s*일", text_blob)
-        if stay_match:
-            stay = f"약 {stay_match.group(1)}일 내외 (검색 결과 기반)"
-
-        eta = fallback["eta"]
-        if "ESTA" in text_blob:
-            eta = "ESTA 필요 가능성 있음 (검색 결과 기반)"
-        elif "eTA" in text_blob or "ETA" in text_blob or "NZeTA" in text_blob:
-            eta = "ETA/eTA 필요 가능성 있음 (검색 결과 기반)"
-        elif "불필요" in text_blob and ("ETA" in text_blob or "ESTA" in text_blob):
-            eta = "ETA/ESTA 불필요 가능성 있음 (검색 결과 기반)"
-
-        passport = fallback["passport"]
-        if "6개월" in text_blob:
-            passport = "입국 시 여권 유효기간 6개월 이상 필요 가능성 높음"
-        elif "3개월" in text_blob:
-            passport = "출국 예정일 기준 3개월 이상 필요 가능성 있음"
-        elif "150일" in text_blob:
-            passport = "입국일 기준 150일 이상 필요 가능성 있음"
-
-        return {
-            "visa": visa,
-            "stay": stay,
-            "eta": eta,
-            "passport": passport,
-            "source": search_results_url,
-        }
-    except Exception:
-        return fallback
-
-
-def get_entry_requirement_for_korean_passport(destination_name: str):
-    """대한민국 여권 기준 비자/입국 요건을 반환합니다."""
-    country = extract_country_from_destination(destination_name)
-    requirement = ENTRY_REQUIREMENTS_BY_COUNTRY.get(country)
-
-    if requirement:
-        return country, requirement, False
-
-    searched_requirement = _summarize_entry_requirement_from_search(country)
-    return country, searched_requirement, True
-
-
-def render_kakao_share_copy_button(share_text: str):
-    """카카오톡 공유용 텍스트를 클립보드에 복사하는 버튼을 렌더링합니다."""
-    safe_text = json.dumps(share_text)
-
-    components.html(
-        f"""
-        <div style="margin-top:8px; margin-bottom:8px;">
-            <button id="kakao-copy-btn"
-                style="
-                    background:#FEE500;
-                    color:#191919;
-                    border:none;
-                    border-radius:10px;
-                    padding:10px 14px;
-                    font-weight:700;
-                    cursor:pointer;
-                ">
-                📋 카카오톡 공유 텍스트 복사
-            </button>
-            <p id="kakao-copy-status" style="margin-top:8px; font-size:14px;"></p>
-        </div>
-        <script>
-            const button = document.getElementById("kakao-copy-btn");
-            const status = document.getElementById("kakao-copy-status");
-            const textToCopy = {safe_text};
-
-            button.addEventListener("click", async () => {{
-                try {{
-                    await navigator.clipboard.writeText(textToCopy);
-                    status.textContent = "복사 완료! 친구 단톡방에 바로 붙여넣어 투표를 받아보세요 🙌";
-                }} catch (error) {{
-                    status.textContent = "브라우저 권한 문제로 자동 복사에 실패했어요. 아래 텍스트를 수동 복사해 주세요.";
-                }}
-            }});
-        </script>
-        """,
-        height=120,
-    )
-
-
-# 2. 사이드바 (유지)
-with st.sidebar:
-    api_key = st.text_input("OpenAI API Key를 입력하세요", type="password")
-    weather_api_key = st.text_input("OpenWeather API Key를 입력하세요", type="password")
-    st.markdown("---")
-    st.markdown("### 🌐 외부 정보 연동")
-    st.caption("대표 이미지/축제는 DuckDuckGo, 날씨는 OpenWeather API를 사용합니다.")
-
-    st.markdown("---")
-    st.write("💡 **팁**")
-    st.write("- **'일주일 이상'**을 선택해야 유럽/미주 등 장거리 추천이 나옵니다.")
-    st.write("- **'모험가'**를 선택하면 더 이색적인 곳이 나옵니다.")
-    st.write("- 오른쪽 아래 **☁️ 버튼**을 누르면 재추천/일정 상담 챗봇이 열립니다.")
-
-# 3. 메인 화면 입력 (유지)
-st.markdown("### 📋 여행 스타일을 골라주세요")
-
-col1, col2 = st.columns(2)
-with col1:
-    # 기간 선택
-    duration = st.selectbox("여행 기간", [
-        "1박 2일", "2박 3일", "3박 4일",
-        "4박 5일", "일주일 (6박 7일)", "일주일 이상 (장기/유럽/미주 가능)"
-    ])
-    companion = st.selectbox("동행 여부", ["혼자", "친구/연인", "가족", "반려동물"])
-
-    # 난이도
-    difficulty = st.selectbox("여행 난이도", [
-        "쉬움 (힐링: 직항, 한국인 많음, 편한 인프라)",
-        "모험가 (탐험: 남들 안 가는 곳, 로컬 감성, 경유 OK)"
-    ])
-
-with col2:
-    style = st.selectbox("여행 스타일", ["휴양/바다 (물놀이)", "관광/유적 (많이 걷기)", "미식/로컬푸드", "쇼핑/도시", "대자연/트레킹"])
-    budget_level = st.selectbox("예산 수준", ["가성비 (아끼기)", "적당함 (평균)", "럭셔리 (플렉스)"])
-    no_drive = st.checkbox("운전 못해요ㅠㅠ (렌트카 없이 다니고 싶어요)")
-
-today = datetime.now().date()
-travel_dates = st.date_input(
-    "여행 날짜 (선택)",
-    value=(today, today),
-    min_value=today,
-    help="오늘 이후 일정만 선택할 수 있어요. 선택한 기간 기준으로 평균 기온/강수량과 우기·태풍 정보를 안내합니다.",
-)
-
-etc_req = st.text_input("특별 요청 (예: 사막이 보고 싶어요, 미술관 투어 원함)")
-
-# 4. 추천 버튼
-if st.button("🚀 여행지 3곳 추천받기"):
-    if not api_key:
-        st.error("⚠️ 사이드바에 OpenAI API Key를 먼저 입력해주세요!")
-    else:
-        with st.spinner("AI가 전 세계 지도를 펼쳐 놓고 고민 중입니다..."):
-            try:
-                client = OpenAI(api_key=api_key)
-
-                # 프롬프트 수정: 장거리 여행 시 대륙 제한 해제
-                prompt = f"""
-                당신은 전 세계를 여행한 베테랑 가이드입니다. 사용자 조건에 맞는 여행지 3곳을 추천하세요.
-
-                [사용자 정보]
-                - 난이도: {difficulty}
-                - 기간: {duration}
-                - 스타일: {style}
-                - 운전 가능 여부: {'어려움 (렌트카 없이 이동 선호)' if no_drive else '가능'}
-                - 예산: {budget_level}
-                - 동행: {companion}
-                - 추가요청: {etc_req if etc_req else '없음'}
-
-                [🚨 거리 및 지역 추천 로직 (수정됨)]
-                1. **단거리 ('1박 2일' ~ '4박 5일'):**
-                   - 물리적으로 먼 곳은 불가능합니다. **한국 국내, 일본, 중국, 대만, 홍콩, 마카오, 블라디보스톡** 등 비행시간 5시간 이내 지역만 추천하세요.
-
-                2. **장거리 ('일주일' ~ '일주일 이상'):**
-                   - **아시아에 국한되지 마세요! 전 세계로 눈을 돌리세요.**
-                   - 예산이 '적당함' 이상이고 기간이 길다면 **유럽(서유럽/동유럽), 미주(미국/캐나다), 대양주(호주/뉴질랜드), 중동(튀르키예/두바이)** 등을 적극 추천하세요.
-                   - 물론 사용자가 휴양을 원하면 동남아도 가능하지만, **'유럽이나 다른 대륙'을 우선적으로 고려**해보세요.
-
-                3. **난이도별 차별화:**
-                   - **'쉬움'**: 파리, 런던, 로마, 시드니, 뉴욕, 싱가포르 등 유명하고 인프라 좋은 곳.
-                   - **'모험가'**:
-                     - 아시아: 몽골, 라오스, 치앙마이, 사파 등.
-                     - 유럽/기타: 포르투갈, 크로아티아, 아이슬란드, 튀르키예 카파도키아, 이집트 등 이색적인 곳.
-                     - **(금지어 적용 유지)**: 다낭, 방콕, 오사카, 세부 등 너무 뻔한 곳은 '모험가'에게 추천 금지.
-
-                4. **공통 제약:**
-                   - 대한민국 외교부 여행 금지 국가 절대 제외.
-                   - 사용자가 "운전 못해요ㅠㅠ"를 체크한 경우, 특히 휴양지 추천 시 렌터카 의존도가 높은 지역(대중교통/셔틀/도보 이동이 불편한 지역)은 제외하세요.
-
-                반드시 아래 JSON 포맷으로 답변하세요.
-                {{
-                    "destinations": [
-                        {{
-                            "name_kr": "도시명 (국가명)",
-                            "airport_code": "IATA공항코드(3자리)",
-                            "latitude": 위도(숫자),
-                            "longitude": 경도(숫자),
-                            "reason": "기간과 대륙을 고려한 추천 이유",
-                            "itinerary": [
-                                "DAY 1: 오전/오후/저녁 동선을 포함한 상세 일정",
-                                "DAY 2: 이동시간/예약팁/식사 추천 포함",
-                                "..."
-                            ],
-                            "total_budget": "총 예상 비용 (1인, 왕복항공 포함, KRW)",
-                            "budget_detail": [
-                                "왕복 항공권: 000,000원 (성수기/비수기 범위)",
-                                "숙소: 1박 000,000원 x N박 = 000,000원",
-                                "식비: 1일 00,000원 x N일 = 000,000원",
-                                "교통/입장료/투어/기타 비용"
-                            ]
-                        }}
-                    ]
-                }}
-
-                [일정/예산 품질 규칙]
-                - itinerary는 문자열 하나가 아니라 '일자별 리스트'로 반환하세요. 최소 3개 이상.
-                - 각 일자 항목에는 오전/오후/저녁 활동과 이동 팁을 포함하세요.
-                - total_budget과 budget_detail은 한국 원화 기준으로 작성하세요.
-                - budget_detail은 실제 여행자가 참고 가능한 현실적인 숫자로 작성하세요.
-                - 예산 수준별 산정 기준을 반드시 반영하세요.
-                  - '가성비 (아끼기)': 저가 항공(LCC) + 호스텔/게스트하우스(또는 2성급) + 대중교통/도보 중심으로 보수적으로 계산.
-                  - '적당함 (평균)': 일반 항공 + 3성급 전후 호텔 + 대중교통/택시 혼합 기준으로 계산.
-                  - '럭셔리 (플렉스)': 국적기/프리미엄 항공 + 5성급 호텔 + 택시/프라이빗 투어를 포함한 상향 기준으로 계산.
-                - 예산 수치는 여행 기간, 성수기 여부, 목적지 물가를 반영해 과도하게 낙관적이지 않게 작성하세요.
-                """
-
-                # temperature 1.1 유지 (다양성)
-                response = client.chat.completions.create(
-                    model="gpt-4o-mini",
-                    messages=[{"role": "user", "content": prompt}],
-                    response_format={"type": "json_object"},
-                    temperature=1.1,
-                )
-
-                result = json.loads(response.choices[0].message.content)
-                destinations = result['destinations']
-                st.session_state.latest_destinations = destinations
-
-                st.success(f"'{duration}' 동안 다녀오기 좋은, 전 세계 여행지를 엄선했습니다! 🌍")
-
-                tabs = st.tabs([d['name_kr'] for d in destinations])
-
-                for i, tab in enumerate(tabs):
-                    with tab:
-                        dest = destinations[i]
-                        st.header(f"📍 {dest['name_kr']}")
-
-                        map_data = pd.DataFrame({'lat': [dest['latitude']], 'lon': [dest['longitude']]})
-                        st.map(map_data, zoom=4)
-
-                        image_url, image_error = get_landmark_image(dest['name_kr'])
-                        food_name, food_image_url, food_image_error = get_representative_food(dest['name_kr'])
-
-                        st.markdown("#### 🖼️ 여행지/먹거리 미리보기")
-                        image_col, food_col = st.columns(2)
-
-                        with image_col:
-                            if image_url:
-                                st.image(
-                                    image_url,
-                                    caption=f"{dest['name_kr']} 대표 랜드마크",
-                                    width=220,
-                                )
-                            else:
-                                st.caption(image_error)
-
-                        with food_col:
-                            if food_image_url:
-                                st.image(
-                                    food_image_url,
-                                    caption=f"대표 먹거리: {food_name}",
-                                    width=220,
-                                )
-                            else:
-                                st.caption(food_image_error)
-
-                        st.info(f"💡 **추천 이유**: {dest['reason']}")
-
-                        regret_risk_warnings = get_regret_risk_warnings(style, dest['name_kr'], dest['reason'])
-                        weather_summary = get_weather_summary(dest['latitude'], dest['longitude'], weather_api_key)
-                        seasonal_note = get_seasonal_travel_note(dest['name_kr'], dest['latitude'], travel_dates)
-                        festival_summary = get_festival_summary(dest['name_kr'])
-                        country, entry_info, is_search_based = get_entry_requirement_for_korean_passport(dest['name_kr'])
-
-                        regret_ratings, regret_one_liner = build_regret_summary(regret_risk_warnings)
-                        regret_risk_warnings = ensure_minimum_regret_warning(regret_risk_warnings)
-                        weather_emoji, weather_core = build_weather_emoji_display(weather_summary)
-                        budget_summary = build_budget_range_summary(dest['total_budget'])
-                        total_budget_in_manwon = to_manwon_text(dest['total_budget'])
-
-                        st.markdown("#### ✅ 상단 요약")
-                        metric_col1, metric_col2, metric_col3 = st.columns(3)
-                        with metric_col1:
-                            st.metric("추천도", regret_ratings)
-                            st.caption(regret_one_liner)
-                        with metric_col2:
-                            st.markdown("**날씨 핵심**")
-                            st.markdown(f"<div style='font-size: 4rem; line-height: 1;'>{weather_emoji}</div>", unsafe_allow_html=True)
-                            st.caption(weather_core)
-                        with metric_col3:
-                            st.metric("예산 총액", budget_summary)
-                            st.caption(total_budget_in_manwon)
-
-                        with st.expander("🧠 😢 상세", expanded=False):
-                            for warning_message in regret_risk_warnings:
-                                st.warning(warning_message)
-
-                        with st.expander("🌤️ 날씨 자세히", expanded=False):
-                            st.write(weather_summary)
-                            st.markdown("#### 🌦️ 여행 기간 기후/시기 적합성")
-                            st.markdown(seasonal_note)
-
-                        with st.expander("🛂 비자/입국 조건", expanded=False):
-                            st.markdown(
-                                f"""
-                                - **비자 필요 여부**: {entry_info['visa']}
-                                - **체류 가능 기간**: {entry_info['stay']}
-                                - **ESTA / ETA 필요 여부**: {entry_info['eta']}
-                                - **여권 유효기간 조건**: {entry_info['passport']}
-                                """
-                            )
-                            if is_search_based:
-                                st.caption("※ 위 정보는 실시간 검색 요약입니다. 예약/출국 전 외교부 해외안전여행 및 해당국 대사관 공지로 최종 확인하세요.")
-                                if entry_info.get("source"):
-                                    st.link_button("🔎 참고 링크(검색 결과)", entry_info["source"])
-
-                        with st.expander("🎉 축제/이벤트", expanded=False):
-                            st.markdown(festival_summary)
-
-                        bgm_title, bgm_url = get_destination_bgm(dest['name_kr'])
-                        with st.expander("🎵 여행지 무드 BGM", expanded=False):
-                            st.caption(bgm_title)
-                            st.video(bgm_url)
-
-                        with st.expander("🗓️ 일정/예산 상세", expanded=False):
-                            col_a, col_b = st.columns(2)
-                            with col_a:
-                                st.markdown("#### 🗓️ 추천 일정")
-                                itinerary_items = dest.get('itinerary', [])
-                                if isinstance(itinerary_items, list):
-                                    for item in itinerary_items:
-                                        st.markdown(f"- {item}")
-                                else:
-                                    st.write(itinerary_items)
-
-                            with col_b:
-                                st.markdown("#### 💰 예상 예산")
-                                st.success(f"**{dest['total_budget']}**")
-                                budget_items = dest.get('budget_detail', [])
-                                if isinstance(budget_items, list):
-                                    for item in budget_items:
-                                        st.caption(f"• {item}")
-                                else:
-                                    st.caption(budget_items)
-
-                        st.markdown("---")
-                        url = f"https://www.skyscanner.co.kr/transport/flights/sela/{dest['airport_code']}"
-                        st.link_button(f"✈️ {dest['name_kr']} 항공권 검색", url)
-
-                st.markdown("---")
-                st.markdown("### 🗳️ 친구들에게 투표받기")
-                share_options = [f"{idx + 1}. {d['name_kr']}" for idx, d in enumerate(destinations[:3])]
-                share_text = (
-                    "나 이번에 여행 가는데 어디가 좋을까? "
-                    + " ".join(share_options)
-                    + " 투표 좀!"
-                )
-                render_kakao_share_copy_button(share_text)
-                st.caption("예시: 나 이번에 여행 가는데 어디가 좋을까? 1. 몽골(별 쏟아짐) 2. 치앙마이(힐링) 3. 다낭(가성비) 투표 좀!")
-                st.text_area("공유 텍스트 미리보기", value=share_text, height=90)
-
-            except Exception as e:
-                st.error(f"오류가 발생했습니다: {e}")
-
-
-if st.session_state.chat_open:
-    chat_container = st.container(border=True, key="cloud_chat_popup")
-    with chat_container:
-        st.markdown("### ☁️ 재추천 챗봇")
-        st.caption("재추천은 물론, 마음에 드는 여행지의 일정·관광지도 원하는 스타일에 맞춰 추천해 드려요.")
-        for message in st.session_state.chat_messages:
-            with st.chat_message(message["role"]):
-                st.markdown(message["content"])
-
-        user_feedback = st.text_input(
-            "메시지 입력",
-            key="cloud_chat_input",
-            label_visibility="collapsed",
-            placeholder="예: 재추천해줘 / 오사카 3박4일 일정 짜줘 / 비 오는 날 갈만한 관광지 추천해줘",
-        )
-        send_clicked = st.button("전송", key="cloud_chat_send")
-
-    if send_clicked and user_feedback.strip():
-        user_feedback = user_feedback.strip()
-        st.session_state.chat_messages.append({"role": "user", "content": user_feedback})
-
-        profile_summary = (
-            f"기간={duration}, 난이도={difficulty}, 스타일={style}, 예산={budget_level}, 동행={companion}, 운전={no_drive}, 추가요청={etc_req or '없음'}"
-        )
-
-        with st.spinner("피드백 반영해서 다시 골라볼게요..."):
-            try:
-                reply = get_followup_recommendations(
-                    api_key=api_key,
-                    user_message=user_feedback,
-                    destinations=st.session_state.latest_destinations,
-                    profile_summary=profile_summary,
+        with st.spinner("주소를 좌표로 변환 중..."):
+            x, y = kakao_address_to_xy(address.strip())
+
+        with st.spinner("1차: 미용실 검색 중..."):
+            if auto_fallback:
+                base_results, used_q, used_r = search_salons_with_fallback(chosen_query=chosen_query, x=x, y=y, radius_m=radius, size=result_size)
+            else:
+                base_results = kakao_keyword_search(query=chosen_query, x=x, y=y, radius_m=radius, size=result_size, page=1)
+                used_q, used_r = chosen_query, radius
+
+        if not base_results:
+            st.warning("검색 결과가 없어요. 자동 완화 옵션을 켜거나 반경을 늘려보세요.")
+            st.stop()
+
+        st.success(f"1차 검색 성공: '{used_q}' / 반경 {used_r}m / 결과 {len(base_results)}개")
+
+        merged_results = base_results
+        style_map: Dict[str, Dict] = {}
+        expanded_queries: List[str] = []
+
+        if use_review_expansion:
+            candidates = base_results[:topn_for_review]
+            area_hint = " ".join(address.strip().split()[:3]) or address.strip()
+
+            with st.spinner("웹 후기(블로그/웹문서) 스니펫 수집 중..."):
+                snippets = {p.get("place_name", ""): build_review_snippet_for_place(p.get("place_name", ""), area_hint) for p in candidates if p.get("place_name", "")}
+
+            with st.spinner("웹 후기 기반 유명 스타일 태그 분석(GPT)..."):
+                style_map = analyze_styles_from_reviews_with_openai(
+                    api_key=OPENAI_API_KEY,
+                    chosen_query=chosen_query,
+                    places=candidates,
+                    review_snippets=snippets,
                 )
-            except Exception as e:
-                reply = f"재추천 중 오류가 발생했어요: {e}"
 
-        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
-        st.session_state.cloud_chat_input = ""
-        st.rerun()
+            expanded_queries = build_expanded_queries_from_tags(chosen_query=chosen_query, style_map=style_map, max_queries=expansion_queries_n)
+
+            if expanded_queries:
+                with st.spinner("확장 검색어로 추가 검색 중..."):
+                    extra_lists = []
+                    for q in expanded_queries:
+                        if auto_fallback:
+                            res, _, _ = search_salons_with_fallback(chosen_query=q, x=x, y=y, radius_m=radius, size=result_size)
+                            extra_lists.append(res)
+                        else:
+                            extra_lists.append(kakao_keyword_search(query=q, x=x, y=y, radius_m=radius, size=result_size, page=1))
+                merged_results = merge_places(base_results, *extra_lists)
+
+        st.success(f"최종 결과 {len(merged_results)}개")
+        if expanded_queries:
+            st.write("확장 검색어(후기 기반):", ", ".join(expanded_queries))
+
+        map_points = [{"lat": float(r["y"]), "lon": float(r["x"])} for r in merged_results if r.get("x") and r.get("y")]
+        if map_points:
+            st.map(map_points, zoom=13)
+
+        st.subheader("미용실 리스트")
+        for i, r in enumerate(merged_results, start=1):
+            name = r.get("place_name", "")
+            road = r.get("road_address_name", "") or r.get("address_name", "")
+            phone = r.get("phone", "")
+            dist = r.get("distance", "")
+            url = r.get("place_url", "")
+
+            st.markdown(f"### {i}. {name}")
+            if dist:
+                st.write(f"- 거리: **{dist}m**")
+            st.write(f"- 주소: {road}")
+            if phone:
+                st.write(f"- 전화: {phone}")
+            if url:
+                st.write(f"- 카카오맵: {url}")
+            if use_review_expansion and name in style_map:
+                tags = style_map[name].get("tags", [])
+                summary = style_map[name].get("summary", "")
+                if tags:
+                    st.write("- 웹 후기 기반 유명 스타일:", " / ".join(tags))
+                if summary:
+                    st.caption(f"후기 요약: {summary}")
+
+    except Exception as e:
+        st.error(f"오류: {e}")
+
+st.divider()
+
+if st.button("전체 선택/결과 초기화", key="reset_all", type="secondary"):
+    for k in keys:
+        st.session_state[k] = None
+    st.session_state["gpt_queries"] = []
+    st.session_state["gpt_reasons"] = []
+    st.rerun()
 
EOF
)
