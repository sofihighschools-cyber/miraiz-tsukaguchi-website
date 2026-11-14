# フリースクール MIRAIZ 阪急塚口校 公式サイト

SOFI株式会社が2026年9月に開校するフリースクール「MIRAIZ（ミライズ）阪急塚口校」の公式ホームページです。

ビルド不要の静的サイト（HTML / CSS / JavaScript のみ）。`index.html` をそのままサーバーに置けば公開できます。

```
miraiz-website/
├── index.html                        … 1ページ完結のサイト本体
├── news.html                         … note・PR TIMES連携のお知らせ一覧
├── data/news.json                    … 自動取得したお知らせデータ
├── scripts/update-news.py            … 公式RSSの取得・整形スクリプト
├── .github/workflows/update-news.yml … 6時間ごとの自動更新
├── assets/
│   ├── css/style.css                 … スタイル（MIRAIZロゴから採色したカラーパレット）
│   ├── js/main.js                    … ドロワー、スクロール演出、フォーム送信
│   └── img/                          … 画像一式（提供PDFから抽出・Web用に最適化）
├── robots.txt                        … 開校前は検索エンジンをブロック（公開時に削除）
├── .nojekyll                         … GitHub Pages で Jekyll 処理を無効化
└── README.md
```

## 掲載内容の出典

| 内容 | 出典 |
| --- | --- |
| キャッチコピー、コンテンツ、マイプロ、参加方法、1日の流れ、8つの特長 | `MIRIZ提案資料.pdf`（Canvaスライド10枚） |
| 「認められる環境で〜」本文、MIRAIZでできること、悩みチェックリスト | チラシ表面 `plusinnovation_miraizomote2026.pdf` |
| 料金、探究型学習、学び直し、安心サポート、I/N学院 | チラシ裏面 `plusinnovation_miraizura2026.pdf` |
| 開校月（2026年9月）、料金、対象年齢、2部制の時間 | Googleドキュメント「MIRAIZ フリースクール」 |
| 写真・ロゴ | 上記PDFに埋め込まれていた画像を抽出し、Web用に再圧縮 |

## 公開前に差し替えが必要な箇所

1. **電話番号・FAX**（`index.html` 内 5か所 / `main.js` 1か所）
   現在は公式チラシ記載の**株式会社プラスイノベーション本部窓口**（TEL 06-6415-6977 / FAX 06-6415-6978）を初期値にしています。
   SOFI株式会社の窓口が決まり次第、差し替えてください。
   - `<head>` の JSON-LD `telephone`
   - ヘッダーのナビ内ボタン
   - お問い合わせセクション（`.contact__tel` と `.contact__direct-note`）
   - フッター
   - 固定CTAバー
   - `assets/js/main.js` のフォーム送信失敗時メッセージ

2. ~~**公開ドメインとOGP URL**~~ → **設定済み**
   正式ドメイン `https://miraiz.sofi-school.com/` を canonical、OGP、JSON-LD、サイトマップに反映済みです。

3. ~~**校舎の詳細住所**~~ → **確定済み**
   〒661-0012 兵庫県尼崎市南塚口町1丁目12-8
   お問い合わせ欄・アクセス欄・フッター・JSON-LDの `address` に反映済みです。

4. **開校日と開校時間**
   - 開校月は **2026年9月**（Googleドキュメントの記載）で作成しています。
     チラシには「2026年8月1日（土）阪急塚口校 開校」とあり、記載が食い違っています。正しい日付をご確認ください。
   - 開校時間は **1部 10:00〜12:00（小学生）／ 2部 13:00〜15:00（中学生）** としています。
     提案資料の「ご相談箇所」では 10:00〜13:00／13:00〜17:00 案、A・Bコース案も併記されていたため、
     サイト上は「※開校時間・クラス編成は予定です」と注記しています。確定後に注記を削除してください。

5. ~~**お問い合わせフォームの送信先**~~ → **設定済み**（`miraiz.tsukaguchi.info@gmail.com`／下記参照）

## お問い合わせフォームの設定

現在は、送信ボタンを押すと**入力内容を差し込んだメール作成画面が開く**フォールバック動作です。
宛先は `assets/js/main.js` 冒頭の定数で設定しています。

```js
const FALLBACK_MAIL_TO = 'miraiz.tsukaguchi.info@gmail.com';
```

この方式は送信者のメールソフトが立ち上がるため、**スマホやWebメール環境では送信が完了しないことがあります**。
確実に受信したい場合は、下記のフォームサービス連携をおすすめします。

サーバーやフォームサービス（Formspree、Google Apps Script など）に POST したい場合は、
`index.html` のフォームタグに送信先URLを設定します。設定すると自動的に `fetch` での非同期送信に切り替わります。

```html
<form class="contact__form" id="contact-form" data-endpoint="https://…" novalidate>
```

`FormData` として、`name` / `role` / `grade` / `tel` / `email` / `purpose`（複数）/ `message` / `agree` が送信されます。

## 公開方法

静的ファイルのみなので、置くだけで動きます。

## お知らせの自動連携

記事取得後に `python3 scripts/render-news.py` を実行し、トップの最新3件とお知らせ一覧をHTMLにも反映します。JavaScriptを実行しないクローラーや通信失敗時にも記事へのリンクを提供します。更新ワークフローはJSON・両HTMLを同一コミットとして保存し、Xserverへ自動反映します。公開記事を削除する際はRSS取得後に再生成して掲載状態を確認してください。

## SEOの運用

- 正式URLは `/`、`/news`、`/hyogo-freeschool-guide`。Xserverでは旧 `.html` URLと末尾スラッシュを301転送します。
- Search Consoleで `https://miraiz.sofi-school.com/` の所有権を確認後、`sitemap.xml` を送信し、3つの正規URLの登録状況を確認してください。サイトマップの設置だけでは登録状況は確認できません。
- 「フリースクール 塚口」「MIRAIZ塚口」「フリースクール おすすめ 兵庫」の表示回数・クリック数・平均掲載順位を記録し、28日単位で比較します。順位やリッチリザルトの表示は保証されません。一般の教育施設ではFAQ構造化データを追加してもGoogleのFAQリッチリザルト表示は通常期待できません。
- Googleビジネスプロフィールでは正式名称・住所・実際の連絡先・営業時間を揃え、教室写真と公式URLを登録してください。現在の電話番号は既存掲載の本部窓口です。校舎専用番号がある場合はサイトとプロフィールを同時に更新します。
- 実在する連携先や地域の公的一覧への掲載を検討してください。被リンクの購入や架空の口コミ・順位表示は行いません。
- ガイドの更新時には見える更新日、Articleの日付、サイトマップの日付を実際の変更日に合わせます。保護者が判断に使う費用、通学日、出席扱いは最新の一次情報で確認します。

### 記事更新の実行

`news.html` は、MIRAIZ塚口のnote公式RSSとSOFI株式会社のPR TIMES公式RSSから取得した記事を、日付順にまとめて表示します。

- GitHub Actionsが6時間ごとに `scripts/update-news.py` を実行
- 更新がある場合だけ `data/news.json`・生成済みの両HTMLをコミット
- RSS取得に一時的に失敗した場合は、前回取得済みの記事を保持
- GitHubの「Actions」→「お知らせ自動更新」→「Run workflow」から手動更新も可能

ローカルで更新する場合：

```bash
python3 scripts/update-news.py
python3 scripts/render-news.py
```

- **Xserver**：`index.html`、`news.html`、`hyogo-freeschool-guide.html`、`data/`、`assets/`、`robots.txt`、`sitemap.xml`、`.htaccess` を `/sofi-school.com/public_html/miraiz.sofi-school.com/` へアップロード
- **Netlify / Vercel / Cloudflare Pages**：このディレクトリを公開ディレクトリに指定（ビルドコマンドなし）
- **GitHub Pages**：下記の通り、`main` ブランチから直接公開されます

ローカルで確認する場合：

```bash
python3 -m http.server 8000
# → http://localhost:8000
```

### GitHub Pages で関係者に共有する

この一式を**公開リポジトリのルート**に置いて `main` へ push し、
リポジトリの **Settings → Pages → Source** で「Deploy from a branch」を選び、
`main` / `/ (root)` を指定して Save すると、
`https://<ユーザー名>.github.io/<リポジトリ名>/` で公開されます。

以降は `main` に push するだけで自動的に反映されます（1〜2分）。

GitHub Actions を使う方法もありますが、Pages機能の初回有効化にはリポジトリ管理者の権限が必要で、
アプリ連携経由のpushでは `Resource not accessible by integration` で失敗します。
静的サイトならブランチ公開のほうが構成がシンプルなので、こちらを採用しています。

**注意：業務ファイルが入っているプライベートリポジトリを公開設定に変えないでください。**
サイト専用の公開リポジトリを分けて運用してください。

#### 検索エンジン対策

開校済みのため、`robots.txt` は全クローラーの巡回を許可しています。

#### 独自ドメインを使う場合

Xserverではサーバーパネルで独自ドメインを追加し、そのドメインのドキュメントルートへ公開ファイルを配置します。
あわせて `index.html` の `canonical` と JSON-LD の `url` を実ドメインに、OGP画像を絶対URLに変更してください。

## 実装メモ

- **カラー**：MIRAIZロゴの風車（9枚羽）から実際の色を抽出し、CSS変数として定義しています（`--c-red` 〜 `--c-magenta`）。カード類のパステルカラーは提案スライドの配色に合わせています。飛鳥みらい学校のような明るい多色構成を意識しました。
- **フォント**：見出しに丸ゴシックの Zen Maru Gothic、本文に Noto Sans JP（Google Fonts）。読み込めない環境では、ヒラギノ丸ゴ／ヒラギノ角ゴ／メイリオへフォールバックします。
- **レスポンシブ**：1080px以下でグローバルナビをドロワー＋下部固定CTAに、900px以下で1カラム、760px以下でマイプロ例の表をカード表示に切り替えます。
- **アクセシビリティ**：スキップリンク、キーボード操作対応のドロワー（Escで閉じる）、フォームの `aria-invalid` とライブリージョン、`prefers-reduced-motion` でのアニメーション停止に対応。
- **画像**：写真はJPEG、切り抜き人物は透過WebP。ファーストビュー以外は遅延読み込み。全画像で合計約1.1MB。
- **構造化データ**：`School` のJSON-LDを埋め込み済み。

## 今後追加できる素材

- **4コマまんが**：Googleドキュメントに記載がありましたが、データが未提供のため未掲載です。いただければ「MIRAIZとは」の後などに追加できます。
- **教室の写真**：現在の教室写真を掲載しています。新しい写真がそろったら差し替えると、教室の今の雰囲気がより伝わります。
- **在校生・保護者の声、スタッフ紹介（氏名・大学・ひとこと）**：開校後に追加すると信頼感が高まります。現在の大学生スタッフ写真は名前なしで掲載しています。
