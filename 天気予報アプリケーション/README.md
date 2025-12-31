# 天気予報アプリケーション / 天气预报应用程序

日本気象庁のAPIを使用して、地域別の天気予報を表示するアプリケーションです。

使用日本气象厅API，显示各地区天气预报的应用程序。

## 機能 / 功能

- 地域リストの表示 / 显示地区列表
- 選択した地域の天気予報を表示 / 显示选择地区的天气预报

## 使用方法 / 使用方法

```bash
cd 天気予報アプリケーション
flet run src
```

## API エンドポイント / API端点

- 地域リスト / 地区列表: `http://www.jma.go.jp/bosai/common/const/area.json`
- 天気予報 / 天气预报: `https://www.jma.go.jp/bosai/forecast/data/forecast/{地域コード}.json`
