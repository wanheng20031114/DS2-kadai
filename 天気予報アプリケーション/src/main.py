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
        print(f"エラー / 错误: {e}")
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
            self.show_error("地域データの取得に失敗しました / 获取地区数据失败")
            self.loading.visible = False
            self.update()
            return
        
        # offices（都道府県レベル）を取得 / 获取offices（都道府县级别）
        self.offices = data.get("offices", {})
        
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
            self.show_error("天気データの取得に失敗しました / 获取天气数据失败")
            self.loading.visible = False
            self.update()
            return
        
        # 天気情報を表示 / 显示天气信息
        self.display_weather(data)
        
        self.loading.visible = False
        self.update()
    
    def display_weather(self, data: list):
        """
        天気予報データを表示する
        显示天气预报数据
        
        Args:
            data: 天気予報データ / 天气预报数据
        """
        self.weather_container.controls.clear()
        
        if not data or len(data) == 0:
            self.show_error("天気データがありません / 没有天气数据")
            return
        
        try:
            # 最初の予報データを取得 / 获取第一个预报数据
            forecast = data[0]
            time_series = forecast.get("timeSeries", [])
            
            if not time_series:
                self.show_error("予報データがありません / 没有预报数据")
                return
            
            # 地域名を表示 / 显示地区名称
            publishing_office = forecast.get("publishingOffice", "")
            report_datetime = forecast.get("reportDatetime", "")[:10]
            
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
            
            # 天気予報（最初のtimeSeriesから）/ 天气预报（从第一个timeSeries）
            weather_ts = time_series[0] if len(time_series) > 0 else None
            
            if weather_ts:
                times = weather_ts.get("timeDefines", [])
                areas = weather_ts.get("areas", [])
                
                if areas:
                    area = areas[0]  # 最初の地域 / 第一个地区
                    area_name = area.get("area", {}).get("name", "")
                    weathers = area.get("weathers", [])
                    
                    self.weather_container.controls.append(
                        ft.Container(
                            margin=ft.margin.symmetric(vertical=15),
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
                    
                    # 各日の天気を表示 / 显示每天的天气
                    for i, time_def in enumerate(times):
                        if i < len(weathers):
                            date_str = time_def[:10]
                            weather_full = weathers[i]
                            # 簡略化：全角空白で区切って主要な天気だけ表示してもよいが、ここではそのまま
                            weather_short = weather_full.split("　")[0] # 全角スペースで分割
                            
                            # 天気アイコン選択 / 选择天气图标
                            icon = self.get_weather_icon(weather_full)
                            
                            card = ft.Container(
                                padding=20,
                                border_radius=16,
                                bgcolor=self.colors["surface"],
                                border=ft.border.all(1, self.colors["surface_variant"]),
                                content=ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.Text(icon, size=40),
                                            padding=10,
                                            bgcolor=self.colors["background"],
                                            border_radius=12,
                                        ),
                                        ft.Column(
                                            [
                                                ft.Text(
                                                    date_str,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=self.colors["text_primary"],
                                                    size=16,
                                                ),
                                                ft.Text(
                                                    weather_short,
                                                    color=self.colors["text_secondary"],
                                                    size=14,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                ),
                                            ],
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=4,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=15,
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=10,
                                    color=ft.Colors.BLACK26,
                                    offset=ft.Offset(0, 4),
                                ),
                            )
                            self.weather_container.controls.append(card)
            
        except Exception as e:
            print(f"表示エラー / 显示错误: {e}")
            self.show_error(f"データの解析に失敗しました / 解析数据失败: {e}")
    
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
    page.title = "天気予報 / 天气预报"
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
