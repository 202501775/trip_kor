import math
import json
from urllib.parse import quote
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from data import get_sample_places


KAKAO_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def search_kakao(query, api_key, category, size=12):
    url = f"{KAKAO_URL}?{urlencode({'query': query, 'size': size, 'sort': 'accuracy'})}"
    request = Request(url, headers={"Authorization": f"KakaoAK {api_key}"})
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    places = []
    for item in payload.get("documents", []):
        places.append(
            {
                "name": item["place_name"],
                "address": item.get("road_address_name") or item.get("address_name", ""),
                "lat": float(item["y"]),
                "lon": float(item["x"]),
                "category": category,
                "phone": item.get("phone", ""),
                "url": item.get("place_url") or f"https://map.kakao.com/link/search/{quote(item['place_name'])}",
                "source": "카카오",
            }
        )
    return places


def fetch_places(region, api_key=None, interests=None):
    if not api_key:
        sample = get_sample_places(region)
        warning = None
        if sample["region"] not in region:
            warning = "API 키가 없어 입력 지역 대신 서울 샘플 데이터를 표시합니다."
        return sample, warning

    interests = interests or []
    attraction_terms = ["가볼만한곳", "관광명소"]
    if "자연·바다" in interests:
        attraction_terms.append("자연 관광지")
    if "액티비티" in interests:
        attraction_terms.append("액티비티")
    if "카페" in interests:
        attraction_terms.append("카페")

    try:
        attractions = []
        seen = set()
        for term in attraction_terms:
            for place in search_kakao(f"{region} {term}", api_key, "관광", 8):
                if place["name"] not in seen:
                    attractions.append(place)
                    seen.add(place["name"])
        restaurants = search_kakao(f"{region} 맛집", api_key, "식당", 15)
        if not attractions or not restaurants:
            raise ValueError("검색 결과가 부족합니다.")
        return {"region": region, "attractions": attractions, "restaurants": restaurants}, None
    except (OSError, ValueError, KeyError) as exc:
        return get_sample_places(region), f"카카오 검색에 실패해 샘플 데이터를 사용합니다: {exc}"


def distance_km(a, b):
    lat1, lon1 = math.radians(a["lat"]), math.radians(a["lon"])
    lat2, lon2 = math.radians(b["lat"]), math.radians(b["lon"])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(value))


def nearest(origin, candidates):
    return min(candidates, key=lambda place: distance_km(origin, place)) if candidates else None
