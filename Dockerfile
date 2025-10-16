ARG CONTEXT=prod

FROM python:3.10.19-slim-bookworm AS base

## Setup
ARG CONTEXT
WORKDIR /app
ENV APP_CONTEXT=${CONTEXT}

## Install
RUN CONTEXT_INSTALLS=$(case "$APP_CONTEXT" in \
    tests)  echo "wait-for-it libc-dev";; \
    dev)    echo "libc-dev";; \
    *)      echo "python3-dev" ;; esac) && \
    apt-get -y update && apt-get -y upgrade && apt-get install --no-install-recommends -y \
    gcc \
    git \
    libpq-dev \
    postgresql-client \
    ${CONTEXT_INSTALLS} && \
    rm -rf /var/lib/apt/lists/*

COPY requirements*.txt ./

RUN REQUIREMENTS_FILE=$(case "$APP_CONTEXT" in \
    tests) echo "tests";; \
    dev)   echo "development";; \
    *)     echo "production" ;; esac) && \
    pip install --no-cache-dir -r "requirements_${REQUIREMENTS_FILE}.txt"

## File copies
COPY scripts/entrypoint.sh .
COPY scripts/service_env.sh scripts/

## External Information
LABEL org.opencontainers.image.title="OpenSlides Media Service"
LABEL org.opencontainers.image.description="Service for OpenSlides which delivers media files."
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/OpenSlides/openslides-media-service"

## Command
ENTRYPOINT ["./entrypoint.sh"]
COPY ./dev/command.sh ./
RUN chmod +x command.sh
CMD ["./command.sh"]

# Development Image
FROM base AS dev

## File Copies
COPY setup.cfg .
COPY scripts/execute-cleanup.sh .

EXPOSE 9006

# Test Image
FROM base AS tests

## File Copies
COPY src/* src/
COPY setup.cfg .

## Command
STOPSIGNAL SIGKILL
CMD ["sleep", "inf"]

# Production Image
FROM base AS prod

# Add appuser
RUN adduser --system --no-create-home appuser && \
    chown appuser /app/

## File Copies
COPY src/* src/
EXPOSE 9006

USER appuser
