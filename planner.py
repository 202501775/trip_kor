from datetime import timedelta
from urllib.parse import quote

from places import nearest


MEAL_COST = {"가성비": 14000, "보통": 22000, "여유": 35000}
LODGING_PER_NIGHT = {"가성비": 120000, "보통": 210000, "여유": 340000}
TRANSPORT_PER_DAY = {"대중교통": 10000, "자가용": 16000, "렌터카": 55000}


def _take_rotating(items, index):
    return items[index % len(items)]


def build_itinerary(start_date, days, people, budget_per_person, transport, pace, spend_level, places):
    attractions = places["attractions"]
    restaurants = places["restaurants"]
    attraction_count = {"여유롭게": 2, "적당히": 3, "빡빡하게": 4}[pace]
    used_attractions = set()
    rows = []

    for day in range(days):
        current_date = start_date + timedelta(days=day)
        day_places = []
        remaining = [p for p in attractions if p["name"] not in used_attractions]
        if not remaining:
            used_attractions.clear()
            remaining = attractions[:]

        first = _take_rotating(remaining, day)
        day_places.append(first)
        used_attractions.add(first["name"])
        for _ in range(attraction_count - 1):
            candidates = [p for p in attractions if p["name"] not in used_attractions]
            if not candidates:
                break
            chosen = nearest(day_places[-1], candidates)
            day_places.append(chosen)
            used_attractions.add(chosen["name"])

        lunch = nearest(day_places[0], restaurants) or _take_rotating(restaurants, day)
        dinner = nearest(day_places[-1], [p for p in restaurants if p["name"] != lunch["name"]]) or lunch

        schedule = [("10:00", day_places[0], "관광")]
        schedule.append(("12:00", lunch, "점심"))
        for idx, place in enumerate(day_places[1:], start=1):
            schedule.append((f"{13 + (idx - 1) * 2}:30", place, "관광"))
        schedule.append(("18:30", dinner, "저녁"))

        for time, place, activity in schedule:
            rows.append(
                {
                    "일차": f"{day + 1}일차",
                    "날짜": current_date.strftime("%m/%d"),
                    "시간": time,
                    "구분": activity,
                    "장소": place["name"],
                    "주소": place["address"],
                    "지도": place["url"],
                    "lat": place["lat"],
                    "lon": place["lon"],
                }
            )

    nights = max(days - 1, 0)
    meal_total = people * days * 2 * MEAL_COST[spend_level]
    lodging_total = nights * LODGING_PER_NIGHT[spend_level]
    transport_total = days * TRANSPORT_PER_DAY[transport] * (1 if transport == "렌터카" else people)
    activity_total = people * days * 15000
    estimated_total = meal_total + lodging_total + transport_total + activity_total
    available_total = people * budget_per_person
    budget = {
        "식비": meal_total,
        "숙박": lodging_total,
        "교통": transport_total,
        "입장·체험": activity_total,
        "예상 합계": estimated_total,
        "전체 예산": available_total,
        "잔여 예산": available_total - estimated_total,
    }
    return rows, budget


def lodging_links(region, people, checkin, checkout):
    query = f"{region} {people}인 숙소"
    encoded_query = quote(query)
    return [
        ("네이버에서 숙소 찾기", f"https://search.naver.com/search.naver?query={encoded_query}"),
        ("카카오맵에서 숙소 찾기", f"https://map.kakao.com/link/search/{encoded_query}"),
        ("여기어때에서 확인", "https://www.goodchoice.kr/"),
        ("야놀자에서 확인", "https://www.yanolja.com/"),
    ]
