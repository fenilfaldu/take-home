FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

RUN pip3 install --no-cache-dir --break-system-packages \
    jupyter \
    nbconvert \
    nbformat \
    ipykernel \
    pandas \
    matplotlib \
    seaborn \
    numpy

WORKDIR /repo

COPY data/ /repo/data/
