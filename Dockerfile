# pull official base image
FROM python:3.9-bullseye

# set work directory
WORKDIR /code

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apt update && apt install -y python3-dev
RUN pip install --upgrade pip
COPY ./requirements.txt /code/
RUN pip install -r requirements.txt

# copy project
COPY . /code/

RUN ["chmod", "+x", "/code/run.sh"]

WORKDIR /code/

EXPOSE 8000