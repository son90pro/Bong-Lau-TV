import datetime
import json
import urllib.request

# API Endpoint & Domain
API_URL = (
    "https://api-v2.chuoichientv.net/v2/matches?type=hot&domain=bonglau&page=1&limit=100"
)
REFERER_URL = "https://lau06.bonglautv1.org/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like"
    " Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Ánh ánh các môn thể thao sang nhóm Tiếng Việt có icon
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
  """Chuyển đổi thời gian từ UTC sang múi giờ Việt Nam (GMT+7)"""
  try:
    dt = datetime.datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
    vn_time = dt.astimezone(datetime.timezone(datetime.timedelta(hours=7)))
    return vn_time.strftime("%H:%M %d/%m")
  except Exception:
    return "LIVE"


def fetch_matches():
  headers = {"User-Agent": USER_AGENT, "Referer": REFERER_URL}
  req = urllib.request.Request(API_URL, headers=headers)
  try:
    with urllib.request.urlopen(req, timeout=15) as response:
      data = json.loads(response.read().decode("utf-8"))
      return data.get("matches", [])
  except Exception as e:
    print(f"❌ Lỗi khi tải dữ liệu từ API: {e}")
    return []


def generate_m3u():
  matches = fetch_matches()

  m3u_lines = [
      '#EXTM3U x-tvg-url="" url-tvg="" tvg-shift="0" refreshrate="30"'
  ]
  count_streams = 0

  for match in matches:
    # 1. Nhóm thể thao
    sport_key = str(match.get("sport", "other")).lower()
    group_title = SPORT_MAP.get(sport_key, f"📺 {sport_key.capitalize()}")

    # 2. Tên đội bóng
    home_team = match.get("teams", {}).get("home", {}).get("name", "Đội A")
    away_team = match.get("teams", {}).get("away", {}).get("name", "Đội B")

    # 3. Logo đội nhà / giải đấu
    home_logo = match.get("teams", {}).get("home", {}).get("logo", "")
    league_logo = match.get("league", {}).get("logo", "")
    logo_url = home_logo if home_logo else league_logo

    # 4. Thời gian trận đấu
    time_str = parse_match_time(match.get("matchTime", ""))

    # 5. Danh sách BLV & Luồng phát
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
        stream_url = stream.get("url", "").strip()

        if not stream_url:
          continue

        # Định dạng gọn nhẹ: Loại bỏ chữ [ĐANG PHÁT] và Tên giải đấu
        display_name = (
            f"[{time_str}] {home_team} vs {away_team} (BLV: {blv_name} |"
            f" {label})"
        )

        # Nối Header Referer & User-Agent trực tiếp vào URL (Chuẩn tương thích ExoPlayer/TiviMate/OTT Navigator)
        playable_url = (
            f"{stream_url}|Referer={REFERER_URL}&User-Agent={USER_AGENT}"
        )

        m3u_lines.append(
            f'#EXTINF:-1 tvg-name="{home_team} vs {away_team}" tvg-logo="{logo_url}"'
            f' group-title="{group_title}",{display_name}'
        )
        m3u_lines.append(f"#EXTVLCOPT:http-referrer={REFERER_URL}")
        m3u_lines.append(f"#EXTVLCOPT:http-user-agent={USER_AGENT}")
        m3u_lines.append(playable_url)
        count_streams += 1

  # Ghi ra file M3U
  with open("playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

  print(f"✅ Đã tạo thành công playlist.m3u với {count_streams} luồng phát.")


if __name__ == "__main__":
  generate_m3u()
    
