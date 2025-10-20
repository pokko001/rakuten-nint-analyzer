"""楽天市場スクレイパー

楽天市場から商品情報を取得:
- 価格・税込/税抜
- 送料
- ポイント倍率
- クーポン情報
- サムネイル画像URL
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field


class RakutenProduct(BaseModel):
    """楽天商品データモデル"""

    product_name: str
    shop_name: str
    price: int = Field(description="税込価格")
    price_tax_excluded: Optional[int] = Field(default=None, description="税抜価格")
    shipping_fee: int = Field(default=0, description="送料")
    total_price: int = Field(description="送料込み価格")
    point_rate: int = Field(default=1, description="ポイント倍率")
    coupon_discount: int = Field(default=0, description="クーポン値引き額")
    thumbnail_url: str
    product_url: str
    jan_code: Optional[str] = Field(default=None)
    rank: int = Field(description="検索結果での順位")


class RakutenScraper:
    """楽天市場スクレイパー"""

    BASE_URL = "https://search.rakuten.co.jp/search/mall"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, app_id: Optional[str] = None):
        """
        Args:
            app_id: 楽天APIアプリID(任意)
        """
        self.app_id = app_id
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def search_by_keyword(
        self, keyword: str, max_results: int = 20
    ) -> List[RakutenProduct]:
        """キーワードで楽天市場を検索

        Args:
            keyword: 検索キーワード
            max_results: 取得する最大件数

        Returns:
            商品情報リスト(検索順位順)
        """
        encoded_keyword = quote(keyword)
        url = f"{self.BASE_URL}/{encoded_keyword}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            products = self._parse_search_results(soup, max_results)
            return products

        except requests.RequestException as e:
            print(f"楽天市場検索エラー: {e}")
            return []

    def search_by_jan(self, jan_code: str, max_results: int = 20) -> List[RakutenProduct]:
        """JANコードで楽天市場を検索

        Args:
            jan_code: JANコード
            max_results: 取得する最大件数

        Returns:
            商品情報リスト
        """
        return self.search_by_keyword(jan_code, max_results)

    def _parse_search_results(
        self, soup: BeautifulSoup, max_results: int
    ) -> List[RakutenProduct]:
        """検索結果HTMLをパース

        Args:
            soup: BeautifulSoupオブジェクト
            max_results: 取得する最大件数

        Returns:
            商品情報リスト
        """
        products: List[RakutenProduct] = []
        items = soup.select("div.searchresultitem")[:max_results]

        for rank, item in enumerate(items, start=1):
            try:
                product = self._parse_item(item, rank)
                if product:
                    products.append(product)
            except Exception as e:
                print(f"商品パースエラー (rank={rank}): {e}")
                continue

        return products

    def _parse_item(self, item: BeautifulSoup, rank: int) -> Optional[RakutenProduct]:
        """個別商品をパース

        Args:
            item: 商品要素
            rank: 検索順位

        Returns:
            商品情報、パース失敗時はNone
        """
        # 商品名
        title_elem = item.select_one("a.title")
        if not title_elem:
            return None
        product_name = title_elem.get_text(strip=True)
        product_url = title_elem.get("href", "")

        # 店舗名
        shop_elem = item.select_one("div.merchant")
        shop_name = shop_elem.get_text(strip=True) if shop_elem else "不明"

        # 価格
        price_elem = item.select_one("span.price")
        if not price_elem:
            return None
        price_text = price_elem.get_text(strip=True)
        price = self._extract_price(price_text)

        # 送料
        shipping_elem = item.select_one("span.shipping")
        shipping_fee = 0
        if shipping_elem and "送料別" in shipping_elem.get_text():
            shipping_fee = self._estimate_shipping_fee(item)

        # ポイント倍率
        point_elem = item.select_one("span.point")
        point_rate = 1
        if point_elem:
            point_text = point_elem.get_text(strip=True)
            point_rate = self._extract_point_rate(point_text)

        # クーポン
        coupon_elem = item.select_one("span.coupon")
        coupon_discount = 0
        if coupon_elem:
            coupon_text = coupon_elem.get_text(strip=True)
            coupon_discount = self._extract_coupon_discount(coupon_text)

        # サムネイル
        img_elem = item.select_one("img.image")
        thumbnail_url = img_elem.get("src", "") if img_elem else ""

        # JANコード(商品ページから取得が必要な場合もあるため、現状はNone)
        jan_code = None

        total_price = price + shipping_fee

        return RakutenProduct(
            product_name=product_name,
            shop_name=shop_name,
            price=price,
            shipping_fee=shipping_fee,
            total_price=total_price,
            point_rate=point_rate,
            coupon_discount=coupon_discount,
            thumbnail_url=thumbnail_url,
            product_url=product_url,
            jan_code=jan_code,
            rank=rank,
        )

    def _extract_price(self, price_text: str) -> int:
        """価格テキストから数値を抽出

        Args:
            price_text: 価格文字列 (例: "¥1,980")

        Returns:
            価格(整数)
        """
        numbers = re.findall(r"\d+", price_text.replace(",", ""))
        return int("".join(numbers)) if numbers else 0

    def _estimate_shipping_fee(self, item: BeautifulSoup) -> int:
        """送料を推定(詳細ページ参照が必要な場合もあるため、暫定値)

        Args:
            item: 商品要素

        Returns:
            推定送料
        """
        # 送料別の場合、デフォルト550円と仮定
        # 実際にはショップごとに異なるため、詳細ページを見る必要がある
        return 550

    def _extract_point_rate(self, point_text: str) -> int:
        """ポイント倍率を抽出

        Args:
            point_text: ポイント文字列 (例: "ポイント10倍")

        Returns:
            倍率(整数)
        """
        match = re.search(r"(\d+)倍", point_text)
        return int(match.group(1)) if match else 1

    def _extract_coupon_discount(self, coupon_text: str) -> int:
        """クーポン値引き額を抽出

        Args:
            coupon_text: クーポン文字列 (例: "500円OFF")

        Returns:
            値引き額(整数)
        """
        match = re.search(r"(\d+)円", coupon_text.replace(",", ""))
        return int(match.group(1)) if match else 0

    def get_market_stats(self, products: List[RakutenProduct]) -> Dict[str, Any]:
        """市場統計を計算

        Args:
            products: 商品リスト

        Returns:
            統計データ
        """
        if not products:
            return {}

        prices = [p.total_price for p in products]
        point_rates = [p.point_rate for p in products]
        coupon_discounts = [p.coupon_discount for p in products if p.coupon_discount > 0]

        return {
            "avg_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "median_price": sorted(prices)[len(prices) // 2],
            "avg_point_rate": sum(point_rates) / len(point_rates),
            "max_point_rate": max(point_rates),
            "coupon_availability": len(coupon_discounts) / len(products) * 100,
            "avg_coupon_discount": (
                sum(coupon_discounts) / len(coupon_discounts) if coupon_discounts else 0
            ),
            "total_shops": len(set(p.shop_name for p in products)),
        }
