FROM python:3.8-slim

ARG INSTALL_DEEPPURPOSE=false

WORKDIR /worker

COPY requirements.txt .
COPY requirements-deeppurpose.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN if [ "$INSTALL_DEEPPURPOSE" = "true" ]; then \
      apt-get update && \
      apt-get install -y --no-install-recommends build-essential git && \
      pip install --no-cache-dir -r requirements-deeppurpose.txt && \
      apt-get clean && \
      rm -rf /var/lib/apt/lists/*; \
    fi

COPY run_inference.py .
COPY scorers ./scorers

ENTRYPOINT ["python", "run_inference.py"]