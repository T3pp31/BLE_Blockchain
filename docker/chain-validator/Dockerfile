FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY docker/chain-validator/validate_entry.py ./validate_entry.py

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "validate_entry.py"]
