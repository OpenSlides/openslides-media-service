#!/bin/sh

if [ "$APP_CONTEXT" = "dev"   ]; then exec flask --app src/mediaserver run --host 0.0.0.0 --port 9006 --debug; fi
if [ "$APP_CONTEXT" = "tests" ]; then sleep inf; fi
if [ "$APP_CONTEXT" = "prod"  ]; then exec gunicorn -b 0.0.0.0:9006 src.mediaserver:app; fi