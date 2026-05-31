FROM python:3.12-slim

WORKDIR /app

COPY config ./config
COPY blockchain ./blockchain
COPY delete_excess_data.py pandas_d_encode.py ./
COPY docker/chain-validator/validate_entry.py ./validate_entry.py

ENV PYTHONPATH=/app

RUN pip install --no-cache-dir pandas

ENTRYPOINT ["python", "validate_entry.py"]
