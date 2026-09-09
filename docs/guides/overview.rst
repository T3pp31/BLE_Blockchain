プロジェクト概要
================

本リポジトリは、BLE（Bluetooth Low Energy）通信とブロックチェーンを組み合わせた
卒業研究用システムです。Raspberry Pi 複数台が BLE スキャン結果を暗号化・署名して
L2CAP で交換し、過半数合意でブロックチェーンを構築します。

ペイロード交換は Transport 抽象層（``src/ble_blockchain/transport.py``）を介して
行います。``config/transport.json`` の ``mode`` で **BLE 方式**（既定）と **file 方式**
を切り替えられ、file 方式では Bluetooth を使わず共有 inbox ディレクトリと
スキャン結果 CSV で交換するため、BLE 非対応環境（macOS 等）でも同一パイプラインが
動きます。

リポジトリレイアウト
--------------------

アプリケーション本体は ``src/ble_blockchain`` パッケージにあります。
実行時に参照する JSON 設定はリポジトリルートの ``config/``、端末別設定は
``settings1.json`` 〜 ``settings4.json`` です。

.. code-block:: text

   BLE_Blockchain/
   ├── main.py                 # 後方互換ラッパー
   ├── config/                 # JSON 設定（transport.json 等）
   ├── settings1.json …        # 端末別設定
   ├── src/ble_blockchain/
   │   ├── app/main.py         # パイプライン
   │   ├── transport.py        # Transport 抽象層（ble / file 切替）
   │   ├── transport_file.py   # file 方式（共有 inbox）
   │   ├── ble/
   │   ├── blockchain/
   │   ├── cipher/
   │   ├── config/             # loader, device_settings
   │   └── pipeline/
   ├── tests/
   └── docs/

エントリポイント
----------------

- **推奨**: ``uv run ble-blockchain --settings settings1.json``
- **後方互換**: ``uv run python main.py --settings settings1.json``

利用者向けドキュメント
----------------------

セットアップ、実行方法、処理フロー、設定の詳細はリポジトリルートの README を参照してください。

- `README.md <../README.md>`_

アーキテクチャ図
----------------

システム構成の図は次のファイルにあります。

- ``diagrams/ble-blockchain-architecture.drawio``

API リファレンス
----------------

Python モジュールの API は本 Sphinx サイトの :doc:`../api/index` セクション（autodoc）を参照してください。
モジュール名は ``ble_blockchain.<subpackage>.<module>`` 形式です。
