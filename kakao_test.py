import re
import requests

RAW = """여기에_카카오_키를_그대로_붙여넣기""".strip()

# 1) 혹시 "REST API Key: xxxx" 같이 복사했으면 키만 추출
m = re.search(r"([0-9a-fA-F]{20,})", RAW)  # 카카오 키는 보통 20자 이상(헥사)
if not m:
    raise SystemExit("❌ 키에서 '키 값'을 찾지 못했어요. Kakao Developers > 앱 키 > REST API Key 값만 복사해 붙여넣어 주세요.")
KAKAO_REST_API_KEY = m.group(1).strip()

# 2) 헤더는 ASCII만 가능하므로 최종 검사
try:
    KAKAO_REST_API_KEY.encode("ascii")
except UnicodeEncodeError:
    raise SystemExit("❌ 키에 한글/이상문자가 섞여 있어요. 키 값만 다시 복사해 붙여넣어 주세요.")

headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

url1 = "https://dapi.kakao.com/v2/local/search/keyword.json"
params1 = {"query": "미용실", "size": 3}

r1 = requests.get(url1, headers=headers, params=params1, timeout=10)
print("키워드 검색 status:", r1.status_code)
print("응답 일부:", r1.text[:200])
