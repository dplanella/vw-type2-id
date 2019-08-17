# pull official base image
FROM python:3.7.4-alpine

# set work directory
WORKDIR /usr/src/vw_type2_id

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN apk --no-cache add --virtual build-dependencies \
                build-base \
                python3-dev \
                libxml2-dev \
                libxslt-dev \
                jpeg-dev \
                zlib-dev
RUN pip install --upgrade pip
RUN pip install pipenv
COPY ./Pipfile /usr/src/vw_type2_id/Pipfile
RUN pipenv install --skip-lock --system --dev

# copy project
COPY . /usr/src/vw_type2_id/
