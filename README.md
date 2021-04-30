# openslides-media-service
Media service for OpenSlides 3+

Delivers media files for OpenSlides. To check permissions, a check-request is
issed to the main OpenSlides worker.

## Configuration
All Configvariables can be provided within a `config.py` or via environment
variables. Configs without default must be specified. All configs (see
`config.py.tpl` as a template):

- `URL_PREFIX`: Default `/media/`. The prefix, the server listens to. E.g. for
  the default, all files must be requested this way: `/media/<path>`.
- `CHECK_REQUEST_URL`: The url to make the chack request to. The host and port
  must be given. E.g.: `worker:8000/check-media/`
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`:
  The host, port, database name, user and password for the mediafile db
- `BLOCK_SIZE`: Default 4096. The size of the blocks, the file is chunked into.
  4096 seems to be a good default (inspired by Django).
- `CACHE_SIZE`: Default 10. The size of the LRU cache for the mediafiledata db.
  Note that regarding if a file is cached a check-request is always done.
- `CACHE_DATA_MIN_SIZE_KB` and `CACHE_DATA_MAX_SIZE_KB`: Default 0 and 10240 (10M).
  The size for mediafiles to match to be cached. Too small or too large files
  are not cached.

## Production setup:
Use the provided Dockerfile. It creates the table in Postgresql, if it doesn't
exist before startup.

## Development:
For the first setup, create a python venv and install dependencies:

    $ python3 -m venv .venv
    $ source .venv/bin/activate
    $ pip install -r requirements.txt

To start the flask development server, activate the virtual environment and run
the `dev.sh` script.

To prepare the database (maybe clear it first: `dropdb mediafiledata && createdb mediafiledata`), execute the following command:

    psql -1 -h <host> -U <user> -d <database> -vt=<table> -f src/schema.sql

# Configure the main OpenSlides worker:
Add a special database to the `DATABASES` configuration:

    DATABASES['mediafiles'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '<databasename>',
        'USER': '<user>',
        'PASSWORD': '<pw>',
        'HOST': '<host>',
        'PORT': '<port>',
    }

The name `mediafiles` must not be altered.
  

## TODOs:
 - support different ports than 5432 in dockerfile
 - Development in docker
 - Tests
 - Name confusion: media-server vs media-service. Be constant here and name it
   media-service!

