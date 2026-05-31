# Sphinx ドキュメント

このディレクトリには API リファレンス（autodoc）と概要ガイドが含まれます。

## 前提

プロジェクトのセットアップ手順はリポジトリルートの [README.md](../README.md) を参照してください。

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

- `ble.l2cap_*` や `send_and_receive` は PyBlueZ（`bluetooth`）に依存します。開発マシンが Linux でない場合、該当ページは import 警告になることがあります（Raspberry Pi 上でのビルドを推奨）。
- `install_package` はモジュール import 時に `apt-get` を実行するため、ドキュメントビルド環境によっては autodoc が失敗することがあります。セットアップ手順はルート README を参照してください。

## 構成

- `guides/overview.rst` — プロジェクト概要（日本語）
- `api/` — モジュール API リファレンス（autodoc）
- `diagrams/` — アーキテクチャ図（drawio）
