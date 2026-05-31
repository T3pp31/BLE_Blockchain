import subprocess


def start_discoverable():
    """
    raspberrypiのbleではセキュリティの観点からか，ble検索にかからないようになっているので，定期的に以下のコマンドを実行する必要がある.
    つまりサーバーとして情報を受け取るためには以下のコマンドを毎回行う必要があるので，サーバを起動するときに以下のコマンドを自動的に実行するように変更する必要がある．

    以下コマンドを，サーバ起動前に実行する必要があるので，関数化する．
    $ bluetoothctl
    $ discoverable on


    """
    subprocess.run(["sudo", "bluetoothctl", "discoverable", "on"])
