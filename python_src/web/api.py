"""FastAPI Webアプリケーション

楽天・Nint商品分析APIとダッシュボード
"""

from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from python_src.scrapers.rakuten_scraper import RakutenScraper
from python_src.scrapers.nint_scraper import NintScraper
from python_src.analyzers.thumbnail_analyzer import ThumbnailAnalyzer
from python_src.analyzers.price_analyzer import PriceAnalyzer
from python_src.analyzers.market_analyzer import MarketAnalyzer
from python_src.analyzers.profit_calculator import ProfitCalculator
from python_src.scoring.scorer import ComprehensiveScorer
from python_src.scoring.recommendation import RecommendationEngine
from python_src.utils.config import settings

# FastAPIアプリケーション初期化
app = FastAPI(
    title="楽天市場・Nint商品分析ツール",
    description="卸業者からの商品リストを基に仕入れ判断を自動化",
    version="0.1.0",
)

# テンプレートとスタティックファイル設定
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
# app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# リクエスト/レスポンスモデル
class AnalyzeRequest(BaseModel):
    """分析リクエスト"""

    keyword: str = Field(description="検索キーワードまたはJANコード")
    purchase_price: float = Field(description="仕入価格")
    target_selling_price: Optional[float] = Field(
        default=None, description="目標販売価格(省略時は自動算出)"
    )
    max_results: int = Field(default=20, description="楽天検索結果の取得件数")


class AnalyzeResponse(BaseModel):
    """分析レスポンス"""

    keyword: str
    recommendation: dict
    comprehensive_score: dict
    price_analysis: dict
    market_analysis: dict
    profit_analysis: dict
    rakuten_products: List[dict]
    nint_market_data: dict


# ルート
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """トップページ"""
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "楽天・Nint商品分析ツール"}
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_product(request: AnalyzeRequest):
    """商品を分析

    Args:
        request: 分析リクエスト

    Returns:
        分析結果
    """
    try:
        # 1. 楽天市場から商品情報を取得
        rakuten_scraper = RakutenScraper()
        rakuten_products = rakuten_scraper.search_by_keyword(
            request.keyword, max_results=request.max_results
        )

        if not rakuten_products:
            raise HTTPException(
                status_code=404, detail=f"キーワード '{request.keyword}' で商品が見つかりませんでした"
            )

        # 2. Nintから市場データを取得
        with NintScraper(
            email=settings.nint_login_email, password=settings.nint_login_password
        ) as nint_scraper:
            nint_data = nint_scraper.search_market(request.keyword)

        if not nint_data:
            raise HTTPException(
                status_code=500, detail="Nintからデータを取得できませんでした"
            )

        # 3. 販売価格の決定
        profit_calc = ProfitCalculator()
        if request.target_selling_price:
            selling_price = request.target_selling_price
        else:
            # 目標粗利率20%で推奨価格を算出
            selling_price = profit_calc.calculate_recommended_price(
                purchase_price=request.purchase_price, target_margin=20.0
            )

        # 4. 各種分析
        # 4-1. 価格分析
        price_analyzer = PriceAnalyzer()
        price_analysis = price_analyzer.analyze(rakuten_products, selling_price)

        # 4-2. 市場分析
        market_analyzer = MarketAnalyzer()
        market_score = market_analyzer.analyze(nint_data)

        # 4-3. サムネイル品質分析(上位3件の平均)
        thumbnail_analyzer = ThumbnailAnalyzer()
        thumbnail_scores = []
        for product in rakuten_products[:3]:
            score = thumbnail_analyzer.analyze_from_url(product.thumbnail_url)
            if score:
                thumbnail_scores.append(score)

        avg_thumbnail_score = (
            sum(s.total_score for s in thumbnail_scores) / len(thumbnail_scores)
            if thumbnail_scores
            else 50.0
        )
        # 代表値として最初のスコアを使用
        thumbnail_score = thumbnail_scores[0] if thumbnail_scores else None

        # 4-4. 利益計算
        profit_analysis = profit_calc.calculate(
            purchase_price=request.purchase_price,
            selling_price=selling_price,
            estimated_monthly_sales=nint_data.estimated_monthly_sales,
        )

        # 5. 総合スコアリング
        scorer = ComprehensiveScorer()
        # サムネイルスコアがない場合はダミーを作成
        if not thumbnail_score:
            from python_src.analyzers.thumbnail_analyzer import ThumbnailScore

            thumbnail_score = ThumbnailScore(
                total_score=50.0,
                resolution_score=15.0,
                text_density_score=12.5,
                background_score=12.5,
                brightness_score=10.0,
            )

        comprehensive_score = scorer.calculate(
            price_analysis=price_analysis,
            market_score=market_score,
            thumbnail_score=thumbnail_score,
            profit_analysis=profit_analysis,
            nint_data=nint_data,
        )

        # 6. 推奨判定
        recommender = RecommendationEngine()
        recommendation = recommender.recommend(comprehensive_score, profit_analysis)

        # レスポンス作成
        return AnalyzeResponse(
            keyword=request.keyword,
            recommendation=recommendation.model_dump(),
            comprehensive_score=comprehensive_score.model_dump(),
            price_analysis=price_analysis.model_dump(),
            market_analysis=market_score.model_dump(),
            profit_analysis=profit_analysis.model_dump(),
            rakuten_products=[p.model_dump() for p in rakuten_products],
            nint_market_data=nint_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析エラー: {str(e)}")


@app.get("/api/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.dashboard_host,
        port=settings.dashboard_port,
        reload=settings.debug,
    )
