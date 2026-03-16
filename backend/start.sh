#!/bin/bash
# Download RNIC file if not present
if [ ! -f /app/data/rnic.csv ] && [ ! -f data/rnic.csv ]; then
    echo "Downloading RNIC data (437 MB)..."
    mkdir -p data
    curl -L -o data/rnic.csv "https://static.data.gouv.fr/resources/registre-national-dimmatriculation-des-coproprietes/20260105-114009/rnc-data-gouv-with-qpv.csv"
    echo "RNIC download complete."
fi

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
