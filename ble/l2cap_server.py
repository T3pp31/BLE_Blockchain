import bluetooth


def l2cap_server():
    """
    BLE経由で情報を受け取る.
    l2cap_client.pyで送信されてくるデータを受信することができる.

    Parameters
    ----------

    Return
    ----------

    Notes


    """
    server_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
    server_sock.bind(("", 0x1001))
    server_sock.listen(1)

    while True:
        print("送信されてくるデータを待ってます")
        client_sock, address = server_sock.accept()
        print(f"接続を確認{str(address)}")

        print("データを受信中")

        total = 0
        total_data = ""
        while True:
            try:
                data = client_sock.recv(1024)
            except bluetooth.BluetoothError as e:
                break

            if len(data) == 0:
                break

            total += len(data)

            print(f"total byte read:{total}")
            print(f"data is: {data}")

        client_sock.close()

        print(f"データを受信しました:{data}")
        print("connection closed")

        data = [s.decode() for s in data]

        return data

    server_sock.close()


def l2cap_server_main(receive_data_list, len_of_device):
    count = 0
    while True:
        data = l2cap_server()
        receive_data_list.append(data)
        count = count + 1
        if count == len_of_device:
            break
