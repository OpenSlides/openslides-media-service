# openslides-media-service
Media service for OpenSlides 4

Delivers media files for OpenSlides.

## Configuration
See `config_handling.py`:
```
"MEDIA_DATABASE_HOST",
"MEDIA_DATABASE_PORT",
"MEDIA_DATABASE_NAME",
"MEDIA_DATABASE_USER",
"MEDIA_DATABASE_PASSWORD",
"BLOCK_SIZE",
"PRESENTER_HOST",
"PRESENTER_PORT",
```
all config must be set.

## Production setup:
TODO

## Development:
We use docker to run the code.

The command `make run-tests` runs the tests.
The command `make run-cleanup` runs the code cleanup (black, isort, flake8).

