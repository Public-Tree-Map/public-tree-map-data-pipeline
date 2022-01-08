
# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8.2-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN apt-get update -y \
    && apt-get install -y build-essential curl

RUN pip3 install --no-cache-dir -r requirements.txt

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 etl_http_listener:app