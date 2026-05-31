プロジェクト概要
================

本リポジトリは、BLE（Bluetooth Low Energy）通信とブロックチェーンを組み合わせた
卒業研究用システムです。Raspberry Pi 複数台が BLE スキャン結果を暗号化・署名して
L2CAP で交換し、過半数合意でブロックチェーンを構築します。

リポジトリレイアウト
--------------------

アプリケーション本体は ``src/ble_blockchain`` パッケージにあります。
実行時に参照する JSON 設定はリポジトリルートの ``config/``、端末別設定は
``settings1.json`` 〜 ``settings4.json`` です。

.. code-block:: text

   BLE_Blockchain/
   ├── main.py                 # 後方互換ラッパー
   ├── config/                 # JSON 設定
   ├── settings1.json …
   ├── src/ble_blockchain/
   │   ├── app/main.py         # パイプライン
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
