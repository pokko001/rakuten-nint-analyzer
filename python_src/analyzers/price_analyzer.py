"""価格競争力分析"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field

from python_src.scrapers.rakuten_scraper import RakutenProduct


class PriceAnalysis(BaseModel):
    """価格分析結果"""

    avg_price: float = Field(description="上位平均価格")
    min_price: float = Field(description="最安価格")
    max_price: float = Field(description="最高価格")
    median_price: float = Field(description="中央値価格")
    price_range: float = Field(description="価格幅")
    competitive_price: float = Field(description="推奨販売価格(競争力あり)")
    price_competitiveness_score: float = Field(description="価格競争力スコア (0-100)")


class PriceAnalyzer:
    """価格競争力分析"""

    def analyze(
        self, products: List[RakutenProduct], target_price: float
    ) -> PriceAnalysis:
        """価格競争力を分析

        Args:
            products: 楽天商品リスト
            target_price: 想定販売価格

        Returns:
            価格分析結果
        """
        if not products:
            raise ValueError("商品リストが空です")

        prices = [p.total_price for p in products]
        prices_sorted = sorted(prices)

        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        median_price = prices_sorted[len(prices_sorted) // 2]
        price_range = max_price - min_price

        # 推奨価格: 平均価格の95%程度
        competitive_price = avg_price * 0.95

        # 価格競争力スコア
        competitiveness_score = self._calculate_competitiveness_score(
            target_price, avg_price, min_price
        )

        return PriceAnalysis(
            avg_price=avg_price,
            min_price=min_price,
            max_price=max_price,
            median_price=median_price,
            price_range=price_range,
            competitive_price=competitive_price,
            price_competitiveness_score=competitiveness_score,
        )

    def _calculate_competitiveness_score(
        self, target_price: float, avg_price: float, min_price: float
    ) -> float:
        """価格競争力スコアを計算 (0-100)

        Args:
            target_price: 想定販売価格
            avg_price: 市場平均価格
            min_price: 市場最安価格

        Returns:
            競争力スコア
        """
        # 最安値よりも安い: 100点
        # 平均価格と同じ: 50点
        # 平均価格より高い: 0-50点(段階的に減点)

        if target_price <= min_price:
            return 100.0
        elif target_price <= avg_price:
            # 最安値から平均価格の間: 50-100点
            ratio = (avg_price - target_price) / (avg_price - min_price)
            score = 50 + (ratio * 50)
        else:
            # 平均価格より高い: 0-50点
            price_diff = target_price - avg_price
            max_acceptable_diff = avg_price * 0.2  # 平均+20%まで許容

            if price_diff > max_acceptable_diff:
                score = 0.0
            else:
                score = 50 * (1 - (price_diff / max_acceptable_diff))

        return round(score, 2)
