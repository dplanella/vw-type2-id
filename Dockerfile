# Pull official base image
FROM python:3.7.4-alpine

# Set working directory
WORKDIR /usr/src/vw_type2_id

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build dependencies
# using the image's package manager
RUN apk --no-cache add --virtual build-dependencies \
                build-base \
                python3-dev \
                libxml2-dev \
                libxslt-dev \
                jpeg-dev \
                zlib-dev

# Install app dependencies
# using pipenv
RUN pip install --upgrade pip
RUN pip install pipenv
COPY ./Pipfile /usr/src/vw_type2_id/Pipfile
RUN pipenv install --skip-lock --system --dev

# copy project
COPY . /usr/src/vw_type2_id/
