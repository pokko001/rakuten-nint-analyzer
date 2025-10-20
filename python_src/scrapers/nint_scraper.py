"""Nintスクレイパー

Nintにログインし、市場分析データを取得:
- 推定月販数
- 売上推移
- 価格推移
- 上位店舗シェア
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright, Page, Browser
from pydantic import BaseModel, Field


class NintMarketData(BaseModel):
    """Nint市場データモデル"""

    keyword: str
    estimated_monthly_sales: int = Field(description="推定月販数")
    revenue_trend: List[Dict[str, Any]] = Field(
        default_factory=list, description="売上推移 [{date, revenue}, ...]"
    )
    price_trend: List[Dict[str, Any]] = Field(
        default_factory=list, description="価格推移 [{date, avg_price}, ...]"
    )
    top_sellers: List[Dict[str, Any]] = Field(
        default_factory=list, description="上位店舗 [{shop_name, monthly_sales, market_share}, ...]"
    )
    avg_price: Optional[float] = Field(default=None, description="平均価格")
    price_volatility: Optional[float] = Field(default=None, description="価格変動係数(CV)")
    growth_rate: Optional[float] = Field(default=None, description="成長率(%)")


class NintScraper:
    """Nintスクレイパー(Playwright使用)"""

    LOGIN_URL = "https://nint.jp/login"  # 実際のURLに要変更
    SEARCH_URL = "https://nint.jp/search"  # 実際のURLに要変更

    def __init__(self, email: str, password: str, headless: bool = True):
        """
        Args:
            email: Nintログインメールアドレス
            password: Nintログインパスワード
            headless: ヘッドレスモード(True=非表示)
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """コンテキストマネージャー: Playwright起動"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self._login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: Playwright終了"""
        if self.browser:
            self.browser.close()
        if hasattr(self, "playwright"):
            self.playwright.stop()

    def _login(self) -> None:
        """Nintにログイン"""
        if not self.page:
            raise RuntimeError("Playwright page not initialized")

        try:
            # ログインページに移動
            self.page.goto(self.LOGIN_URL, timeout=30000)

            # メールアドレス・パスワード入力
            # ※実際のセレクタはNintのHTMLに合わせて調整が必要
            self.page.fill('input[type="email"]', self.email)
            self.page.fill('input[type="password"]', self.password)

            # ログインボタンクリック
            self.page.click('button[type="submit"]')

            # ログイン完了を待機(ダッシュボードページなどの要素を待つ)
            self.page.wait_for_selector("div#dashboard", timeout=30000)

            print("✓ Nintログイン成功")

        except Exception as e:
            print(f"✗ Nintログイン失敗: {e}")
            raise

    def search_market(self, keyword: str) -> Optional[NintMarketData]:
        """キーワードで市場分析データを取得

        Args:
            keyword: 検索キーワード

        Returns:
            市場データ、取得失敗時はNone
        """
        if not self.page:
            raise RuntimeError("Playwright page not initialized")

        try:
            # 検索ページに移動
            self.page.goto(self.SEARCH_URL, timeout=30000)

            # キーワード入力・検索
            # ※実際のセレクタはNintのHTMLに合わせて調整が必要
            self.page.fill('input[name="keyword"]', keyword)
            self.page.click('button[type="submit"]')

            # 結果ページを待機
            self.page.wait_for_selector("div.market-stats", timeout=30000)

            # データをパース
            market_data = self._parse_market_data(keyword)
            return market_data

        except Exception as e:
            print(f"市場データ取得エラー ({keyword}): {e}")
            return None

    def _parse_market_data(self, keyword: str) -> NintMarketData:
        """市場データをパース

        Args:
            keyword: 検索キーワード

        Returns:
            パースされた市場データ
        """
        if not self.page:
            raise RuntimeError("Playwright page not initialized")

        # ※以下は仮実装。実際のNintのHTML構造に合わせて要調整

        # 推定月販数を取得
        monthly_sales_text = self.page.locator("span.monthly-sales").inner_text()
        estimated_monthly_sales = int(monthly_sales_text.replace(",", "").replace("個", ""))

        # 売上推移を取得(過去6ヶ月)
        revenue_trend = self._extract_revenue_trend()

        # 価格推移を取得
        price_trend = self._extract_price_trend()

        # 上位店舗を取得
        top_sellers = self._extract_top_sellers()

        # 平均価格
        avg_price_text = self.page.locator("span.avg-price").inner_text()
        avg_price = float(avg_price_text.replace(",", "").replace("円", ""))

        # 価格変動係数(標準偏差/平均)
        price_volatility = self._calculate_price_volatility(price_trend)

        # 成長率(直近3ヶ月 vs 過去3ヶ月)
        growth_rate = self._calculate_growth_rate(revenue_trend)

        return NintMarketData(
            keyword=keyword,
            estimated_monthly_sales=estimated_monthly_sales,
            revenue_trend=revenue_trend,
            price_trend=price_trend,
            top_sellers=top_sellers,
            avg_price=avg_price,
            price_volatility=price_volatility,
            growth_rate=growth_rate,
        )

    def _extract_revenue_trend(self) -> List[Dict[str, Any]]:
        """売上推移を抽出

        Returns:
            [{date: "2024-01", revenue: 1000000}, ...]
        """
        if not self.page:
            return []

        # ※仮実装: 実際のNintのグラフデータ取得方法に要調整
        trend_data = []
        today = datetime.now()

        for i in range(6):
            month_date = today - timedelta(days=30 * i)
            date_str = month_date.strftime("%Y-%m")

            # 実際にはDOMから取得
            revenue = 1000000 - (i * 50000)  # ダミーデータ

            trend_data.append({"date": date_str, "revenue": revenue})

        return list(reversed(trend_data))

    def _extract_price_trend(self) -> List[Dict[str, Any]]:
        """価格推移を抽出

        Returns:
            [{date: "2024-01", avg_price: 5980}, ...]
        """
        if not self.page:
            return []

        # ※仮実装
        trend_data = []
        today = datetime.now()

        for i in range(6):
            month_date = today - timedelta(days=30 * i)
            date_str = month_date.strftime("%Y-%m")

            # 実際にはDOMから取得
            avg_price = 6000 - (i * 100)  # ダミーデータ

            trend_data.append({"date": date_str, "avg_price": avg_price})

        return list(reversed(trend_data))

    def _extract_top_sellers(self) -> List[Dict[str, Any]]:
        """上位店舗情報を抽出

        Returns:
            [{shop_name: "店舗A", monthly_sales: 500, market_share: 25.0}, ...]
        """
        if not self.page:
            return []

        # ※仮実装: 実際のNintのランキングテーブルから取得
        top_sellers = [
            {"shop_name": "トップショップA", "monthly_sales": 500, "market_share": 25.0},
            {"shop_name": "トップショップB", "monthly_sales": 400, "market_share": 20.0},
            {"shop_name": "トップショップC", "monthly_sales": 300, "market_share": 15.0},
            {"shop_name": "トップショップD", "monthly_sales": 200, "market_share": 10.0},
            {"shop_name": "トップショップE", "monthly_sales": 200, "market_share": 10.0},
        ]

        return top_sellers

    def _calculate_price_volatility(self, price_trend: List[Dict[str, Any]]) -> float:
        """価格変動係数(CV)を計算

        Args:
            price_trend: 価格推移データ

        Returns:
            CV = 標準偏差 / 平均
        """
        if not price_trend:
            return 0.0

        prices = [p["avg_price"] for p in price_trend]
        avg = sum(prices) / len(prices)

        variance = sum((p - avg) ** 2 for p in prices) / len(prices)
        std_dev = variance**0.5

        cv = (std_dev / avg) * 100 if avg > 0 else 0.0
        return round(cv, 2)

    def _calculate_growth_rate(self, revenue_trend: List[Dict[str, Any]]) -> float:
        """成長率を計算(直近3ヶ月 vs 過去3ヶ月)

        Args:
            revenue_trend: 売上推移データ

        Returns:
            成長率(%)
        """
        if len(revenue_trend) < 6:
            return 0.0

        recent_3m = sum(r["revenue"] for r in revenue_trend[-3:])
        previous_3m = sum(r["revenue"] for r in revenue_trend[:3])

        growth_rate = ((recent_3m - previous_3m) / previous_3m) * 100 if previous_3m > 0 else 0.0
        return round(growth_rate, 2)
