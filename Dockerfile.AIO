ARG CONTEXT=prod
ARG PYTHON_IMAGE_VERSION=3.10.17

FROM python:${PYTHON_IMAGE_VERSION}-slim-bookworm as base

ARG PYTHON_IMAGE_VERSION
ARG CONTEXT

WORKDIR /app

## Context-based setup
### Add context value as a helper env variable
ENV ${CONTEXT}=1

### Query based on context value
ENV CONTEXT_INSTALLS=${tests:+"wait-for-it libc-dev"}${prod:+"python3-dev"}${dev:+"libc-dev"}
ENV REQUIREMENTS_FILE=${tests:+"tests"}${prod:+"production"}${dev:+"development"}

## Install

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get install --no-install-recommends -y \
    postgresql-client libpq-dev git gcc ${CONTEXT_INSTALLS}

COPY requirements*.txt ./

RUN pip install -r requirements_${REQUIREMENTS_FILE}.txt

## File copies
COPY scripts/entrypoint.sh .
COPY scripts/service_env.sh scripts/

LABEL org.opencontainers.image.title="OpenSlides Media Service"
LABEL org.opencontainers.image.description="Service for OpenSlides which delivers media files."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-media-service"

## Reset helper env variables
ENV ${CONTEXT}=
ENV CONTEXT_INSTALLS=
ENV REQUIREMENTS_FILE=

## Entrypoint
EXPOSE 9006
ENTRYPOINT ["./entrypoint.sh"]



# Development Image
FROM base as dev

## File Copies
COPY setup.cfg .
COPY scripts/execute-cleanup.sh .

RUN chmod 777 -R .

EXPOSE 9006
CMD exec flask --app src/mediaserver run --host 0.0.0.0 --port 9006 --debug



# Test Image
FROM base as tests

## File Copies
COPY src/* src/
COPY setup.cfg .

RUN chmod 777 -R .

STOPSIGNAL SIGKILL
CMD ["sleep", "inf"]



# Production Image
FROM base as prod

# Add appuser
RUN adduser --system --no-create-home appuser
RUN chown appuser /app/

## File Copies
COPY src/* src/

USER appuser
CMD exec gunicorn -b 0.0.0.0:9006 src.mediaserver:app