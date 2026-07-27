FROM python:3.11-slim

WORKDIR /worker

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        autodock-vina \
        openbabel \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY run_docking.py .

CMD ["python", "run_docking.py"]