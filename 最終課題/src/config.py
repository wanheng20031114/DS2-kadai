"""
設定ファイル
楽天トラベルのURL構成と日付設定を管理する
"""

# 楽天トラベル検索URLのベース
BASE_URL = "https://search.travel.rakuten.co.jp/ds/vacant/searchVacant"

# 検索パラメータ（固定値）
SEARCH_PARAMS = {
    "f_dai": "japan",
    "f_chu": "tiba",           # 千葉県
    "f_shou": "keiyo",         # 京葉エリア（幕張）
    "f_hyoji": "30",           # 1ページあたり30件
    "f_page": "1",
    "f_sort": "hotel",
    "f_heya_su": "1",          # 1部屋
    "f_otona_su": "1",         # 大人1名
    "f_s1": "0",
    "f_s2": "0",
    "f_y1": "0",
    "f_y2": "0",
    "f_y3": "0",
    "f_y4": "0",
    "f_kin2": "0",
    "f_cd": "03",
}

# 日付グループ設定
# TGS 2026: 一般公開日 9/19(土)-9/21(月)
DATE_GROUPS = {
    "tgs_period": {
        "name": "TGS期間",
        "checkin": {"year": 2026, "month": 9, "day": 19},
        "checkout": {"year": 2026, "month": 9, "day": 21},
    },
    "before_tgs": {
        "name": "TGS前週",
        "checkin": {"year": 2026, "month": 9, "day": 12},
        "checkout": {"year": 2026, "month": 9, "day": 14},
    },
    "after_tgs": {
        "name": "TGS翌週",
        "checkin": {"year": 2026, "month": 9, "day": 26},
        "checkout": {"year": 2026, "month": 9, "day": 28},
    },
}

# HTTPリクエストヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}

# スクレイピング設定
REQUEST_DELAY = 2  # リクエスト間隔（秒）

# データベース設定
import os
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "hotels.db")


def build_url(checkin: dict, checkout: dict) -> str:
    """
    日付情報からURLを構築する
    
    Args:
        checkin: {"year": 2026, "month": 9, "day": 19}
        checkout: {"year": 2026, "month": 9, "day": 21}
    
    Returns:
        完全なURL文字列
    """
    params = SEARCH_PARAMS.copy()
    params.update({
        "f_nen1": str(checkin["year"]),
        "f_tuki1": str(checkin["month"]),
        "f_hi1": str(checkin["day"]),
        "f_nen2": str(checkout["year"]),
        "f_tuki2": str(checkout["month"]),
        "f_hi2": str(checkout["day"]),
    })
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_URL}?{query_string}"
