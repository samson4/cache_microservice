import io
import json
import unittest

import httpx
from pydantic import ValidationError

from app.cli import CliSettings, PAYLOAD_ENDPOINT, load_input, run


REQUEST_BODY = {
    "list_1": ["first string"],
    "list_2": ["other string"],
}


class CliTests(unittest.TestCase):
    def test_parses_short_options_and_inline_json(self) -> None:
        settings = CliSettings(
            _cli_parse_args=[
                "-H",
                "http://localhost:9000",
                "-r",
                "2",
                "-j",
                json.dumps(REQUEST_BODY),
            ]
        )

        payload = load_input(settings, io.StringIO())

        self.assertEqual(settings.host.host, "localhost")
        self.assertEqual(settings.repeat, 2)
        self.assertEqual(payload.model_dump(), REQUEST_BODY)

    def test_rejects_conflicting_input_options(self) -> None:
        with self.assertRaises(ValidationError):
            CliSettings(
                _cli_parse_args=[
                    "-i",
                    "payload.json",
                    "-j",
                    json.dumps(REQUEST_BODY),
                ]
            )

    def test_rejects_invalid_payload_before_request(self) -> None:
        settings = CliSettings(
            _cli_parse_args=[
                "-j",
                '{"list_1":["one"],"list_2":[]}',
            ]
        )

        with self.assertRaises(ValidationError):
            load_input(settings, io.StringIO())

    def test_repeat_creates_and_reads_payload(self) -> None:
        payload_id = "794ea65f-938d-4f04-84bc-f22245ef3780"
        requests: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append((request.method, request.url.path))
            if request.method == "POST":
                self.assertEqual(json.loads(request.content), REQUEST_BODY)
                return httpx.Response(200, json={"id": payload_id})
            return httpx.Response(
                200,
                json={"output": "FIRST STRING, OTHER STRING"},
            )

        settings = CliSettings(_cli_parse_args=["-r", "2"])
        payload = load_input(settings, io.StringIO(json.dumps(REQUEST_BODY)))
        output = io.StringIO()

        with httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="http://test",
        ) as client:
            run(settings, payload, client, output)

        records = [
            json.loads(line)
            for line in output.getvalue().splitlines()
        ]
        self.assertEqual([record["iteration"] for record in records], [1, 2])
        self.assertEqual({record["id"] for record in records}, {payload_id})
        self.assertTrue(
            all(
                record["output"] == "FIRST STRING, OTHER STRING"
                for record in records
            )
        )
        self.assertEqual(
            requests,
            [
                ("POST", PAYLOAD_ENDPOINT),
                ("GET", f"{PAYLOAD_ENDPOINT}/{payload_id}"),
                ("POST", PAYLOAD_ENDPOINT),
                ("GET", f"{PAYLOAD_ENDPOINT}/{payload_id}"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
