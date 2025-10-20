"""設定管理モジュール"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# .envファイルをロード
load_dotenv()


class Settings(BaseSettings):
    """アプリケーション設定"""

    # 楽天API設定
    rakuten_app_id: Optional[str] = Field(default=None, alias="RAKUTEN_APP_ID")
    rakuten_affiliate_id: Optional[str] = Field(default=None, alias="RAKUTEN_AFFILIATE_ID")

    # Nint認証情報
    nint_login_email: str = Field(..., alias="NINT_LOGIN_EMAIL")
    nint_login_password: str = Field(..., alias="NINT_LOGIN_PASSWORD")

    # データベース
    database_url: str = Field(default="sqlite:///./data/analyzer.db", alias="DATABASE_URL")

    # Webダッシュボード
    dashboard_host: str = Field(default="0.0.0.0", alias="DASHBOARD_HOST")
    dashboard_port: int = Field(default=8000, alias="DASHBOARD_PORT")
    debug: bool = Field(default=True, alias="DEBUG")

    # プロジェクトルート
    project_root: Path = Path(__file__).parent.parent.parent

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


# グローバル設定インスタンス
settings = Settings()
