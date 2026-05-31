import subprocess


# 必要なパッケージの一括インストール
def install_package():
    """
    必要なパッケージの一括インストール

    Parameters
    ----------

    Return
    ----------

    """
    subprocess.run(["sudo", "apt-get", "install", "libatlas-base-dev"])
    subprocess.run(["sudo", "apt-get", "install", "libjasper-dev"])
    subprocess.run(
        ["sudo", "apt-get", "install", "bluetooth", "libbluetooth-dev"]
    )
    subprocess.run(["pip", "install", "-r", "requirements.txt"])


install_package()
