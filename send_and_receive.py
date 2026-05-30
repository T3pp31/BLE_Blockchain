import json
import threading
from concurrent.futures import ThreadPoolExecutor

from ble.l2cap_client import l2cap_client


def toTwo(bt_addrs, send_data_list):
    client_thread = threading.Thread(
        target=l2cap_client(bt_addrs[0], send_data_list)
    )


def toThree(bt_addrs, send_data_list):
    client_thread = threading.Thread(
        target=l2cap_client(bt_addrs[1], send_data_list)
    )


def toFour(bt_addrs, send_data_list):
    client_thread = threading.Thread(
        target=l2cap_client(bt_addrs[2], send_data_list)
    )


def SEND(bt_addrs, send_data_list):
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(toTwo(bt_addrs, send_data_list))
        executor.submit(toThree(bt_addrs, send_data_list))
        executor.submit(toFour(bt_addrs, send_data_list))


if __name__ == "__main__":
    with open("settings1.json", "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)

    bt_addrs = [
        value for key, value in json_data.items() if key != "profile"
    ]
    send_data = "ewqkormwqim"

    SEND(bt_addrs, send_data)
