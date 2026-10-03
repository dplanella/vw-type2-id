# Pull official base image
FROM python:3.8-alpine

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

# Install client libraries
RUN apk update && apk add --virtual .run-deps \
    libpq \
    gettext \
    postgresql-client

# Install build dependencies
# using the image's package manager
RUN apk --no-cache add --virtual .build-deps \
    build-base \
    gettext-dev \
    jpeg-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    postgresql-dev \
    zlib-dev

# Copy the app's source code to the project location
# within the container
COPY . ${CONTAINER_PROJECT}

# Install local dependencies
RUN pip install --no-cache-dir -r requirements.txt

#RUN apk del .build-deps