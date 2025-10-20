"""総合スコアリングエンジン

各種分析結果を統合し、総合スコアを算出
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

from python_src.analyzers.price_analyzer import PriceAnalysis
from python_src.analyzers.market_analyzer import MarketAnalysisScore
from python_src.analyzers.thumbnail_analyzer import ThumbnailScore
from python_src.analyzers.profit_calculator import ProfitAnalysis
from python_src.scrapers.nint_scraper import NintMarketData


class ComprehensiveScore(BaseModel):
    """総合スコア"""

    price_competitiveness: float = Field(description="価格競争力スコア")
    market_opportunity: float = Field(description="市場機会スコア")
    competition_level: float = Field(description="競争度スコア")
    thumbnail_quality: float = Field(description="サムネイル品質スコア")
    profitability: float = Field(description="利益性スコア")
    risk_level: float = Field(description="リスクスコア")

    total_score: float = Field(description="総合スコア (0-100)")

    weights: Dict[str, float] = Field(description="各スコアのウェイト")
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細データ")


class ComprehensiveScorer:
    """総合スコアリング"""

    # デフォルトウェイト
    DEFAULT_WEIGHTS = {
        "price_competitiveness": 0.25,  # 25%
        "market_opportunity": 0.30,  # 30%
        "competition_level": 0.15,  # 15%
        "thumbnail_quality": 0.15,  # 15%
        "profitability": 0.10,  # 10%
        "risk_level": 0.05,  # 5%
    }

    def __init__(self, weights: Dict[str, float] = None):
        """
        Args:
            weights: カスタムウェイト(省略時はデフォルト)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()

    def _validate_weights(self) -> None:
        """ウェイトの合計が1.0であることを確認"""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"ウェイトの合計が1.0ではありません: {total}")

    def calculate(
        self,
        price_analysis: PriceAnalysis,
        market_score: MarketAnalysisScore,
        thumbnail_score: ThumbnailScore,
        profit_analysis: ProfitAnalysis,
        nint_data: NintMarketData,
    ) -> ComprehensiveScore:
        """総合スコアを計算

        Args:
            price_analysis: 価格分析結果
            market_score: 市場分析スコア
            thumbnail_score: サムネイル品質スコア
            profit_analysis: 利益分析結果
            nint_data: Nint市場データ

        Returns:
            総合スコア
        """
        # 各スコアを正規化(0-100)
        price_comp_score = price_analysis.price_competitiveness_score

        market_opp_score = market_score.market_size_score

        competition_score = market_score.competition_score

        thumbnail_qual_score = thumbnail_score.total_score

        profit_score = self._score_profitability(profit_analysis)

        risk_score = self._score_risk(nint_data, profit_analysis)

        # 加重平均で総合スコアを計算
        total_score = (
            price_comp_score * self.weights["price_competitiveness"]
            + market_opp_score * self.weights["market_opportunity"]
            + competition_score * self.weights["competition_level"]
            + thumbnail_qual_score * self.weights["thumbnail_quality"]
            + profit_score * self.weights["profitability"]
            + risk_score * self.weights["risk_level"]
        )

        return ComprehensiveScore(
            price_competitiveness=round(price_comp_score, 2),
            market_opportunity=round(market_opp_score, 2),
            competition_level=round(competition_score, 2),
            thumbnail_quality=round(thumbnail_qual_score, 2),
            profitability=round(profit_score, 2),
            risk_level=round(risk_score, 2),
            total_score=round(total_score, 2),
            weights=self.weights,
            details={
                "gross_margin": profit_analysis.gross_margin,
                "estimated_monthly_profit": profit_analysis.estimated_monthly_profit,
                "roi": profit_analysis.roi,
            },
        )

    def _score_profitability(self, profit_analysis: ProfitAnalysis) -> float:
        """利益性スコア (0-100)

        Args:
            profit_analysis: 利益分析結果

        Returns:
            スコア
        """
        # 粗利率ベースでスコア化
        # 粗利率 < 10%: 0点
        # 粗利率 = 20%: 50点
        # 粗利率 = 30%: 80点
        # 粗利率 >= 40%: 100点

        margin = profit_analysis.gross_margin

        if margin < 10:
            score = margin * 5  # 0-50点
        elif margin < 30:
            score = 50 + ((margin - 10) / 20) * 30  # 50-80点
        elif margin < 40:
            score = 80 + ((margin - 30) / 10) * 20  # 80-100点
        else:
            score = 100.0

        return round(score, 2)

    def _score_risk(
        self, nint_data: NintMarketData, profit_analysis: ProfitAnalysis
    ) -> float:
        """リスクスコア (0-100)

        リスクが低いほど高スコア

        Args:
            nint_data: Nint市場データ
            profit_analysis: 利益分析結果

        Returns:
            スコア
        """
        # 価格変動リスク
        price_volatility = nint_data.price_volatility or 0.0

        # 粗利率が低いほどリスク高
        margin_risk = 100 - min(100, profit_analysis.gross_margin * 5)

        # 価格変動が大きいほどリスク高
        # CV < 5%: リスク低(20点)
        # CV = 10%: リスク中(10点)
        # CV > 20%: リスク高(0点)
        if price_volatility < 5:
            volatility_risk = 20 - price_volatility * 2
        elif price_volatility < 20:
            volatility_risk = 20 - ((price_volatility - 5) / 15) * 20
        else:
            volatility_risk = 0.0

        # リスクスコア = 100 - 総合リスク
        total_risk = margin_risk * 0.6 + volatility_risk * 0.4
        risk_score = 100 - total_risk

        return max(0.0, min(100.0, round(risk_score, 2)))
