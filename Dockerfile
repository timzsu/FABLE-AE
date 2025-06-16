FROM fable:1.0

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        wget python3-matplotlib python3-scienceplots python3-numpy python3-pandas python3-tabulate \
    && apt-get clean