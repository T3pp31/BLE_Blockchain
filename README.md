# 日本語
# 初めに
本レポジトリは卒論に向けた開発を行うためのものである．

# システムの概要
BLEとBlockchainを組み合わせたシステムを構築する．
Raspberrypiは4台程度用意し，相互通信をBLEを用いて実現する．
RaspberrypiをBLEビーコンとし，スマートフォンやノートパソコンのBLEブロードキャストをキャッチする．キャッチした情報をAESで暗号化し，BLE経由でデバイス間で共有する．共有されたデータをブロックにのせ，以前のハッシュ値と見比べることでチェーンを作成する．

# blockchain
blockchainフォルダでは，ブロックとチェーンを作成し，情報を載せるためのブロックチェーンを実装する．

ブロックチェーンをテストするためのDockerを作成している途中である．


# ble

Raspberrypi同士の通信ではl2cap_client.pyとl2cap_server.pyを利用する．
discover.pyでbleブロードキャストをキャッチする．

raspberrypiのbleではセキュリティの観点からか，ble検索にかからないようになっているので，定期的に以下のコマンドを実行する必要がある.
つまりサーバーとして情報を受け取るためには以下のコマンドを毎回行う必要があるので，サーバを起動するときに以下のコマンドを自動的に実行するように変更する必要がある．
```
$ bluetoothctl
$ discoverable on
```

# main
bluetoothでの同時送受信が困難になるのなら，ラウンドロビン方式（1が送ってる時は他のデバイスは送らない）を取る必要がある

# セットアップ

## 環境構築

### Python 依存関係（uv 推奨）

[uv](https://docs.astral.sh/uv/) を使って仮想環境とパッケージを管理します。

```bash
# uv 未導入の場合（例）
curl -LsSf https://astral.sh/uv/install.sh | sh

cd BLE_Blockchain
uv sync
```

開発用ツール（pylint / pytest）も入れる場合:

```bash
uv sync --group dev
```

### Raspberry Pi 上のシステム依存

BLE（PyBlueZ 等）用の apt パッケージは従来どおり必要です。

```bash
sudo apt-get install git
git clone https://github.com/Fu-Te/BLE_Blockchain
cd BLE_Blockchain
python3 install_package.py   # apt + pip（Pi 向け）
uv sync                      # 上記のあと uv で Python 依存を揃える場合
```

## 使い方

各 Raspberry Pi には端末専用の設定ファイル（`settings1.json`〜`settings4.json`）を用意しています。
設定ファイルには、**自端末以外**の Bluetooth アドレス（3台分）と、送受信フローを表す `profile` キーを記載してください。

| 端末 | 設定ファイル | 旧コマンド（削除済み） |
|------|-------------|----------------------|
| Pi 1 | `settings1.json` | `python3 main.py` / `python3 main1.py` |
| Pi 2 | `settings2.json` | `python3 main2.py` |
| Pi 3 | `settings3.json` | `python3 main3.py` |
| Pi 4 | `settings4.json` | `python3 main4.py` |

実行例:

```bash
uv run python main.py --settings settings1.json
```

`uv` を使わない場合は `python3 main.py --settings settings1.json` でも同様です。

`profile` キーは `config/runtime_profiles.json` の端末別フロー（送受信順序）と対応しています。
送受信のタイミングや sleep 秒数を変更する場合は `config/runtime_profiles.json` を編集してください。



# 処理の流れ
※の部分はまだ開発が終わっていない部分
```
ビーコンのアドレスをjsonから取得
↓
秘密鍵，公開鍵の作成
↓
Discoverable on
↓
bt端末をスキャン
↓
※必要な情報以外を落とす
↓
署名の作成
↓
送信用データの作成
↓
※ラウンドロビン
※データの受信（要検討）
※データの送信（要検討）
↓
署名の検証
↓
※ブロックチェーンへ追加

※データをWeb上で確認できるようにする
or
※csvデータをLAN内から取得できるように
```

# 変数
# 送信するデータの格納用リスト

#　[df, public_key, signature]を格納します
send_data_list = []
例)[[df,public_key,signature],[df1,public_key1,signature1]]
send_data_list[[0][1]]だと，public_keyがでる


# 受け取る情報の格納用リスト
# [[df, public_key, signature],[df, public_key, signature]]のような構成になる．
# 取り出すためにはreceive_data_list[1][0]みたいな感じで使う
receive_data_list = []