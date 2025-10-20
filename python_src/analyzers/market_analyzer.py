"""市場分析(Nintデータベース)"""

import math
from typing import Optional
from pydantic import BaseModel, Field

from python_src.scrapers.nint_scraper import NintMarketData


class MarketAnalysisScore(BaseModel):
    """市場分析スコア"""

    market_size_score: float = Field(description="市場規模スコア (0-100)")
    growth_score: float = Field(description="成長性スコア (0-100)")
    competition_score: float = Field(description="競争度スコア (0-100)")
    total_score: float = Field(description="総合市場スコア (0-100)")


class MarketAnalyzer:
    """市場分析"""

    def analyze(self, nint_data: NintMarketData) -> MarketAnalysisScore:
        """Nintデータから市場を分析

        Args:
            nint_data: Nint市場データ

        Returns:
            市場分析スコア
        """
        market_size_score = self._score_market_size(nint_data.estimated_monthly_sales)
        growth_score = self._score_growth(nint_data.growth_rate or 0.0)
        competition_score = self._score_competition(nint_data.top_sellers)

        total_score = (market_size_score + growth_score + competition_score) / 3

        return MarketAnalysisScore(
            market_size_score=market_size_score,
            growth_score=growth_score,
            competition_score=competition_score,
            total_score=round(total_score, 2),
        )

    def _score_market_size(self, monthly_sales: int) -> float:
        """市場規模スコア (0-100)

        Args:
            monthly_sales: 推定月販数

        Returns:
            スコア
        """
        # 対数スケールでスコア化
        # 月販10個: 20点
        # 月販100個: 40点
        # 月販1000個: 60点
        # 月販10000個: 80点
        # 月販100000個: 100点

        if monthly_sales <= 0:
            return 0.0

        log_sales = math.log10(monthly_sales)
        score = 20 * log_sales

        return min(100.0, max(0.0, round(score, 2)))

    def _score_growth(self, growth_rate: float) -> float:
        """成長性スコア (0-100)

        Args:
            growth_rate: 成長率(%)

        Returns:
            スコア
        """
        # 成長率が高いほど高スコア
        # -50%: 0点
        # 0%: 50点
        # +50%: 80点
        # +100%以上: 100点

        if growth_rate <= -50:
            score = 0.0
        elif growth_rate <= 0:
            score = 50 + (growth_rate / 50) * 50
        elif growth_rate <= 50:
            score = 50 + (growth_rate / 50) * 30
        else:
            score = min(100.0, 80 + ((growth_rate - 50) / 50) * 20)

        return round(score, 2)

    def _score_competition(self, top_sellers: list) -> float:
        """競争度スコア (0-100)

        上位店舗のシェアが分散しているほど参入余地があり高スコア

        Args:
            top_sellers: 上位店舗リスト

        Returns:
            スコア
        """
        if not top_sellers:
            return 50.0  # データなしの場合は中立

        # 上位5店舗のシェア合計
        top_5_share = sum(seller.get("market_share", 0) for seller in top_sellers[:5])

        # シェアが分散しているほど高スコア
        # 上位5店舗シェア < 40%: 100点(参入余地大)
        # 上位5店舗シェア = 60%: 50点
        # 上位5店舗シェア > 80%: 0点(寡占市場)

        if top_5_share < 40:
            score = 100.0
        elif top_5_share <= 80:
            score = 100 - ((top_5_share - 40) / 40) * 100
        else:
            score = 0.0

        return round(score, 2)
