# Sphinx ドキュメント

このディレクトリには API リファレンス（autodoc）と概要ガイドが含まれます。

## 前提

プロジェクトのセットアップ・実行・設定はリポジトリルートの [README.md](../README.md) を参照してください。

Python コードは **`src/ble_blockchain`** パッケージにあり、JSON 設定はリポジトリルートの **`config/`** にあります。

## 依存関係のインストール

```bash
# リポジトリルートで
uv sync --group docs
```

または:

```bash
pip install sphinx sphinx-rtd-theme
```

## HTML のビルド

```bash
cd docs
make html
```

`make` が使えない場合:

```bash
cd docs
sphinx-build -b html . _build
```

ビルド成果物は `docs/_build/` に出力されます。このディレクトリは `.gitignore` で除外されています。

## 注意

- autodoc の import パスは `ble_blockchain.*` です（`docs/conf.py` で `../src` を `sys.path` に追加）。
- `ble_blockchain.ble.l2cap_*` や `ble_blockchain.pipeline.send_and_receive` は PyBlueZ（`bluetooth`）に依存します。開発マシンが Linux でない場合、該当ページは import 警告になることがあります（Raspberry Pi 上でのビルドを推奨）。
- **`scripts/install_package.py`** は import 時に `apt-get` / `pip` を実行するため、autodoc 対象にしていません。Pi 向けセットアップ手順はルート README を参照してください。

## 構成

| パス | 内容 |
|------|------|
| `guides/overview.rst` | プロジェクト概要（日本語） |
| `api/` | モジュール API（`ble_blockchain` パッケージ） |
| `diagrams/` | アーキテクチャ図（draw.io） |
