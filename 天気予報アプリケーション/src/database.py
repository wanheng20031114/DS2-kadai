"""
天気予報データベースモジュール / 天气预报数据库模块
===================================================
SQLiteデータベースを使用して天気予報データを管理する
使用SQLite数据库管理天气预报数据

テーブル構成 / 表结构:
- offices: 地域情報 / 地区信息
- forecasts: 予報メタデータ / 预报元数据
- weather_details: 天気詳細 / 天气详情
- temperatures: 気温データ / 气温数据
- pops: 降水確率 / 降水概率
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional


class WeatherDatabase:
    """
    天気予報データベースの管理クラス
    天气预报数据库管理类
    """
    
    def __init__(self, db_path: str = None):
        """
        データベース接続を初期化する
        初始化数据库连接
        
        Args:
            db_path: データベースファイルのパス（デフォルトはsrcフォルダ内のweather.db）
                    数据库文件路径（默认为src文件夹内的weather.db）
        """
        if db_path is None:
            # スクリプトと同じディレクトリにDBを作成
            # 在脚本所在目录创建数据库
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, "weather.db")
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # 行を辞書形式でアクセス可能に / 使行可以按字典方式访问
        self.init_tables()
    
    def init_tables(self):
        """
        データベーステーブルを初期化する
        初始化数据库表
        """
        cursor = self.conn.cursor()
        
        # 地域テーブル / 地区表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offices (
                office_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                en_name TEXT,
                parent_code TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 予報メタデータテーブル / 预报元数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                office_code TEXT NOT NULL,
                publishing_office TEXT,
                report_datetime DATETIME NOT NULL,
                forecast_type TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (office_code) REFERENCES offices(office_code),
                UNIQUE(office_code, report_datetime, forecast_type)
            )
        """)
        
        # 天気詳細テーブル / 天气详情表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_id INTEGER NOT NULL,
                area_code TEXT,
                area_name TEXT NOT NULL,
                time_define DATETIME NOT NULL,
                weather_code TEXT,
                weather_text TEXT,
                wind TEXT,
                wave TEXT,
                FOREIGN KEY (forecast_id) REFERENCES forecasts(id)
            )
        """)
        
        # 気温テーブル / 气温表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temperatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_id INTEGER NOT NULL,
                area_code TEXT,
                area_name TEXT NOT NULL,
                time_define DATETIME NOT NULL,
                temp_min TEXT,
                temp_max TEXT,
                FOREIGN KEY (forecast_id) REFERENCES forecasts(id)
            )
        """)
        
        # 降水確率テーブル / 降水概率表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_id INTEGER NOT NULL,
                area_code TEXT,
                area_name TEXT NOT NULL,
                time_define DATETIME NOT NULL,
                pop_value TEXT,
                FOREIGN KEY (forecast_id) REFERENCES forecasts(id)
            )
        """)
        
        self.conn.commit()
    
    def save_offices(self, offices_data: dict):
        """
        地域情報をデータベースに保存する
        将地区信息保存到数据库
        
        Args:
            offices_data: APIから取得したofficesデータ / 从API获取的offices数据
        """
        cursor = self.conn.cursor()
        
        for code, info in offices_data.items():
            cursor.execute("""
                INSERT OR REPLACE INTO offices (office_code, name, en_name, parent_code, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                code,
                info.get("name", ""),
                info.get("enName", ""),
                info.get("parent", ""),
                datetime.now().isoformat()
            ))
        
        self.conn.commit()
    
    def get_offices(self) -> dict:
        """
        データベースから地域情報を取得する
        从数据库获取地区信息
        
        Returns:
            地域情報の辞書 / 地区信息字典
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM offices")
        rows = cursor.fetchall()
        
        offices = {}
        for row in rows:
            offices[row["office_code"]] = {
                "name": row["name"],
                "enName": row["en_name"],
                "parent": row["parent_code"]
            }
        return offices
    
    def save_forecast(self, office_code: str, forecast_data: list) -> bool:
        """
        天気予報データをデータベースに保存する
        将天气预报数据保存到数据库
        
        Args:
            office_code: 地域コード / 地区代码
            forecast_data: APIから取得した予報データ / 从API获取的预报数据
            
        Returns:
            成功したかどうか / 是否成功
        """
        if not forecast_data or len(forecast_data) == 0:
            return False
        
        cursor = self.conn.cursor()
        
        try:
            # 短期予報データ（data[0]）を保存 / 保存短期预报数据
            if len(forecast_data) > 0:
                short_forecast = forecast_data[0]
                publishing_office = short_forecast.get("publishingOffice", "")
                report_datetime = short_forecast.get("reportDatetime", "")
                
                # 予報メタデータを挿入 / 插入预报元数据
                cursor.execute("""
                    INSERT OR REPLACE INTO forecasts (office_code, publishing_office, report_datetime, forecast_type)
                    VALUES (?, ?, ?, ?)
                """, (office_code, publishing_office, report_datetime, "short"))
                
                forecast_id = cursor.lastrowid
                
                # 存在しない場合は、既存のIDを取得 / 如果不存在则获取现有ID
                if forecast_id == 0:
                    cursor.execute("""
                        SELECT id FROM forecasts 
                        WHERE office_code = ? AND report_datetime = ? AND forecast_type = ?
                    """, (office_code, report_datetime, "short"))
                    row = cursor.fetchone()
                    if row:
                        forecast_id = row["id"]
                        # 既存データを削除して再挿入 / 删除现有数据并重新插入
                        cursor.execute("DELETE FROM weather_details WHERE forecast_id = ?", (forecast_id,))
                        cursor.execute("DELETE FROM temperatures WHERE forecast_id = ?", (forecast_id,))
                        cursor.execute("DELETE FROM pops WHERE forecast_id = ?", (forecast_id,))
                
                # timeSeries[0] - 天気詳細 / 天气详情
                if "timeSeries" in short_forecast and len(short_forecast["timeSeries"]) > 0:
                    ts_weather = short_forecast["timeSeries"][0]
                    time_defines = ts_weather.get("timeDefines", [])
                    
                    for area in ts_weather.get("areas", []):
                        area_code = area.get("area", {}).get("code", "")
                        area_name = area.get("area", {}).get("name", "")
                        weathers = area.get("weathers", [])
                        weather_codes = area.get("weatherCodes", [])
                        winds = area.get("winds", [])
                        waves = area.get("waves", [])
                        
                        for i, time_def in enumerate(time_defines):
                            cursor.execute("""
                                INSERT INTO weather_details 
                                (forecast_id, area_code, area_name, time_define, weather_code, weather_text, wind, wave)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                forecast_id,
                                area_code,
                                area_name,
                                time_def,
                                weather_codes[i] if i < len(weather_codes) else "",
                                weathers[i] if i < len(weathers) else "",
                                winds[i] if i < len(winds) else "",
                                waves[i] if i < len(waves) else ""
                            ))
                
                # timeSeries[1] - 降水確率 / 降水概率
                if "timeSeries" in short_forecast and len(short_forecast["timeSeries"]) > 1:
                    ts_pop = short_forecast["timeSeries"][1]
                    time_defines = ts_pop.get("timeDefines", [])
                    
                    for area in ts_pop.get("areas", []):
                        area_code = area.get("area", {}).get("code", "")
                        area_name = area.get("area", {}).get("name", "")
                        pops = area.get("pops", [])
                        
                        for i, time_def in enumerate(time_defines):
                            if i < len(pops):
                                cursor.execute("""
                                    INSERT INTO pops (forecast_id, area_code, area_name, time_define, pop_value)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (forecast_id, area_code, area_name, time_def, pops[i]))
                
                # timeSeries[2] - 気温 / 气温
                if "timeSeries" in short_forecast and len(short_forecast["timeSeries"]) > 2:
                    ts_temp = short_forecast["timeSeries"][2]
                    time_defines = ts_temp.get("timeDefines", [])
                    
                    for area in ts_temp.get("areas", []):
                        area_code = area.get("area", {}).get("code", "")
                        area_name = area.get("area", {}).get("name", "")
                        temps = area.get("temps", [])
                        
                        for i, time_def in enumerate(time_defines):
                            if i < len(temps):
                                cursor.execute("""
                                    INSERT INTO temperatures 
                                    (forecast_id, area_code, area_name, time_define, temp_max, temp_min)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (forecast_id, area_code, area_name, time_def, temps[i], ""))
            
            # 週間予報データ（data[1]）を保存 / 保存周间预报数据
            if len(forecast_data) > 1:
                week_forecast = forecast_data[1]
                publishing_office = week_forecast.get("publishingOffice", "")
                report_datetime = week_forecast.get("reportDatetime", "")
                
                cursor.execute("""
                    INSERT OR REPLACE INTO forecasts (office_code, publishing_office, report_datetime, forecast_type)
                    VALUES (?, ?, ?, ?)
                """, (office_code, publishing_office, report_datetime, "week"))
                
                forecast_id = cursor.lastrowid
                
                if forecast_id == 0:
                    cursor.execute("""
                        SELECT id FROM forecasts 
                        WHERE office_code = ? AND report_datetime = ? AND forecast_type = ?
                    """, (office_code, report_datetime, "week"))
                    row = cursor.fetchone()
                    if row:
                        forecast_id = row["id"]
                        cursor.execute("DELETE FROM weather_details WHERE forecast_id = ?", (forecast_id,))
                        cursor.execute("DELETE FROM temperatures WHERE forecast_id = ?", (forecast_id,))
                
                # 週間天気コード / 周间天气代码
                if "timeSeries" in week_forecast and len(week_forecast["timeSeries"]) > 0:
                    ts_weather = week_forecast["timeSeries"][0]
                    time_defines = ts_weather.get("timeDefines", [])
                    
                    for area in ts_weather.get("areas", []):
                        area_code = area.get("area", {}).get("code", "")
                        area_name = area.get("area", {}).get("name", "")
                        weather_codes = area.get("weatherCodes", [])
                        
                        for i, time_def in enumerate(time_defines):
                            if i < len(weather_codes):
                                cursor.execute("""
                                    INSERT INTO weather_details 
                                    (forecast_id, area_code, area_name, time_define, weather_code, weather_text, wind, wave)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (forecast_id, area_code, area_name, time_def, weather_codes[i], "", "", ""))
                
                # 週間気温 / 周间气温
                if "timeSeries" in week_forecast and len(week_forecast["timeSeries"]) > 1:
                    ts_temp = week_forecast["timeSeries"][1]
                    time_defines = ts_temp.get("timeDefines", [])
                    
                    for area in ts_temp.get("areas", []):
                        area_code = area.get("area", {}).get("code", "")
                        area_name = area.get("area", {}).get("name", "")
                        temps_min = area.get("tempsMin", [])
                        temps_max = area.get("tempsMax", [])
                        
                        for i, time_def in enumerate(time_defines):
                            t_min = temps_min[i] if i < len(temps_min) else ""
                            t_max = temps_max[i] if i < len(temps_max) else ""
                            cursor.execute("""
                                INSERT INTO temperatures 
                                (forecast_id, area_code, area_name, time_define, temp_min, temp_max)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (forecast_id, area_code, area_name, time_def, t_min, t_max))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"データベース保存エラー / 数据库保存错误: {e}")
            self.conn.rollback()
            return False
    
    def get_forecast(self, office_code: str, forecast_type: str = "short", 
                     report_date: str = None) -> Optional[dict]:
        """
        データベースから天気予報データを取得する
        从数据库获取天气预报数据
        
        Args:
            office_code: 地域コード / 地区代码
            forecast_type: 予報タイプ（short/week）/ 预报类型
            report_date: 発表日（YYYY-MM-DD形式、Noneの場合は最新）/ 发表日期
            
        Returns:
            予報データの辞書、またはNone / 预报数据字典或None
        """
        cursor = self.conn.cursor()
        
        # 予報メタデータを取得 / 获取预报元数据
        if report_date:
            cursor.execute("""
                SELECT * FROM forecasts 
                WHERE office_code = ? AND forecast_type = ? AND DATE(report_datetime) = ?
                ORDER BY report_datetime DESC LIMIT 1
            """, (office_code, forecast_type, report_date))
        else:
            cursor.execute("""
                SELECT * FROM forecasts 
                WHERE office_code = ? AND forecast_type = ?
                ORDER BY report_datetime DESC LIMIT 1
            """, (office_code, forecast_type))
        
        forecast_row = cursor.fetchone()
        if not forecast_row:
            return None
        
        forecast_id = forecast_row["id"]
        
        # 天気詳細を取得 / 获取天气详情
        cursor.execute("""
            SELECT * FROM weather_details WHERE forecast_id = ? ORDER BY time_define
        """, (forecast_id,))
        weather_rows = cursor.fetchall()
        
        # 気温を取得 / 获取气温
        cursor.execute("""
            SELECT * FROM temperatures WHERE forecast_id = ? ORDER BY time_define
        """, (forecast_id,))
        temp_rows = cursor.fetchall()
        
        # 降水確率を取得 / 获取降水概率
        cursor.execute("""
            SELECT * FROM pops WHERE forecast_id = ? ORDER BY time_define
        """, (forecast_id,))
        pop_rows = cursor.fetchall()
        
        return {
            "forecast": dict(forecast_row),
            "weather_details": [dict(row) for row in weather_rows],
            "temperatures": [dict(row) for row in temp_rows],
            "pops": [dict(row) for row in pop_rows]
        }
    
    def get_available_dates(self, office_code: str) -> list:
        """
        保存済みの予報日付リストを取得する
        获取已保存的预报日期列表
        
        Args:
            office_code: 地域コード / 地区代码
            
        Returns:
            日付のリスト（YYYY-MM-DD形式）/ 日期列表
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT DATE(report_datetime) as report_date 
            FROM forecasts 
            WHERE office_code = ?
            ORDER BY report_date DESC
        """, (office_code,))
        
        return [row["report_date"] for row in cursor.fetchall()]
    
    def close(self):
        """
        データベース接続を閉じる
        关闭数据库连接
        """
        if self.conn:
            self.conn.close()
