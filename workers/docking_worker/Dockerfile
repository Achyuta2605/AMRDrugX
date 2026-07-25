FROM gnina/gnina:latest

WORKDIR /worker

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY run_docking.py .

ENTRYPOINT ["python3", "run_docking.py"]