FROM python:3.11-slim

WORKDIR /worker

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L \
    https://github.com/rdk/p2rank/releases/download/2.5.1/p2rank_2.5.1.tar.gz \
    -o /tmp/p2rank.tar.gz \
    && mkdir -p /opt/p2rank \
    && tar -xzf /tmp/p2rank.tar.gz -C /opt/p2rank --strip-components=1 \
    && rm /tmp/p2rank.tar.gz

ENV P2RANK_HOME=/opt/p2rank
ENV PATH="/opt/p2rank:${PATH}"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY run_p2rank.py .

CMD ["python", "run_p2rank.py"]