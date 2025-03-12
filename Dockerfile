FROM python:3.11-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ddw ./ddw
ENV PYTHONPATH=.
CMD [ "python", "ddw/app.py" ]
