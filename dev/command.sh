#!/bin/sh

if [ ! -z $dev   ]; then exec flask --app src/mediaserver run --host 0.0.0.0 --port 9006 --debug; fi
if [ ! -z $tests ]; then sleep inf; fi
if [ ! -z $prod  ]; then exec gunicorn -b 0.0.0.0:9006 src.mediaserver:app; fi