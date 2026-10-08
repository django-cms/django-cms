"""Measure CMS HTTP response latency over loopback TCP across Git snapshots.

python3 scripts/benchmark_menu_http.py --output /tmp/cms-http-benchmark
"""

import argparse
import hashlib
import http.client
import io
import json
import math
import os
import platform
import sqlite3
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode
from wsgiref.simple_server import WSGIRequestHandler, make_server

from benchmark_menu_scaling import DEFAULT_REFS, database_fixture

SIZES = (400, 1600)
WORKLOADS = ("menu_unrestricted", "menu_mixed_restrictions", "menu_shared_denied")
CACHE_MODES = ("uncached", "cached")
WARMUPS = 2
TEMPLATE_NAME = "benchmark_http.html"
PAGE_PATH = "/en/benchmark/"
SETUP_PATH = "/__benchmark_setup"
QUERY_HEADER = "HTTP_X_BENCHMARK_QUERIES"


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        # Request logging would add unrelated I/O to every timed request.
        pass


def setup_fixture(params):
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.contrib.sites.models import Site
    from django.test import Client

    from cms.models import Page, PageContent, PageUrl

    kind = params["workload"][0]
    size = int(params["size"][0])
    mode = params["mode"][0]
    assert kind in WORKLOADS and mode in CACHE_MODES and size in SIZES
    settings.CMS_CACHE_DURATIONS = {"menus": 0 if mode == "uncached" else 3600, "content": 3600, "permissions": 3600}
    database_fixture(kind, size)
    # The requested landing page stays accessible even when the other tree is denied.
    site = Site.objects.get(pk=1)
    landing = Page.objects.create(path="0002", depth=1, numchild=0, site=site)
    PageContent.objects.create(page=landing, language="en", title="Benchmark landing", template=TEMPLATE_NAME)
    PageUrl.objects.create(page=landing, site=site, language="en", slug="benchmark", path="benchmark")
    PageContent.objects.update(template=TEMPLATE_NAME)
    client = Client()
    client.force_login(get_user_model().objects.get(username="benchmark-viewer"))
    expected = {"menu_unrestricted": size + 2, "menu_mixed_restrictions": size // 2 + 2, "menu_shared_denied": 1}
    return {
        "cookie": f"{settings.SESSION_COOKIE_NAME}={client.cookies[settings.SESSION_COOKIE_NAME].value}",
        "expected_links": expected[kind],
        "page_count": size + 2,
    }


def serve(args):
    sys.path.insert(0, str(Path(args.server).resolve()))
    os.environ["DJANGO_SETTINGS_MODULE"] = "cms.tests.settings"
    os.environ["DATABASE_URL"] = "sqlite://:memory:"
    from django.conf import settings

    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    settings.CMS_PAGE_CACHE = False
    # Keep the real middleware chain, except whole-response caching.
    settings.MIDDLEWARE = [entry for entry in settings.MIDDLEWARE if not entry.startswith("django.middleware.cache.")]
    settings.TEMPLATES[0]["DIRS"].insert(0, args.templates)
    settings.CMS_TEMPLATES = [(TEMPLATE_NAME, "HTTP benchmark")]
    import django

    django.setup()
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    assert connection.settings_dict["NAME"] == ":memory:"
    call_command("migrate", run_syncdb=True, verbosity=0)
    application = get_wsgi_application()

    def dispatch(environ, start_response):
        if environ["PATH_INFO"] == SETUP_PATH:
            payload = setup_fixture(parse_qs(environ.get("QUERY_STRING", "")))
            start_response("200 OK", [("Content-Type", "application/json")])
            return [json.dumps(payload).encode()]
        if QUERY_HEADER not in environ:
            return application(environ, start_response)

        # Collect SQL only for separate, untimed verification requests.
        headers = []
        status = []

        def capture_response(value, values, exc_info=None):
            status.append(value)
            headers.extend(values)

        with CaptureQueriesContext(connection) as queries:
            response = application(environ, capture_response)
            try:
                body = list(response)
            finally:
                response.close()
        headers.append(("X-Benchmark-Queries", str(len(queries))))
        start_response(status[0], headers)
        return body

    with make_server("127.0.0.1", 0, dispatch, handler_class=QuietHandler) as server:
        import cms

        print(
            json.dumps(
                {
                    "port": server.server_port,
                    "python": sys.version,
                    "django": django.get_version(),
                    "sqlite": sqlite3.sqlite_version,
                    "platform": platform.platform(),
                    "cms_path": cms.__file__,
                }
            ),
            flush=True,
        )
        server.serve_forever()


def request(port, path, headers):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=120)
    try:
        started = time.perf_counter_ns()
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        first_headers = time.perf_counter_ns()
        body = response.read()
        finished = time.perf_counter_ns()
        assert response.status == 200, (response.status, body[:1000])
        return {
            "total_ms": (finished - started) / 1_000_000,
            "headers_ms": (first_headers - started) / 1_000_000,
            "body": body,
            "queries": response.getheader("X-Benchmark-Queries"),
        }
    finally:
        connection.close()


def check_response(result, expected):
    body = result["body"]
    assert b"user=benchmark-viewer" in body, "Request was not authenticated"
    assert body.count(b"<a ") == expected, (body.count(b"<a "), expected)
    return hashlib.sha256(body).hexdigest()


def run_cases(port, repeats):
    records = []
    for workload in WORKLOADS:
        for size in SIZES:
            for mode in CACHE_MODES:
                params = urlencode({"workload": workload, "size": size, "mode": mode})
                fixture = json.loads(request(port, f"{SETUP_PATH}?{params}", {})["body"])
                headers = {"Cookie": fixture["cookie"]}
                samples = []
                signatures = set()
                for index in range(WARMUPS + repeats):
                    result = request(port, PAGE_PATH, headers)
                    signatures.add(check_response(result, fixture["expected_links"]))
                    if index >= WARMUPS:
                        samples.append({key: result[key] for key in ("total_ms", "headers_ms")})
                assert len(signatures) == 1
                result = request(port, PAGE_PATH, {**headers, "X-Benchmark-Queries": "1"})
                assert check_response(result, fixture["expected_links"]) in signatures
                records.append(
                    {
                        "workload": workload,
                        "size": size,
                        "mode": mode,
                        "page_count": fixture["page_count"],
                        "links": fixture["expected_links"],
                        "signature": signatures.pop(),
                        "response_bytes": len(result["body"]),
                        "queries": int(result["queries"]),
                        "samples": samples,
                    }
                )
                print(
                    f"  {workload}, N={size}, {mode}: {statistics.median(s['total_ms'] for s in samples):.2f} ms",
                    flush=True,
                )
    return records


def summarize(output, revisions):
    grouped = {}
    for revision in revisions:
        for path in sorted(output.glob(f"{revision[:9]}-*.json")):
            for result in json.loads(path.read_text())["results"]:
                key = (result["workload"], result["size"], result["mode"])
                group = grouped.setdefault(key, {}).setdefault(revision, {**result, "samples": []})
                assert group["signature"] == result["signature"]
                assert group["queries"] == result["queries"]
                group["samples"].extend(result["samples"])
    lines = [
        "| Workload | Pages | Menu cache | "
        + " | ".join(ref[:9] + " median / p95 ms" for ref in revisions)
        + " | Speedup |",
        "|---|---:|---|" + "---:|" * (len(revisions) + 1),
    ]
    stats = []
    for (workload, size, mode), versions in grouped.items():
        assert len({item["signature"] for item in versions.values()}) == 1, (workload, size, mode)
        cells = []
        medians = []
        for revision in revisions:
            group = versions[revision]
            values = sorted(sample["total_ms"] for sample in group["samples"])
            median = statistics.median(values)
            p95 = values[math.ceil(0.95 * len(values)) - 1]
            group["median_ms"], group["p95_ms"] = median, p95
            medians.append(median)
            cells.append(f"{median:.2f} / {p95:.2f}")
        lines.append(
            f"| {workload} | {size + 2} | {mode} | " + " | ".join(cells) + f" | {medians[0] / medians[-1]:.2f}x |"
        )
        stats.append({"workload": workload, "size": size, "mode": mode, "revisions": versions})
    (output / "summary.md").write_text("\n".join(lines) + "\n")
    (output / "statistics.json").write_text(json.dumps(stats, indent=2) + "\n")
    print("\n".join(lines), flush=True)


def compare(args):
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[1]
    revisions = [subprocess.check_output(["git", "rev-parse", ref], cwd=repo, text=True).strip() for ref in args.refs]
    manifest = {"revisions": revisions, "rounds": args.rounds, "repeats": args.repeats, "warmups": WARMUPS}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with tempfile.TemporaryDirectory(prefix="cms-http-benchmark-") as temporary:
        templates = Path(temporary) / "templates"
        templates.mkdir()
        (templates / TEMPLATE_NAME).write_text(
            "{% load menu_tags %}<!doctype html><html><body><h1>CMS HTTP benchmark</h1>"
            "<p>user={{ request.user.username }}</p><ul>"
            '{% show_menu 0 100 100 100 "menu/menu.html" "CMSMenu" %}</ul></body></html>'
        )
        for revision in revisions:
            target = Path(temporary) / revision
            target.mkdir()
            archive = subprocess.check_output(["git", "archive", revision], cwd=repo)
            with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
                contents.extractall(target, filter="data")
        for round_index in range(args.rounds):
            order = revisions[round_index % len(revisions) :] + revisions[: round_index % len(revisions)]
            for revision in order:
                print(f"Round {round_index + 1}: {revision[:9]}", flush=True)
                target = Path(temporary) / revision
                log_path = output / f"{revision[:9]}-{round_index + 1}.log"
                with log_path.open("w") as log:
                    process = subprocess.Popen(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--server",
                            str(target),
                            "--templates",
                            str(templates),
                        ],
                        cwd=target,
                        env=dict(os.environ, PYTHONHASHSEED="0", PYTHONPATH=str(target)),
                        stdout=subprocess.PIPE,
                        stderr=log,
                        text=True,
                    )
                    try:
                        ready = process.stdout.readline()
                        assert ready, f"Server failed; see {log_path}"
                        metadata = json.loads(ready)
                        assert Path(metadata["cms_path"]).parent.parent.name == revision
                        results = run_cases(metadata["port"], args.repeats)
                        destination = output / f"{revision[:9]}-{round_index + 1}.json"
                        destination.write_text(json.dumps({**metadata, "results": results}, indent=2) + "\n")
                    finally:
                        process.terminate()
                        process.wait(timeout=10)
    summarize(output, revisions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--refs", nargs="+", default=DEFAULT_REFS)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--server")
    parser.add_argument("--templates")
    args = parser.parse_args()
    if args.server:
        serve(args)
        return
    if not args.output:
        parser.error("--output is required")
    compare(args)


if __name__ == "__main__":
    main()
