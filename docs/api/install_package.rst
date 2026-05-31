install_package（セットアップスクリプト）
=========================================

Raspberry Pi 向けに apt パッケージと ``requirements.txt`` を一括インストールするスクリプトです。
**Python パッケージのモジュールではなく**、リポジトリ直下で次のように実行します。

.. code-block:: bash

   python3 scripts/install_package.py

.. warning::

   このファイルは import 時に ``sudo apt-get`` / ``pip`` を実行するため、
   Sphinx autodoc の対象にはしていません。

実装: ``scripts/install_package.py``
