# クイックスタートガイド

楽天市場・Nint連携型番商品リサーチ自動化ツールの使い方を簡潔に説明します。

## 1. セットアップ(初回のみ)

```bash
# プロジェクトディレクトリに移動
cd rakuten-nint-analyzer

# Python依存関係をインストール
pip install -e .

# Playwright Browsersをインストール
playwright install chromium

# 環境変数を設定
cp .env.example .env
```

`.env`ファイルを編集してNint認証情報を設定:

```env
NINT_LOGIN_EMAIL=あなたのメールアドレス@example.com
NINT_LOGIN_PASSWORD=あなたのパスワード
```

## 2. Webダッシュボードを起動

```bash
# FastAPIサーバー起動
python -m python_src.web.api
```

起動後、ブラウザで以下にアクセス:

**http://localhost:8000**

## 3. 商品を分析

Webダッシュボードで以下を入力:

1. **キーワード/JANコード**: 例: `iPhone 15 Pro`
2. **仕入価格**: 例: `50000`
3. **目標販売価格**: 空欄(自動算出) または 例: `65000`
4. **取得件数**: 20件(デフォルト)

「🔍 分析開始」ボタンをクリック。

## 4. 結果を確認

数秒〜数十秒で以下が表示されます:

### 判定結果
- **GO**: 参入推奨
- **Conditional**: 条件付き推奨
- **No-Go**: 参入非推奨

### 総合スコア
- 価格競争力、市場機会、競争度など6つの指標
- 0-100点でスコア化

### 利益分析
- 粗利率、推定月間利益、損益分岐点

### 楽天商品一覧
- 上位商品の価格・ポイント・店舗情報

---

## よくある質問

### Q1. Nint認証に失敗する

**A**: 以下を確認してください:
1. `.env`ファイルのメールアドレス・パスワードが正しいか
2. Nintのログインページ構造が変更されていないか
   - `python_src/scrapers/nint_scraper.py`のセレクタを調整

### Q2. 楽天市場の商品が取得できない

**A**: 以下を確認してください:
1. インターネット接続が正常か
2. 楽天市場のHTML構造が変更されていないか
   - `python_src/scrapers/rakuten_scraper.py`のセレクタを調整

### Q3. サムネイル品質スコアが0になる

**A**: 画像URLが取得できていない可能性があります。
- `python_src/scrapers/rakuten_scraper.py`の画像セレクタを確認

### Q4. 推奨価格を手動で設定したい

**A**: Webフォームの「目標販売価格」欄に金額を入力してください。空欄の場合は自動算出されます。

---

## トラブルシューティング

### エラー: "command not found: playwright"

```bash
# Playwrightを再インストール
pip install playwright
playwright install chromium
```

### エラー: "ModuleNotFoundError: No module named 'python_src'"

```bash
# カレントディレクトリがプロジェクトルートか確認
pwd
# /Users/あなたの名前/rakuten-nint-analyzer であるべき

# プロジェクトを開発モードでインストール
pip install -e .
```

### エラー: "pydantic_settings" not found

```bash
# pydantic-settingsをインストール
pip install pydantic-settings
```

---

## 次のステップ

- [README.md](README.md): 詳細なドキュメント
- [CLAUDE.md](CLAUDE.md): Miyabi AIエージェントによる自動開発
- [GitHub Issues](https://github.com/pokko001/rakuten-nint-analyzer/issues): バグ報告・機能要望

---

**開発者**: Miyabi Framework + Claude Code
**ライセンス**: MIT
