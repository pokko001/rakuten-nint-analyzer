"""利益計算・販売予測"""

from typing import Optional
from pydantic import BaseModel, Field


class ProfitAnalysis(BaseModel):
    """利益分析結果"""

    purchase_price: float = Field(description="仕入価格")
    selling_price: float = Field(description="販売価格")
    gross_profit: float = Field(description="粗利額")
    gross_margin: float = Field(description="粗利率(%)")
    estimated_monthly_sales: int = Field(description="推定月販数")
    estimated_monthly_profit: float = Field(description="推定月間利益")
    break_even_quantity: int = Field(description="損益分岐点販売数")
    roi: float = Field(description="投資収益率(ROI, %)")


class ProfitCalculator:
    """利益計算・販売予測"""

    # 楽天手数料(カテゴリによって異なるが、平均8%と仮定)
    RAKUTEN_FEE_RATE = 0.08

    # その他費用(梱包・発送等)
    DEFAULT_SHIPPING_COST = 500
    DEFAULT_PACKAGING_COST = 100

    def calculate(
        self,
        purchase_price: float,
        selling_price: float,
        estimated_monthly_sales: int,
        shipping_cost: float = DEFAULT_SHIPPING_COST,
        packaging_cost: float = DEFAULT_PACKAGING_COST,
        fixed_cost: float = 0.0,
    ) -> ProfitAnalysis:
        """利益を計算

        Args:
            purchase_price: 仕入価格
            selling_price: 販売価格
            estimated_monthly_sales: 推定月販数
            shipping_cost: 送料(1個あたり)
            packaging_cost: 梱包費(1個あたり)
            fixed_cost: 月額固定費(広告費など)

        Returns:
            利益分析結果
        """
        # 楽天手数料
        rakuten_fee = selling_price * self.RAKUTEN_FEE_RATE

        # 1個あたりの総コスト
        unit_cost = purchase_price + shipping_cost + packaging_cost + rakuten_fee

        # 粗利
        gross_profit = selling_price - unit_cost
        gross_margin = (gross_profit / selling_price) * 100 if selling_price > 0 else 0

        # 推定月間利益
        monthly_profit = (gross_profit * estimated_monthly_sales) - fixed_cost

        # 損益分岐点販売数
        if gross_profit > 0:
            break_even_quantity = int(fixed_cost / gross_profit) + 1
        else:
            break_even_quantity = 0

        # ROI(投資収益率)
        total_investment = purchase_price * estimated_monthly_sales + fixed_cost
        roi = (monthly_profit / total_investment) * 100 if total_investment > 0 else 0

        return ProfitAnalysis(
            purchase_price=purchase_price,
            selling_price=selling_price,
            gross_profit=round(gross_profit, 2),
            gross_margin=round(gross_margin, 2),
            estimated_monthly_sales=estimated_monthly_sales,
            estimated_monthly_profit=round(monthly_profit, 2),
            break_even_quantity=break_even_quantity,
            roi=round(roi, 2),
        )

    def calculate_recommended_price(
        self,
        purchase_price: float,
        target_margin: float = 20.0,
        shipping_cost: float = DEFAULT_SHIPPING_COST,
        packaging_cost: float = DEFAULT_PACKAGING_COST,
    ) -> float:
        """目標粗利率から推奨販売価格を逆算

        Args:
            purchase_price: 仕入価格
            target_margin: 目標粗利率(%)
            shipping_cost: 送料
            packaging_cost: 梱包費

        Returns:
            推奨販売価格
        """
        # 売価をxとすると:
        # margin = (x - (purchase + shipping + packaging + x * fee_rate)) / x
        # margin * x = x - purchase - shipping - packaging - x * fee_rate
        # x * (margin + fee_rate) = x - purchase - shipping - packaging
        # x = (purchase + shipping + packaging) / (1 - margin - fee_rate)

        cost_base = purchase_price + shipping_cost + packaging_cost
        margin_rate = target_margin / 100

        recommended_price = cost_base / (1 - margin_rate - self.RAKUTEN_FEE_RATE)

        return round(recommended_price, 2)
