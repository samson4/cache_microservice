# Payload Cache Service

A FastAPI microservice that transforms and interleaves two equally sized lists of
strings. Individual transformation results are cached in SQLite, and identical
payload requests reuse the same identifier.

The supplied transformer converts each string to uppercase. This behavior is based
on the example output in the task specification and is isolated in a transformer
method so it can be replaced later.

## Features

- FastAPI endpoints for creating and retrieving generated payloads.
- Persistent transformation caching with SQLAlchemy and SQLite.
- Payload identifier reuse for identical requests.
- Alembic database migrations.
- A Pydantic Settings-based command-line client.
- Docker Compose development workflow.
- Unit tests for the service and CLI.

## Requirements

The container workflow requires:

- Docker
- Docker Compose
- Make

For local Python commands, install Python 3.13 and
[uv](https://docs.astral.sh/uv/).

## Configuration

Create the local environment file:

```bash
cp .env.example .env
```

The application expects these settings:

```dotenv
DATABASE_URL=sqlite:///./data/payload_cache.db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_BUSY_TIMEOUT=5
API_PORT=8000
```

`API_PORT` controls both the Uvicorn listening port and the host port published by
Docker Compose. The SQLite database is stored in a named Docker volume mounted at
`/app/data`, so normal container restarts and `make down` preserve cached data.

## Docker workflow

Show the available commands:

```bash
make help
```

Build and start the API in the background:

```bash
make run
```

Follow the application logs:

```bash
make logs
```

With the example configuration, the service is available at:

- API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- OpenAPI document: `http://127.0.0.1:8000/openapi.json`

The health endpoint executes a lightweight database query. It returns HTTP `200`
with `{"status":"ok"}` when the database responds and HTTP `503` when the database
is unavailable.

Stop the containers without removing them:

```bash
make stop
```

Stop and remove the containers and network while preserving cached data:

```bash
make down
```

Remove containers, networks, images, and the persistent database volume:

```bash
make clean
```

`make clean` permanently deletes the containerized SQLite database and its cached
results.

## API usage

Create a payload:

```bash
curl -X POST http://127.0.0.1:8000/payload \
  -H 'Content-Type: application/json' \
  -d '{
    "list_1": ["first string", "second string"],
    "list_2": ["other string", "another string"]
  }'
```

Example response:

```json
{
  "id": "89ebc229-d5fa-414c-961f-6b812c915fcc"
}
```

Retrieve the generated payload:

```bash
curl http://127.0.0.1:8000/payload/89ebc229-d5fa-414c-961f-6b812c915fcc
```

```json
{
  "output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING"
}
```

Submitting the same ordered lists again returns the same identifier. Strings already
present in the transformation cache are reused instead of being transformed again.

### Concurrent requests

For SQLite, payload creation starts with `BEGIN IMMEDIATE` before checking either
cache. This ensures that simultaneous requests cannot transform the same missing
string twice: the second writer waits, then reads the results committed by the first.
If the writer lock cannot be obtained within `DATABASE_BUSY_TIMEOUT`, the API returns
HTTP `503` with `Retry-After: 1`.

This deliberately serializes payload creation, including requests for unrelated
strings. It is a small and predictable tradeoff for this single-host SQLite service;
a higher-throughput distributed version would need different coordination.

## CLI usage

The installed command supports:

```text
cache-cli [-H|--host URL] [-r|--repeat N]
          [-i|--input FILE|-] [-j|--json JSON]
          [-o|--output FILE|-] [-h|--help]
```

The specification assigns `-h` to both host and help. This implementation reserves
`-h` for help and uses `-H` for host. The default host uses `API_PORT` from `.env`.

Start the API with `make run`, then run the CLI locally:

```bash
uv run cache-cli \
  --json '{"list_1":["hello"],"list_2":["world"]}'
```

Or run the installed CLI inside the API container:

```bash
docker compose exec api cache-cli \
  --json '{"list_1":["hello"],"list_2":["world"]}'
```

Test payload reuse over three iterations:

```bash
uv run cache-cli --repeat 3 \
  --json '{"list_1":["hello"],"list_2":["world"]}'
```

Each iteration writes one JSON line. Repeated requests should show the same `id`:

```json
{"iteration": 1, "id": "<uuid>", "output": "HELLO, WORLD"}
{"iteration": 2, "id": "<uuid>", "output": "HELLO, WORLD"}
{"iteration": 3, "id": "<uuid>", "output": "HELLO, WORLD"}
```

Read input from a file:

```bash
uv run cache-cli --input payload.json
```

Read input from standard input:

```bash
printf '%s' '{"list_1":["hello"],"list_2":["world"]}' \
  | uv run cache-cli --input -
```

Write newline-delimited JSON to a file:

```bash
uv run cache-cli --repeat 3 --input payload.json --output results.jsonl
```

Override the server URL when necessary:

```bash
uv run cache-cli -H http://127.0.0.1:9000 --input payload.json
```

Display CLI help:

```bash
uv run cache-cli --help
```

## Tests

Build the dedicated test stage and run all tests in its isolated container:

```bash
make test
```

Run them locally:

```bash
uv run python -m unittest discover -s tests -v
```

Check linting and formatting locally:

```bash
make lint
```

Apply Ruff's safe lint fixes and formatter:

```bash
make format
```

GitHub Actions runs the formatting check, linter, and full test suite on every push
and pull request.

The tests cover the FastAPI create/read endpoints, transformation and interleaving,
full and partial cache hits, payload identifier reuse, validation, missing payloads,
empty and Unicode input, CLI parsing, file/stdin input, and repeated CLI requests.
The test stage is separate from the final runtime stage, so test files are not shipped
in the production image.

## Project structure

```text
app/
  cache/          API schemas, models, routes, and service logic
  core/           Configuration and database setup
  cli.py          Command-line client
alembic/          Database migrations
data/             Local SQLite data directory
docker/           Container image definition
tests/            Service and CLI unit tests
docker-compose.yml
Makefile
```
