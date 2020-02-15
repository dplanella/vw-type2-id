# Pull official base image
FROM python:3.6-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
# Do not buffer stdout and stderr output.
# Required to see logs for containers in detached mode
# See https://stackoverflow.com/q/29663459
ENV PYTHONUNBUFFERED 1
ENV PROJECT=vw_type2_id
ENV CONTAINER_HOME=/opt
ENV CONTAINER_PROJECT=$CONTAINER_HOME/$PROJECT

# Set working directory
WORKDIR ${CONTAINER_PROJECT}
COPY ./docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Install build dependencies
# using the image's package manager
RUN apk --no-cache add --virtual .build-dependencies \
    build-base \
    jpeg-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    zlib-dev

# Install app dependencies
# using pipenv
RUN pip install --upgrade pip \
    pipenv \
    gunicorn

# Copy the app's source code to the project location
# within the container
COPY . ${CONTAINER_PROJECT}

# Install local dependencies
#RUN pipenv install --skip-lock --system --dev
RUN pipenv install --system --deploy --ignore-pipfile
