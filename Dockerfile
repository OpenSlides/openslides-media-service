ARG CONTEXT=prod

FROM python:3.10.18-slim-bookworm as base

## Setup
ARG CONTEXT
WORKDIR /app
# Used for easy target differentiation
ARG ${CONTEXT}=1 
ENV APP_CONTEXT=${CONTEXT}

### Context based queries
ARG CONTEXT_INSTALLS=${tests:+"wait-for-it libc-dev"}${prod:+"python3-dev"}${dev:+"libc-dev"}
ARG REQUIREMENTS_FILE=${tests:+"tests"}${prod:+"production"}${dev:+"development"}

## Install

RUN apt-get -y update && apt-get -y upgrade && apt-get install --no-install-recommends -y \
    gcc \
    git \
    libpq-dev \
    postgresql-client \
    ${CONTEXT_INSTALLS} && \
    rm -rf /var/lib/apt/lists/*

COPY requirements*.txt ./

RUN pip install --no-cache-dir -r requirements_${REQUIREMENTS_FILE}.txt

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
FROM base as dev

## File Copies
COPY setup.cfg .
COPY scripts/execute-cleanup.sh .

EXPOSE 9006



# Test Image
FROM base as tests

## File Copies
COPY src/* src/
COPY setup.cfg .


## Command
STOPSIGNAL SIGKILL
CMD ["sleep", "inf"]



# Production Image
FROM base as prod

# Add appuser
RUN adduser --system --no-create-home appuser && \
    chown appuser /app/

## File Copies
COPY src/* src/
EXPOSE 9006

USER appuser