#!/bin/sh

if [ "$APP_CONTEXT" = "dev"   ]; then exec flask --app src/mediaserver run --host 0.0.0.0 --port 9006 --debug; fi
if [ "$APP_CONTEXT" = "tests" ]; then sleep inf; fi
if [ "$APP_CONTEXT" = "prod"  ]; then
  args="-b 0.0.0.0:${MEDIA_PORT:-9006}"
  case "${MEDIA_ENABLE_CONTROL_SOCKET:-no}" in
    '1'|'yes'|'on'|'true') break;;
    *) args="$args --no-control-socket" ; break;;
  esac
  exec gunicorn $args src.mediaserver:app
fi
