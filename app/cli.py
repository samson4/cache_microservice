import json
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Annotated, Self, TextIO

import httpx
from pydantic import AliasChoices, Field, HttpUrl, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError

from app.cache.schemas import CacheCreateResponse, CacheInput, CacheRead
from app.core.config import settings as app_settings


PAYLOAD_ENDPOINT = "/payload"


def default_host() -> HttpUrl:
    return HttpUrl(f"http://127.0.0.1:{app_settings.API_PORT}")


class CliSettings(BaseSettings):
    """Options for creating and reading payloads through the cache API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CACHE_CLI_",
        extra="ignore",
        cli_parse_args=True,
        cli_exit_on_error=False,
        cli_prog_name="cache-cli",
        cli_hide_none_type=True,
        populate_by_name=True,
        case_sensitive=True,
    )

    host: HttpUrl = Field(
        default_factory=default_host,
        validation_alias=AliasChoices("host", "H"),
        description="Server URL. Use -H because -h is reserved for help.",
    )
    repeat: Annotated[int, Field(gt=0)] = Field(
        default=1,
        validation_alias=AliasChoices("repeat", "r"),
        description="Number of POST and GET iterations.",
    )
    input_file: str | None = Field(
        default=None,
        validation_alias=AliasChoices("input", "i"),
        description="UTF-8 JSON file, or - for stdin.",
    )
    json_input: str | None = Field(
        default=None,
        validation_alias=AliasChoices("json", "j"),
        description="Inline JSON; mutually exclusive with --input.",
    )
    output_file: str = Field(
        default="-",
        validation_alias=AliasChoices("output", "o"),
        description="Output file, or - for stdout.",
    )

    @model_validator(mode="after")
    def validate_options(self) -> Self:
        if self.input_file is not None and self.json_input is not None:
            raise ValueError("--input and --json are mutually exclusive")
        if self.input_file == "" or self.output_file == "":
            raise ValueError("Input and output file names must not be empty")
        if self.host.username or self.host.password or self.host.query or self.host.fragment:
            raise ValueError("--host must not contain credentials, a query, or a fragment")
        if self.host.path not in (None, "/"):
            raise ValueError("--host must not contain a path")
        return self


def load_input(settings: CliSettings, stdin: TextIO) -> CacheInput:
    if settings.json_input is not None:
        raw_input = settings.json_input
    elif settings.input_file in (None, "-"):
        raw_input = stdin.read()
    else:
        raw_input = Path(settings.input_file).read_text(encoding="utf-8-sig")

    return CacheInput.model_validate_json(raw_input.removeprefix("\ufeff"))


def run(
    settings: CliSettings,
    payload: CacheInput,
    client: httpx.Client,
    output: TextIO,
) -> None:
    for iteration in range(1, settings.repeat + 1):
        response = client.post(PAYLOAD_ENDPOINT, json=payload.model_dump())
        response.raise_for_status()
        created = CacheCreateResponse.model_validate(response.json())

        response = client.get(f"{PAYLOAD_ENDPOINT}/{created.id}")
        response.raise_for_status()
        result = CacheRead.model_validate(response.json())

        record = {
            "iteration": iteration,
            "id": created.id,
            "output": result.output,
        }
        output.write(json.dumps(record, ensure_ascii=False) + "\n")
        output.flush()


def main(argv: list[str] | None = None) -> int:
    try:
        settings = CliSettings(
            _cli_parse_args=sys.argv[1:] if argv is None else argv,
        )
        payload = load_input(settings, sys.stdin)
    except (ValidationError, SettingsError, OSError, ValueError) as exc:
        print(f"cache-cli: {exc}", file=sys.stderr)
        return 2

    try:
        with ExitStack() as stack:
            output = (
                sys.stdout
                if settings.output_file == "-"
                else stack.enter_context(
                    Path(settings.output_file).open(
                        "w",
                        encoding="utf-8",
                        newline="\n",
                    )
                )
            )
            client = stack.enter_context(
                httpx.Client(
                    base_url=str(settings.host).rstrip("/"),
                    timeout=30.0,
                )
            )
            run(settings, payload, client, output)
    except (httpx.HTTPError, OSError, ValueError) as exc:
        print(f"cache-cli: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
