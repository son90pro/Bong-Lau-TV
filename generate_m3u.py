import datetime
import json
import urllib.parse
import urllib.request

API_BASE_URL = "https://api-v2.chuoichientv.net/v2/matches"
REFERER_URL = "https://lau06.bonglautv1.org/"

SPORT_MAP = {
    "football": "⚽ Bóng Đá",
    "volleyball": "🏐 Bóng Chuyền",
    "basketball": "🏀 Bóng Rổ",
    "tennis": "🎾 Quần Vợt",
    "badminton": "🏸 Cầu Lông",
    "table-tennis": "🏓 Bóng Bàn",
    "esports": "🎮 Thể Thao Điện Tử",
}


def parse_match_time(utc_str):
  try:
    dt = datetime.datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    vn_time = dt.astimezone(datetime.timezone(datetime.timedelta(hours=7)))
    return vn_time.strftime("%H:%M %d/%m")
  except Exception:
    return "LIVE"


def fetch_matches_by_type(match_type):
  url = f"{API_BASE_URL}?type={match_type}&domain=bonglau&page=1&limit=100"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      ),
      "Referer": REFERER_URL,
  }
  req = urllib.request.Request(url, headers=headers)
  try:
    with urllib.request.urlopen(req, timeout=15) as response:
      data = json.loads(response.read().decode("utf-8"))
      return data.get("matches", [])
  except Exception as e:
    print(f"⚠️ Lỗi API type={match_type}: {e}")
    return []


def fetch_all_matches():
  live_matches = fetch_matches_by_type("live")
  hot_matches = fetch_matches_by_type("hot")

  seen_ids = set()
  combined = []

  for match in live_matches + hot_matches:
    m_id = match.get("_id") or match.get("externalId")
    if m_id and m_id not in seen_ids:
      seen_ids.add(m_id)
      combined.append(match)

  return combined


def generate_m3u():
  matches = fetch_all_matches()

  m3u_lines = [
      '#EXTM3U x-tvg-url="" url-tvg="" tvg-shift="0" refreshrate="30"'
  ]
  count_streams = 0

  for match in matches:
    sport_key = str(match.get("sport", "other")).lower()
    group_title = SPORT_MAP.get(sport_key, f"📺 {sport_key.capitalize()}")

    home_team = match.get("teams", {}).get("home", {}).get("name", "Đội A")
    away_team = match.get("teams", {}).get("away", {}).get("name", "Đội B")

    home_logo = match.get("teams", {}).get("home", {}).get("logo", "")
    league_logo = match.get("league", {}).get("logo", "")
    logo_url = home_logo if home_logo else league_logo

    time_str = parse_match_time(match.get("matchTime", ""))

    blv_list = (
        match.get("blvs")
        or match.get("blvs_bonglau")
        or match.get("blvs_nguoitho")
        or []
    )

    for blv in blv_list:
      blv_name = blv.get("name", "Mặc định")
      streams = blv.get("streams", [])

      for stream in streams:
        label = stream.get("label", "HD")
        raw_url = stream.get("url", "").strip()

        # Bỏ qua các link không phải luồng stream m3u8
        if not raw_url or not (".m3u8" in raw_url or "http" in raw_url):
          continue

        display_name = (
            f"[{time_str}] {home_team} vs {away_team} (BLV: {blv_name} |"
            f" {label})"
        )

        # Gắn Pipe Header trực tiếp cho TiviMate / OTT Navigator
        # TiviMate sẽ gửi đúng Referer và User-Agent này khi tải luồng & các file phân đoạn (.ts)
        tivimate_url = (
            f"{raw_url}|Referer=https://lau06.bonglautv1.org/&Origin=https://lau06.bonglautv1.org&User-Agent=Mozilla/5.0"
            " (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like"
            " Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        m3u_lines.append(
            f'#EXTINF:-1 tvg-name="{home_team} vs {away_team}"'
            f' tvg-logo="{logo_url}" group-title="{group_title}",{display_name}'
        )
        m3u_lines.append(tivimate_url)
        count_streams += 1

  with open("playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

  print(f"✅ Đã tạo playlist.m3u thành công với {count_streams} luồng phát.")


if __name__ == "__main__":
  generate_m3u()
    
