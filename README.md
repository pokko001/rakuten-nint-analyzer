# rakuten-nint-analyzer

**楽天市場・Nint連携型番商品リサーチ自動化ツール**

卸業者からの商品リストを基に、楽天市場とNintからデータを収集し、仕入れ判断を自動化・半自動化するPython製Webアプリケーション。

Autonomous development powered by **Miyabi** - AI-driven development framework.

---

## 主な機能

### 1. 楽天市場データ収集
- キーワード/JANコード検索
- 上位N件の商品情報自動取得
- 価格・ポイント・送料・クーポン情報
- サムネイル画像品質評価(解像度・文字量・背景処理)

### 2. Nint市場分析
- 推定月販数・売上推移
- 価格推移・変動係数
- 上位店舗シェア分析
- 成長率計算

### 3. 総合スコアリング
以下の指標を統合し、0-100点でスコア化:
- **価格競争力** (25%)
- **市場機会** (30%)
- **競争度** (15%)
- **サムネイル品質** (15%)
- **利益性** (10%)
- **リスク** (5%)

### 4. 仕入れ判定
スコアと粗利率から自動判定:
- **GO**: 参入推奨 (スコア≥75、粗利率≥20%)
- **Conditional**: 条件付き推奨 (スコア≥60、粗利率≥15%)
- **No-Go**: 参入非推奨

### 5. Webダッシュボード
FastAPI + TailwindCSS + Alpine.jsによる直感的なUI

---

## Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** (Miyabiフレームワーク用)
- **Nint アカウント** (市場分析用)

### Installation

```bash
# 1. リポジトリをクローン
git clone https://github.com/pokko001/rakuten-nint-analyzer.git
cd rakuten-nint-analyzer

# 2. Node.js依存関係をインストール (Miyabi用)
npm install

# 3. Python依存関係をインストール (uv推奨)
pip install -e .

# 4. Playwright Browsersをインストール
playwright install chromium

# 5. 環境変数を設定
cp .env.example .env
# .envを編集してNint認証情報などを設定
```

### Configuration

`.env`ファイルを編集:

```env
# Nint認証情報 (必須)
NINT_LOGIN_EMAIL=your_email@example.com
NINT_LOGIN_PASSWORD=your_password

# 楽天API (任意 - 公式API使用時)
RAKUTEN_APP_ID=your_app_id
RAKUTEN_AFFILIATE_ID=your_affiliate_id

# Webダッシュボード
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8000
DEBUG=true
```

### Running the Application

```bash
# Webダッシュボード起動
python -m python_src.web.api

# ブラウザで開く
# http://localhost:8000
```

---

## Project Structure

```
rakuten-nint-analyzer/
├── python_src/              # Pythonソースコード
│   ├── scrapers/           # スクレイパー
│   │   ├── rakuten_scraper.py   # 楽天市場
│   │   └── nint_scraper.py      # Nint (Playwright)
│   ├── analyzers/          # 分析エンジン
│   │   ├── thumbnail_analyzer.py  # サムネイル品質
│   │   ├── price_analyzer.py      # 価格競争力
│   │   ├── market_analyzer.py     # 市場分析
│   │   └── profit_calculator.py   # 利益計算
│   ├── scoring/            # スコアリング
│   │   ├── scorer.py              # 総合スコア
│   │   └── recommendation.py      # GO/Conditional/No-Go判定
│   ├── web/                # Webアプリケーション
│   │   ├── api.py                 # FastAPI
│   │   └── templates/index.html   # ダッシュボードUI
│   └── utils/              # ユーティリティ
│       └── config.py              # 設定管理
├── data/                   # データディレクトリ
│   ├── input/             # 仕入先Excelファイル
│   └── output/            # レポート出力
├── src/                    # TypeScript (Miyabi)
│   └── index.ts
├── .claude/                # AI agent configuration
├── .github/workflows/      # CI/CD automation
├── pyproject.toml          # Python依存管理
├── package.json            # Node.js依存管理
└── README.md
```

## Miyabi Framework

This project uses **7 autonomous AI agents**:

1. **CoordinatorAgent** - Task planning & orchestration
2. **IssueAgent** - Automatic issue analysis & labeling
3. **CodeGenAgent** - AI-powered code generation
4. **ReviewAgent** - Code quality validation (80+ score)
5. **PRAgent** - Automatic PR creation
6. **DeploymentAgent** - CI/CD deployment automation
7. **TestAgent** - Test execution & coverage

### Workflow

1. **Create Issue**: Describe what you want to build
2. **Agents Work**: AI agents analyze, implement, test
3. **Review PR**: Check generated pull request
4. **Merge**: Automatic deployment

### Label System

Issues transition through states automatically:

- `📥 state:pending` - Waiting for agent assignment
- `🔍 state:analyzing` - Being analyzed
- `🏗️ state:implementing` - Code being written
- `👀 state:reviewing` - Under review
- `✅ state:done` - Completed & merged

## Commands

```bash
# Check project status
npx miyabi status

# Watch for changes (real-time)
npx miyabi status --watch

# Create new issue
gh issue create --title "Add feature" --body "Description"
```

## Configuration

### Environment Variables

Required variables (see `.env.example`):

- `GITHUB_TOKEN` - GitHub personal access token
- `ANTHROPIC_API_KEY` - Claude API key (optional for local development)
- `REPOSITORY` - Format: `owner/repo`

### GitHub Actions

Workflows are pre-configured in `.github/workflows/`:

- CI/CD pipeline
- Automated testing
- Deployment automation
- Agent execution triggers

**Note**: Set repository secrets at:
`https://github.com/pokko001/rakuten-nint-analyzer/settings/secrets/actions`

Required secrets:
- `GITHUB_TOKEN` (auto-provided by GitHub Actions)
- `ANTHROPIC_API_KEY` (add manually for agent execution)

## Documentation

- **Miyabi Framework**: https://github.com/ShunsukeHayashi/Miyabi
- **NPM Package**: https://www.npmjs.com/package/miyabi
- **Label System**: See `.github/labels.yml`
- **Agent Operations**: See `CLAUDE.md`

## Support

- **Issues**: https://github.com/ShunsukeHayashi/Miyabi/issues
- **Discord**: [Coming soon]

## License

MIT

---

✨ Generated by [Miyabi](https://github.com/ShunsukeHayashi/Miyabi)
