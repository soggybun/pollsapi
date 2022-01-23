FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y python3-dev

WORKDIR /app

COPY ./requirements.txt /app/
RUN pip install -r requirements.txt


COPY . /app/
WORKDIR /code/

EXPOSE 8000




