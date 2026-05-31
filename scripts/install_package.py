"""Raspberry Pi 向け依存パッケージの一括インストールスクリプト。"""

import subprocess


def install_package() -> None:
    """Install system and Python dependencies required on Raspberry Pi."""
    subprocess.run(
        ["sudo", "apt-get", "install", "libatlas-base-dev"], check=False
    )
    subprocess.run(
        ["sudo", "apt-get", "install", "libjasper-dev"], check=False
    )
    subprocess.run(
        ["sudo", "apt-get", "install", "bluetooth", "libbluetooth-dev"],
        check=False,
    )
    subprocess.run(
        ["pip", "install", "-r", "requirements.txt"], check=False
    )


install_package()
