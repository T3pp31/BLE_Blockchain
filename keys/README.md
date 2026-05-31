# Device signing keys

`keys/` 配下の PEM（秘密鍵・公開鍵ファイル）は Git に含めません。各環境で次を実行して生成してください。

```bash
uv run python scripts/generate_device_keys.py
```

This creates `device1`–`device4` key pairs and updates `settings1.json`–`settings4.json` with `public_key_pem` and `peer_public_keys`.

Copy each `keys/deviceN_private.pem` to the matching Raspberry Pi. Keep the same `settingsN.json` on that Pi.
