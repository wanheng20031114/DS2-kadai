"""
スクレイピングモジュール
楽天トラベルからホテル価格データを取得する
"""

import re
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import requests

from config import (
    HEADERS, 
    REQUEST_DELAY, 
    DATE_GROUPS, 
    DB_PATH,
    build_url
)
from database import HotelDatabase


class HotelScraper:
    """楽天トラベルからホテル情報をスクレイピングするクラス"""
    
    def __init__(self):
        """スクレイパーを初期化する"""
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.db = HotelDatabase(DB_PATH)
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        URLからHTMLを取得する
        
        Args:
            url: 取得するURL
        
        Returns:
            HTMLテキスト、失敗時はNone
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as e:
            print(f"エラー: {e}")
            return None
    
    def extract_walk_minutes(self, access_info: str) -> Optional[int]:
        """
        アクセス情報から徒歩分数を抽出する
        
        Args:
            access_info: アクセス情報テキスト
        
        Returns:
            徒歩分数（整数）、抽出できない場合はNone
        """
        if not access_info:
            return None
        
        # 「徒歩X分」または「歩X分」のパターンを検索
        patterns = [
            r"徒歩(\d+)分",
            r"歩(\d+)分",
            r"(\d+)分.*駅",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, access_info)
            if match:
                return int(match.group(1))
        
        return None
    
    def parse_price(self, price_text: str) -> Optional[int]:
        """
        価格テキストから数値を抽出する
        
        Args:
            price_text: 価格テキスト（例: "132,200"）
        
        Returns:
            価格（整数）
        """
        if not price_text:
            return None
        # カンマと余分な文字を削除
        cleaned = re.sub(r"[^\d]", "", price_text)
        return int(cleaned) if cleaned else None
    
    def parse_review_count(self, review_text: str) -> Optional[int]:
        """
        レビューテキストから件数を抽出する
        
        Args:
            review_text: レビューテキスト（例: "（15610件）"）
        
        Returns:
            レビュー件数
        """
        if not review_text:
            return None
        match = re.search(r"(\d+)件", review_text.replace(",", ""))
        return int(match.group(1)) if match else None
    
    def parse_hotels(self, html: str) -> List[Dict]:
        """
        HTMLからホテル情報を抽出する
        
        Args:
            html: HTMLテキスト
        
        Returns:
            ホテル情報の辞書リスト
        """
        soup = BeautifulSoup(html, "html.parser")
        hotels = []
        
        # ホテルリストアイテムを取得
        hotel_items = soup.select("li.htl-list-card")
        
        for item in hotel_items:
            try:
                hotel = self._parse_hotel_item(item)
                if hotel and hotel.get("min_price"):
                    hotels.append(hotel)
            except Exception as e:
                print(f"パースエラー: {e}")
                continue
        
        return hotels
    
    def _parse_hotel_item(self, item) -> Optional[Dict]:
        """
        ホテルリストアイテムをパースする
        
        Args:
            item: BeautifulSoupのタグオブジェクト
        
        Returns:
            ホテル情報の辞書
        """
        # ホテルID
        hotel_id = item.get("data-map-modal-hotel-no")
        
        # ホテル名
        name_elem = item.select_one("h2.hotel-list__title-text a")
        hotel_name = name_elem.get_text(strip=True) if name_elem else None
        
        # 評価
        rating_elem = item.select_one("p.cstmrEvl strong")
        rating = float(rating_elem.get_text(strip=True)) if rating_elem else None
        
        # レビュー件数
        review_elem = item.select_one("p.cstmrEvl")
        review_text = review_elem.get_text() if review_elem else ""
        review_count = self.parse_review_count(review_text)
        
        # アクセス情報
        access_elem = item.select_one("p.htlAccess span")
        access_info = access_elem.get_text(strip=True) if access_elem else None
        walk_minutes = self.extract_walk_minutes(access_info) if access_info else None
        
        # 最低価格（プランの中で最も安い価格を取得）
        min_price = None
        price_elems = item.select("span.ndPrice strong")
        for price_elem in price_elems:
            price = self.parse_price(price_elem.get_text())
            if price and (min_price is None or price < min_price):
                min_price = price
        
        return {
            "hotel_id": hotel_id,
            "hotel_name": hotel_name,
            "rating": rating,
            "review_count": review_count,
            "access_info": access_info,
            "walk_minutes": walk_minutes,
            "min_price": min_price,
        }
    
    def scrape_date_group(self, group_key: str) -> List[Dict]:
        """
        特定の日付グループをスクレイピングする
        
        Args:
            group_key: 日付グループのキー（例: "tgs_period"）
        
        Returns:
            ホテル情報の辞書リスト
        """
        group = DATE_GROUPS[group_key]
        url = build_url(group["checkin"], group["checkout"])
        
        print(f"\n【{group['name']}】をスクレイピング中...")
        print(f"  チェックイン: {group['checkin']['year']}/{group['checkin']['month']}/{group['checkin']['day']}")
        print(f"  チェックアウト: {group['checkout']['year']}/{group['checkout']['month']}/{group['checkout']['day']}")
        
        html = self.fetch_page(url)
        if not html:
            print("  HTMLの取得に失敗しました")
            return []
        
        hotels = self.parse_hotels(html)
        
        # 日付情報を追加
        checkin_str = f"{group['checkin']['year']}-{group['checkin']['month']:02d}-{group['checkin']['day']:02d}"
        checkout_str = f"{group['checkout']['year']}-{group['checkout']['month']:02d}-{group['checkout']['day']:02d}"
        
        for hotel in hotels:
            hotel["checkin_date"] = checkin_str
            hotel["checkout_date"] = checkout_str
            hotel["date_group"] = group["name"]
        
        print(f"  取得したホテル数: {len(hotels)}件")
        return hotels
    
    def scrape_all(self) -> int:
        """
        全日付グループをスクレイピングし、DBに保存する
        
        Returns:
            取得した総ホテル数
        """
        print("=" * 50)
        print("楽天トラベル ホテル価格スクレイピング開始")
        print("=" * 50)
        
        total_count = 0
        
        for i, group_key in enumerate(DATE_GROUPS.keys()):
            # サーバ負荷軽減のため待機
            if i > 0:
                print(f"\n{REQUEST_DELAY}秒待機中...")
                time.sleep(REQUEST_DELAY)
            
            hotels = self.scrape_date_group(group_key)
            
            if hotels:
                count = self.db.insert_many(hotels)
                total_count += count
                print(f"  DBに保存: {count}件")
        
        print("\n" + "=" * 50)
        print(f"スクレイピング完了！ 合計: {total_count}件")
        print(f"データベース: {DB_PATH}")
        print("=" * 50)
        
        return total_count
    
    def test_connection(self) -> bool:
        """接続テスト"""
        group = DATE_GROUPS["tgs_period"]
        url = build_url(group["checkin"], group["checkout"])
        print(f"テストURL: {url[:80]}...")
        
        html = self.fetch_page(url)
        if html:
            hotels = self.parse_hotels(html)
            print(f"接続成功！ {len(hotels)}件のホテルを検出")
            if hotels:
                print(f"サンプル: {hotels[0]['hotel_name']}")
            return True
        return False


if __name__ == "__main__":
    scraper = HotelScraper()
    
    # 全データをスクレイピング
    scraper.scrape_all()
