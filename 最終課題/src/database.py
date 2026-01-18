"""
データベース操作モジュール
SQLiteを使用してホテル価格データを管理する
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional


class HotelDatabase:
    """ホテル価格データベースを管理するクラス"""
    
    def __init__(self, db_path: str):
        """
        データベースを初期化する
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path
        # dataフォルダが存在しない場合は作成
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()
    
    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得する"""
        return sqlite3.connect(self.db_path)
    
    def _create_table(self) -> None:
        """ホテル価格テーブルを作成する"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS hotel_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id TEXT,
            hotel_name TEXT,
            rating REAL,
            review_count INTEGER,
            access_info TEXT,
            walk_minutes INTEGER,
            min_price INTEGER,
            checkin_date TEXT,
            checkout_date TEXT,
            date_group TEXT,
            scraped_at TEXT
        )
        """
        with self._get_connection() as conn:
            conn.execute(create_sql)
            conn.commit()
    
    def insert_hotel(self, data: Dict) -> None:
        """
        ホテルデータを挿入する
        
        Args:
            data: ホテル情報の辞書
        """
        insert_sql = """
        INSERT INTO hotel_prices 
        (hotel_id, hotel_name, rating, review_count, access_info, walk_minutes, 
         min_price, checkin_date, checkout_date, date_group, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            conn.execute(insert_sql, (
                data.get("hotel_id"),
                data.get("hotel_name"),
                data.get("rating"),
                data.get("review_count"),
                data.get("access_info"),
                data.get("walk_minutes"),
                data.get("min_price"),
                data.get("checkin_date"),
                data.get("checkout_date"),
                data.get("date_group"),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def insert_many(self, hotels: List[Dict]) -> int:
        """
        複数のホテルデータを一括挿入する
        
        Args:
            hotels: ホテル情報の辞書リスト
        
        Returns:
            挿入した件数
        """
        for hotel in hotels:
            self.insert_hotel(hotel)
        return len(hotels)
    
    def get_all_hotels(self) -> List[Dict]:
        """全ホテルデータを取得する"""
        query = "SELECT * FROM hotel_prices ORDER BY checkin_date, hotel_name"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_hotels_by_date_group(self, date_group: str) -> List[Dict]:
        """
        日付グループでホテルデータを取得する
        
        Args:
            date_group: 日付グループ名（例: "TGS期間"）
        
        Returns:
            ホテル情報の辞書リスト
        """
        query = "SELECT * FROM hotel_prices WHERE date_group = ? ORDER BY hotel_name"
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, (date_group,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_price_comparison(self) -> List[Dict]:
        """
        ホテルごとの価格比較データを取得する
        
        Returns:
            ホテル名、TGS価格、前週価格、翌週価格を含む辞書リスト
        """
        query = """
        SELECT 
            hotel_name,
            MAX(CASE WHEN date_group = 'TGS期間' THEN min_price END) as tgs_price,
            MAX(CASE WHEN date_group = 'TGS前週' THEN min_price END) as before_price,
            MAX(CASE WHEN date_group = 'TGS翌週' THEN min_price END) as after_price,
            MAX(walk_minutes) as walk_minutes,
            MAX(rating) as rating
        FROM hotel_prices
        GROUP BY hotel_name
        HAVING tgs_price IS NOT NULL
        ORDER BY walk_minutes
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_all(self) -> None:
        """全データを削除する"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM hotel_prices")
            conn.commit()
    
    def count(self) -> int:
        """データ件数を取得する"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM hotel_prices")
            return cursor.fetchone()[0]


if __name__ == "__main__":
    # テスト用
    from config import DB_PATH
    db = HotelDatabase(DB_PATH)
    print(f"データベースパス: {DB_PATH}")
    print(f"現在のデータ件数: {db.count()}")
