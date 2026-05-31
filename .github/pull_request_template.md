<!-- あくまでテンプレートなので必ずしもすべての項目を埋めなくてもよい -->

## 背景

<!-- 背景を明記してください（issue 番号、卒論・実験の文脈など） -->


## 変更内容

<!-- 何を・なぜ変えたか（1〜3 行で要約） -->


## 要件

<!-- 具体的な要件を書いてください（正常時 / エラー時 / どういう挙動かなど） -->


## スクリーンショット

<!-- UI やログ、draw.io の差分など、説明に必要なら貼ってください -->


## 影響範囲

<!-- 例: src/ble_blockchain/, config/*.json, settingsN.json, Pi 起動手順, Docker 検証 -->

| 領域 | 影響 |
|------|------|
| `src/ble_blockchain/` | |
| `config/`（JSON） | |
| `settings*.json` / `keys/*.pem` | |
| `tests/` | |
| `docs/` / `docs/diagrams/` | |
| Raspberry Pi デプロイ | |


## 不安点

<!-- 実装上、自信がないところや不安なところなどがあれば明記してください -->


## セルフチェックリスト

### 共通

* [ ] コミットの単位を適宜 rebase / squash で適切な大きさにまとめていること
* [ ] コミットメッセージに変更内容と理由が書かれていること
* [ ] 不要なコードは削除していること（コメントアウトだけ残さない）
* [ ] 適切にエラーハンドリングされていること（ファイル読込・型変換で落ちない）
* [ ] クラス名・メソッド名・定数名は意図が分かる名前であること

### 本リポジトリ（BLE_Blockchain）

* [ ] `uv sync --group dev` のうえで **`uv run pytest`** が通ること
* [ ] 設定値をソースに直書きしていないこと（`config/*.json` または環境変数）
* [ ] **`keys/*.pem` や `.env` をコミットしていない**こと
* [ ] 公開 API（`ble_blockchain.*` の import、CLI、`settingsN.json` のキー）を変えた場合、**README** と必要なら **docs/**（Sphinx RST）を更新したこと
* [ ] アーキテクチャ・モジュール構成を変えた場合、**`docs/diagrams/ble-blockchain-architecture.drawio`** を更新したこと
* [ ] Pi 向け手順（`ble-blockchain` / `main.py` / `scripts/`）に影響がある場合、README の実行例を更新したこと
* [ ] L2CAP / PyBlueZ まわりを触った場合、Linux（Pi）での動作確認またはテストで代替していること

### 任意

* [ ] `uv run pylint`（CI と同様）をローカルで確認したこと
* [ ] `uv sync --group docs` → `cd docs && make html` で Sphinx がビルドできること
