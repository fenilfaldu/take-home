FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    pandas==2.2.2 \
    numpy==1.26.4 \
    matplotlib==3.9.2

COPY prepare_data.py .
RUN python3 prepare_data.py && rm prepare_data.py

RUN test -f users.csv && test -f events.csv

CMD ["bash"]