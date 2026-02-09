import requests
import streamlit as st

KAKAO_REST_API_KEY = st.secrets["KAKAO_REST_API_KEY"].strip()
headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

def call(url, params):
    r = requests.get(url, headers=headers, params=params, timeout=10)
    print("URL:", r.url)
    print("STATUS:", r.status_code)
    print("BODY:", r.text[:300])
    print("-" * 60)

call("https://dapi.kakao.com/v2/local/search/keyword.json", {"query": "미용실", "size": 3})
call("https://dapi.kakao.com/v2/local/search/address.json", {"query": "서울시 서대문구 연세로 50"})
