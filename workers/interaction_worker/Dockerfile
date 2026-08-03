FROM python:3.10-slim

WORKDIR /worker

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openbabel \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir plip

COPY run_interaction_analysis.py .

CMD ["python", "run_interaction_analysis.py"]