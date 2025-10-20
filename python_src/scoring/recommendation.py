"""推奨判定エンジン

総合スコアと利益率から GO/Conditional/No-Go を判定
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from python_src.scoring.scorer import ComprehensiveScore
from python_src.analyzers.profit_calculator import ProfitAnalysis


class RecommendationType(str, Enum):
    """推奨タイプ"""

    GO = "GO"  # 参入推奨
    CONDITIONAL = "Conditional"  # 条件付き推奨
    NO_GO = "No-Go"  # 参入非推奨


class Recommendation(BaseModel):
    """推奨結果"""

    decision: RecommendationType = Field(description="判定結果")
    confidence: float = Field(description="信頼度 (0-100)")
    recommended_price: Optional[float] = Field(default=None, description="推奨価格")
    reasoning: str = Field(description="判定理由")
    action_items: list[str] = Field(default_factory=list, description="アクションアイテム")


class RecommendationEngine:
    """推奨判定エンジン"""

    # 判定しきい値
    GO_SCORE_THRESHOLD = 75
    GO_MARGIN_THRESHOLD = 20.0

    CONDITIONAL_SCORE_THRESHOLD = 60
    CONDITIONAL_MARGIN_THRESHOLD = 15.0

    def recommend(
        self,
        comprehensive_score: ComprehensiveScore,
        profit_analysis: ProfitAnalysis,
    ) -> Recommendation:
        """推奨を判定

        Args:
            comprehensive_score: 総合スコア
            profit_analysis: 利益分析結果

        Returns:
            推奨結果
        """
        total_score = comprehensive_score.total_score
        gross_margin = profit_analysis.gross_margin
        monthly_profit = profit_analysis.estimated_monthly_profit

        # GO判定
        if (
            total_score >= self.GO_SCORE_THRESHOLD
            and gross_margin >= self.GO_MARGIN_THRESHOLD
        ):
            return self._make_go_recommendation(comprehensive_score, profit_analysis)

        # Conditional判定
        elif (
            total_score >= self.CONDITIONAL_SCORE_THRESHOLD
            and gross_margin >= self.CONDITIONAL_MARGIN_THRESHOLD
        ):
            return self._make_conditional_recommendation(
                comprehensive_score, profit_analysis
            )

        # No-Go判定
        else:
            return self._make_no_go_recommendation(comprehensive_score, profit_analysis)

    def _make_go_recommendation(
        self, score: ComprehensiveScore, profit: ProfitAnalysis
    ) -> Recommendation:
        """GO推奨を作成"""
        confidence = (score.total_score + profit.gross_margin) / 2

        reasoning = (
            f"総合スコア{score.total_score}点、粗利率{profit.gross_margin:.1f}%で "
            "参入推奨基準を満たしています。市場機会が大きく、競争力のある価格設定が可能です。"
        )

        action_items = [
            "仕入先との価格交渉を進めてください",
            "サムネイル画像を高品質化して競合と差別化",
            f"推定月間利益: ¥{profit.estimated_monthly_profit:,.0f}",
            f"損益分岐点: {profit.break_even_quantity}個/月",
        ]

        return Recommendation(
            decision=RecommendationType.GO,
            confidence=round(confidence, 2),
            recommended_price=profit.selling_price,
            reasoning=reasoning,
            action_items=action_items,
        )

    def _make_conditional_recommendation(
        self, score: ComprehensiveScore, profit: ProfitAnalysis
    ) -> Recommendation:
        """Conditional推奨を作成"""
        confidence = (score.total_score + profit.gross_margin) / 2 * 0.8

        # 改善ポイントを特定
        weak_points = []
        if score.price_competitiveness < 60:
            weak_points.append("価格競争力")
        if score.market_opportunity < 60:
            weak_points.append("市場規模")
        if score.thumbnail_quality < 60:
            weak_points.append("サムネイル品質")
        if profit.gross_margin < 20:
            weak_points.append("粗利率")

        reasoning = (
            f"総合スコア{score.total_score}点、粗利率{profit.gross_margin:.1f}%で "
            f"条件付き推奨です。以下の改善が必要: {', '.join(weak_points)}"
        )

        action_items = [
            "仕入価格の再交渉を検討してください",
            "競合分析を深掘りし、差別化ポイントを明確化",
            "テスト販売(少量仕入)から開始を推奨",
            f"推定月間利益: ¥{profit.estimated_monthly_profit:,.0f}(改善余地あり)",
        ]

        return Recommendation(
            decision=RecommendationType.CONDITIONAL,
            confidence=round(confidence, 2),
            recommended_price=profit.selling_price,
            reasoning=reasoning,
            action_items=action_items,
        )

    def _make_no_go_recommendation(
        self, score: ComprehensiveScore, profit: ProfitAnalysis
    ) -> Recommendation:
        """No-Go推奨を作成"""
        confidence = 100 - ((score.total_score + profit.gross_margin) / 2)

        # 主要な問題点を特定
        critical_issues = []
        if score.price_competitiveness < 40:
            critical_issues.append("価格競争力が著しく低い")
        if score.market_opportunity < 40:
            critical_issues.append("市場規模が不十分")
        if score.competition_level < 40:
            critical_issues.append("競争が激しすぎる(寡占市場)")
        if profit.gross_margin < 15:
            critical_issues.append("粗利率が低すぎる")

        reasoning = (
            f"総合スコア{score.total_score}点、粗利率{profit.gross_margin:.1f}%で "
            f"参入非推奨です。主な問題: {', '.join(critical_issues)}"
        )

        action_items = [
            "この商品への参入は見送りを推奨します",
            "他の商品候補を検討してください",
            "仕入先に大幅な価格交渉が可能であれば再評価",
        ]

        return Recommendation(
            decision=RecommendationType.NO_GO,
            confidence=round(confidence, 2),
            recommended_price=None,
            reasoning=reasoning,
            action_items=action_items,
        )
