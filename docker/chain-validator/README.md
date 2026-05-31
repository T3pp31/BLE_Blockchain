# Chain validator (Docker)

Validate a chain export JSON produced by `main.py` / `ble-blockchain` or `ble_blockchain.blockchain.aggregator`.

## Build

```bash
docker build -t ble-chain-validator -f docker/chain-validator/Dockerfile .
```

## Run

```bash
docker run --rm -v "$(pwd)/data:/data" ble-chain-validator /data/chains/canonical.json
```

Exit code `0` means the chain passed `validate_chain()`.
