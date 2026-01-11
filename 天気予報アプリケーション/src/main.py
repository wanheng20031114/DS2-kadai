"""
天気予報アプリケーション / 天气预报应用程序
===============================================
日本気象庁のAPIを使用して、地域別の天気予報を表示するアプリケーション
使用日本气象厅API，显示各地区天气预报的应用程序

エンドポイント / 端点:
- 地域リスト / 地区列表: http://www.jma.go.jp/bosai/common/const/area.json
- 天気予報 / 天气预报: https://www.jma.go.jp/bosai/forecast/data/forecast/{地域コード}.json
"""

import flet as ft
import urllib.request
import json
from database import WeatherDatabase


def fetch_json(url: str) -> dict | None:
    """
    指定されたURLからJSONデータを取得する
    从指定URL获取JSON数据
    
    Args:
        url: 取得先のURL / 请求的URL
        
    Returns:
        JSONデータまたはNone（エラー時）
        JSON数据或None（发生错误时）
    """
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"エラー: {e}")
        return None


class WeatherApp(ft.Column):
    """
    天気予報アプリケーションのメインクラス
    天气预报应用程序的主类
    """
    
    # APIエンドポイント / API端点
    AREA_API_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
    FORECAST_API_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"
    
    def __init__(self):
        """
        コンストラクタ：UIコンポーネントを初期化する
        构造函数：初始化UI组件
        """
        super().__init__()
        
        # データベースを初期化 / 初始化数据库
        self.db = WeatherDatabase()
        
        # 地域データを格納する辞書 / 存储地区数据的字典
        self.offices = {}
        
        # 配色パレット / 配色板 (Modern Slate Theme)
        self.colors = {
            "primary": "#38bdf8",      # Sky 400
            "background": "#0f172a",   # Slate 900
            "surface": "#1e293b",      # Slate 800
            "surface_variant": "#334155", # Slate 700
            "text_primary": "#f8fafc", # Slate 50
            "text_secondary": "#94a3b8", # Slate 400
            "accent_gradient": ["#1e293b", "#0f172a"], # Card gradient
        }
        
        # UIコンポーネント / UI组件
        # タイトル / 标题
        self.title_text = ft.Text(
            "天気予報",
            size=32,
            weight=ft.FontWeight.W_900,  # Extra Bold
            color=self.colors["text_primary"],
            font_family="Roboto, Noto Sans JP, sans-serif",
        )
        
        # 地域選択ドロップダウン / 地区选择下拉框
        self.area_dropdown = ft.Dropdown(
            label="地域を選択",
            label_style=ft.TextStyle(color=self.colors["text_secondary"]),
            hint_text="都道府県を選んでください",
            text_style=ft.TextStyle(color=self.colors["text_primary"], size=16),
            width=350,
            on_change=self.on_area_selected,
            bgcolor=self.colors["surface"], # Solid color for readability
            border_color=self.colors["surface_variant"],
            border_width=1,
            focused_border_color=self.colors["primary"],
        )
        
        # 天気情報表示コンテナ / 天气信息显示容器
        self.weather_container = ft.Column(
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # ローディングインジケータ / 加载指示器
        self.loading = ft.ProgressRing(
            visible=False, 
            color=self.colors["primary"]
        )
        
        # エラーメッセージ / 错误信息
        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            visible=False,
            size=14,
        )
        
        # メインコンテナを構築 / 构建主容器
        main_container = ft.Container(
            width=500, # Slightly wider
            padding=40,
            border_radius=24,
            # Glassmorphism effect / 玻璃拟态效果 (Subtle)
            bgcolor=ft.Colors.with_opacity(0.8, self.colors["background"]),
            border=ft.border.all(1, self.colors["surface_variant"]),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.BLACK45,
                offset=ft.Offset(0, 10),
            ),
            content=ft.Column(
                controls=[
                    # タイトル部 / 标题部分
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CLOUD, color=self.colors["primary"], size=36),
                                self.title_text
                            ], 
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=12,
                        ),
                        margin=ft.margin.only(bottom=10)
                    ),
                    ft.Divider(color=self.colors["surface_variant"], height=30),
                    
                    # 地域選択部 / 地区选择部分
                    self.area_dropdown,
                    
                    # ローディング / 加载中
                    ft.Container(
                        content=self.loading,
                        alignment=ft.alignment.center,
                        height=20 if not self.loading.visible else None, # Prevent layout jump
                    ),
                    
                    # エラー表示 / 错误显示
                    self.error_text,
                    
                    # 天気情報表示部 / 天气信息显示部分
                    ft.Container(
                        content=self.weather_container,
                        height=400,
                        padding=ft.padding.only(top=10),
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        
        self.controls = [main_container]
    
    def did_mount(self):
        """
        コンポーネントがマウントされた時に呼ばれる
        组件挂载时调用
        """
        self.load_areas()
    
    def load_areas(self):
        """
        地域リストをAPIから読み込む
        从API加载地区列表
        """
        self.loading.visible = True
        self.update()
        
        data = fetch_json(self.AREA_API_URL)
        
        if data is None:
            self.show_error("地域データの取得に失敗しました")
            self.loading.visible = False
            self.update()
            return
        
        # offices（都道府県レベル）を取得 / 获取offices（都道府县级别）
        self.offices = data.get("offices", {})
        
        # 地域情報をデータベースに保存 / 将地区信息保存到数据库
        self.db.save_offices(self.offices)
        
        # ドロップダウンにオプションを追加 / 向下拉框添加选项
        options = []
        for code, info in self.offices.items():
            name = info.get("name", "不明")
            options.append(ft.dropdown.Option(key=code, text=name))
        
        # 名前順でソート / 按名称排序
        options.sort(key=lambda x: x.text)
        self.area_dropdown.options = options
        
        self.loading.visible = False
        self.error_text.visible = False
        self.update()
    
    def on_area_selected(self, e):
        """
        地域が選択された時のイベントハンドラ
        地区被选择时的事件处理程序
        
        Args:
            e: イベントオブジェクト / 事件对象
        """
        area_code = e.control.value
        if not area_code:
            return
        
        self.load_weather(area_code)
    
    def load_weather(self, area_code: str):
        """
        天気予報データを読み込む
        加载天气预报数据
        
        Args:
            area_code: 地域コード / 地区代码
        """
        self.loading.visible = True
        self.weather_container.controls.clear()
        self.error_text.visible = False
        self.update()
        
        url = self.FORECAST_API_URL.format(area_code)
        data = fetch_json(url)
        
        if data is None:
            self.show_error("天気データの取得に失敗しました")
            self.loading.visible = False
            self.update()
            return
        
        # 天気情報をデータベースに保存 / 将天气信息保存到数据库
        self.db.save_forecast(area_code, data)
        
        # 天気情報を表示 / 显示天气信息
        self.display_weather(data)
        
        self.loading.visible = False
        self.update()
    
    def display_weather(self, data: list):
        """
        天気予報データを表示する
        显示天气预报数据
        
        
        Args:
            data: 天気予報データ
        """
        self.weather_container.controls.clear()
        
        if not data or len(data) == 0:
            self.show_error("予報データがありません")
            return
        
        try:
            # 地域名と発表日時（短期予報から）
            forecast_short = data[0]
            publishing_office = forecast_short.get("publishingOffice", "")
            report_datetime = forecast_short.get("reportDatetime", "")[:16].replace("T", " ")
            
            # ヘッダー情報
            self.weather_container.controls.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=self.colors["text_secondary"], size=16),
                        ft.Text(f"{publishing_office} • {report_datetime}", color=self.colors["text_secondary"], size=12),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                )
            )

            # タブレイアウトの作成
            tabs = ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(
                        text="詳細",
                        icon=ft.Icons.TODAY,
                        content=self.create_current_tab(data),
                    ),
                    ft.Tab(
                        text="週間",
                        icon=ft.Icons.CALENDAR_MONTH,
                        content=self.create_weekly_tab(data),
                    ),
                ],
                expand=True,
                divider_color=self.colors["surface_variant"],
                indicator_color=self.colors["primary"],
                label_color=self.colors["primary"],
                unselected_label_color=self.colors["text_secondary"],
            )
            
            self.weather_container.controls.append(
                ft.Container(
                    content=tabs,
                    height=350,  # タブコンテンツの高さ
                )
            )
            
        except Exception as e:
            print(f"表示エラー / 显示错误: {e}")
            self.show_error(f"データの解析に失敗しました / 解析数据失败: {e}")

    def create_current_tab(self, data: list) -> ft.Control:
        """
        詳細天気タブの内容を作成
        创建详细天气标签页内容
        """
        content_col = ft.Column(spacing=20, scroll=ft.ScrollMode.AUTO)
        
        try:
            # 1. 天気概況 (data[0]["timeSeries"][0])
            ts_weather = data[0]["timeSeries"][0]
            area_weather = ts_weather["areas"][0]
            area_name = area_weather["area"]["name"]
            current_weather = area_weather["weathers"][0]
            
            # 地域名表示
            content_col.controls.append(
                ft.Container(
                    margin=ft.margin.only(top=10),
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.LOCATION_ON, color=self.colors["primary"], size=20),
                            ft.Text(
                                area_name,
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=self.colors["text_primary"],
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                )
            )
            
            # 現在の天気カード
            icon = self.get_weather_icon(current_weather)
            weather_short = current_weather.split("　")[0]
            
            # 気温データを取得 (data[0]["timeSeries"][2])
            temp_display = ""
            if len(data[0]["timeSeries"]) > 2:
                ts_temps = data[0]["timeSeries"][2]
                if ts_temps.get("areas"):
                    temps = ts_temps["areas"][0].get("temps", [])
                    if len(temps) >= 2:
                        # temps[0] = 今日の最高気温、temps[1] = 今日の最低気温（または逆の場合もある）
                        temp_display = f"{temps[0]}°C"
                    elif len(temps) == 1:
                        temp_display = f"{temps[0]}°C"
            
            weather_card = ft.Container(
                padding=20,
                border_radius=16,
                bgcolor=self.colors["surface"],
                border=ft.border.all(1, self.colors["surface_variant"]),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(icon, size=48),
                            padding=15,
                            bgcolor=self.colors["background"],
                            border_radius=12,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    "今日の天気",
                                    color=self.colors["text_secondary"],
                                    size=12,
                                ),
                                ft.Row(
                                    [
                                        ft.Text(
                                            weather_short,
                                            weight=ft.FontWeight.BOLD,
                                            color=self.colors["text_primary"],
                                            size=18,
                                        ),
                                        ft.Text(
                                            temp_display,
                                            weight=ft.FontWeight.BOLD,
                                            color="#ef4444",  # Red for temperature
                                            size=18,
                                        ) if temp_display else ft.Container(),
                                    ],
                                    spacing=10,
                                ),
                                ft.Text(
                                    current_weather,
                                    color=self.colors["text_secondary"],
                                    size=12,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=2,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=4,
                            expand=True,
                        ),
                    ],
                    spacing=15,
                ),
            )
            content_col.controls.append(weather_card)
            
            # 2. 降水確率 (data[0]["timeSeries"][1])
            if len(data[0]["timeSeries"]) > 1:
                ts_pop = data[0]["timeSeries"][1]
                pops = ts_pop["areas"][0]["pops"]
                times = ts_pop["timeDefines"]
                
                pop_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10)
                
                for i, time_str in enumerate(times):
                    if i < len(pops):
                        time_display = time_str[11:16] # 12:00
                        pop_val = pops[i]
                        
                        pop_item = ft.Container(
                            width=70,
                            padding=10,
                            border_radius=10,
                            bgcolor=self.colors["surface"],
                            border=ft.border.all(1, self.colors["surface_variant"]),
                            content=ft.Column(
                                [
                                    ft.Text(time_display, size=12, color=self.colors["text_secondary"]),
                                    ft.Icon(ft.Icons.WATER_DROP, size=16, color=self.colors["primary"]),
                                    ft.Text(f"{pop_val}%", size=14, weight=ft.FontWeight.BOLD, color=self.colors["text_primary"]),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2
                            )
                        )
                        pop_row.controls.append(pop_item)
                
                content_col.controls.append(
                    ft.Column([
                        ft.Text("降水確率 (6h)", size=14, color=self.colors["text_secondary"]),
                        pop_row
                    ], spacing=5)
                )

        except Exception as e:
            print(f"詳細タブ生成エラー: {e}")
            content_col.controls.append(ft.Text(f"データエラー: {e}", color=ft.Colors.RED))
            
        return ft.Container(content=content_col, padding=ft.padding.all(10))

    def create_weekly_tab(self, data: list) -> ft.Control:
        """
        週間天気タブの内容を作成
        创建周天气标签页内容
        """
        content_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        try:
            # 週間予報データがあるか確認 (通常は data[1])
            if len(data) < 2:
                return ft.Text("週間予報データがありません", color=self.colors["text_secondary"])

            weekly_data = data[1]
            if not weekly_data.get("timeSeries"):
                return ft.Text("週間予報データがありません", color=self.colors["text_secondary"])

            # 天気コード (timeSeries[0])
            ts_weather = weekly_data["timeSeries"][0]
            weather_codes = ts_weather["areas"][0].get("weatherCodes", [])
            dates = ts_weather["timeDefines"]

            # 気温 (timeSeries[1]) - 範囲情報などが含まれる
            ts_temps = weekly_data["timeSeries"][1] if len(weekly_data["timeSeries"]) > 1 else None
            temps_min = []
            temps_max = []
            
            if ts_temps:
                # tempsMin/Max はリストの場合と、空文字が含まれる場合がある
                temps_min = ts_temps["areas"][0].get("tempsMin", [])
                temps_max = ts_temps["areas"][0].get("tempsMax", [])

            # 今日の気温を短期予報から取得（週間予報の最初の日は空の場合がある）
            today_temp_high = None
            today_temp_low = None
            if len(data[0]["timeSeries"]) > 2:
                ts_today = data[0]["timeSeries"][2]
                if ts_today.get("areas"):
                    today_temps = ts_today["areas"][0].get("temps", [])
                    if len(today_temps) >= 1:
                        today_temp_high = today_temps[0]  # 今日の最高気温
                    if len(today_temps) >= 3:
                        today_temp_low = today_temps[2]   # 明日の最低気温（今日の最低はないため）

            for i, date_str in enumerate(dates):
                if i < len(weather_codes):
                    # 日付フォーマット (YYYY-MM-DD -> MM/DD)
                    date_display = f"{date_str[5:7]}/{date_str[8:10]}"
                    
                    # 天気コードからアイコン
                    code = weather_codes[i]
                    icon = self.get_weather_icon_by_code(code)
                    
                    # 気温
                    temp_text = ""
                    t_min = temps_min[i] if i < len(temps_min) else "-"
                    t_max = temps_max[i] if i < len(temps_max) else "-"
                    
                    # 見やすく整形
                    if t_min == "" or t_min is None: t_min = "-"
                    if t_max == "" or t_max is None: t_max = "-"
                    
                    # 今日の気温が空の場合、短期予報から取得
                    if i == 0:
                        if t_max == "-" and today_temp_high:
                            t_max = today_temp_high
                        if t_min == "-" and today_temp_low:
                            t_min = today_temp_low
                    
                    item = ft.Container(
                        padding=ft.padding.symmetric(vertical=8, horizontal=15),
                        border_radius=10,
                        bgcolor=self.colors["surface"],
                        content=ft.Row(
                            [
                                ft.Text(date_display, width=50, color=self.colors["text_secondary"]),
                                ft.Text(icon, size=24, width=40, text_align=ft.TextAlign.CENTER),
                                ft.Row(
                                    [
                                        ft.Text(f"{t_max}°", color="#ef4444", weight=ft.FontWeight.BOLD), # Red
                                        ft.Text("/", color=self.colors["text_secondary"]),
                                        ft.Text(f"{t_min}°", color="#38bdf8", weight=ft.FontWeight.BOLD), # Blue
                                    ],
                                    spacing=5,
                                    width=100,
                                    alignment=ft.MainAxisAlignment.END
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    )
                    content_col.controls.append(item)

        except Exception as e:
            print(f"週間タブ生成エラー: {e}")
            content_col.controls.append(ft.Text(f"データエラー: {e}", color=ft.Colors.RED))

        return ft.Container(content=content_col, padding=ft.padding.all(10))
    
    def get_weather_icon_by_code(self, code: str) -> str:
        """
        天気コードからアイコンを返す
        根据天气代码返回图标
        
        100系: 晴れ
        200系: 曇り
        300系: 雨
        400系: 雪
        """
        c = int(code)
        if 100 <= c < 200:
            return "☀️"
        elif 200 <= c < 300:
            return "☁️"
        elif 300 <= c < 400:
            return "🌧️"
        elif 400 <= c < 500:
            return "❄️"
        else:
            return "🌤️"
    
    def get_weather_icon(self, weather: str) -> str:
        """
        天気説明に基づいてアイコンを返す
        根据天气描述返回图标
        
        Args:
            weather: 天気説明 / 天气描述
            
        Returns:
            天気アイコン / 天气图标
        """
        if "晴" in weather:
            if "曇" in weather or "くもり" in weather:
                return "⛅"
            elif "雨" in weather:
                return "🌦️"
            return "☀️"
        elif "曇" in weather or "くもり" in weather:
            if "雨" in weather:
                return "🌧️"
            return "☁️"
        elif "雨" in weather:
            return "🌧️"
        elif "雪" in weather:
            return "❄️"
        elif "雷" in weather:
            return "⛈️"
        return "🌤️"
    
    def show_error(self, message: str):
        """
        エラーメッセージを表示する
        显示错误信息
        
        Args:
            message: エラーメッセージ / 错误信息
        """
        self.error_text.value = message
        self.error_text.visible = True


def main(page: ft.Page):
    """
    アプリケーションのエントリーポイント
    应用程序入口点
    
    Args:
        page: Fletページオブジェクト / Flet页面对象
    """
    # ページ設定 / 页面设置
    page.title = "天気予報"
    page.bgcolor = "#0f172a" # Slate 900
    page.theme_mode = ft.ThemeMode.DARK # 強制ダークモード / 强制深色模式
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 20
    
    # フォント設定（オプション）
    page.fonts = {
        "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap"
    }
    
    # アプリケーションを追加 / 添加应用程序
    app = WeatherApp()
    page.add(app)


# アプリケーション起動 / 启动应用程序
ft.app(main)
