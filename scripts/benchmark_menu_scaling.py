"""Compare actual menu operations across Git revisions; no timing mocks.

Run with the Python environment used for the CMS test suite:
    python3 scripts/benchmark_menu_scaling.py --output /tmp/cms-benchmark
"""

import argparse
import gc
import hashlib
import io
import json
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
from types import SimpleNamespace

DEFAULT_REFS = ("e87eef5bb", "e47defe93", "de5f2ec3f")
SIZES = (250, 1000, 4000)
DEEP_SIZES = (100, 400, 800)
DB_SIZES = (100, 400, 1600)
WARMUPS = 2


def measure(prepare, repeats):
    samples = []
    signatures = set()
    for index in range(WARMUPS + repeats):
        run, verify = prepare()
        # Collect fixture cycles before timing; retain normal GC during work.
        gc.collect()
        started = time.perf_counter_ns()
        try:
            result = run()
        except RecursionError:
            return {"samples_ms": [], "signature": None, "error": "RecursionError"}
        elapsed = time.perf_counter_ns() - started
        signature = verify(result)
        signatures.add(hashlib.sha256(repr(signature).encode()).hexdigest())
        if index >= WARMUPS:
            samples.append(elapsed / 1_000_000)
    assert len(signatures) == 1, "Output changed between repetitions"
    return {"samples_ms": samples, "signature": signatures.pop()}


def node_fixture(kind, size):
    from cms.cms_menus import NavExtender, SoftRootCutter
    from cms.models import CMSPlugin
    from cms.utils.plugins import downcast_plugins, get_bound_plugins
    from menus.base import NavigationNode
    from menus.menu_pool import _build_nodes_inner_for_one_menu
    from menus.modifiers import AuthVisibility
    from menus.utils import cut_levels

    def node(index, **kwargs):
        return NavigationNode(str(index), "/", index, **kwargs)

    def verify(result):
        assert [item.id for item in result] == expected
        return [(item.id, [child.id for child in item.children]) for item in result]

    if kind.startswith("plugins_"):
        plugins = [
            CMSPlugin(pk=i, parent_id=i - 1 if i > 1 else None, plugin_type="EmptyPlugin") for i in range(1, size + 1)
        ]
        fn = downcast_plugins if kind == "plugins_downcast" else get_bound_plugins

        def check_plugins(result):
            ids = [item.pk for item in result]
            assert ids == list(range(1, size + 1))
            return ids

        return lambda: list(fn(plugins)), check_plugins

    if kind.startswith("build_"):
        nodes = [node(i, parent_id=i - 1 if i > 1 else None) for i in range(1, size + 1)]
        expected = list(range(1, size + 1))
        inputs = nodes[::-1] if kind == "build_reversed" else nodes
        return lambda: _build_nodes_inner_for_one_menu(inputs, "Menu"), verify

    if kind.startswith("extenders_"):
        pages = [node(i) for i in range(1, size + 1)]
        roots = [node(-i) for i in range(1, size + 1)]
        menus = {}
        for index, (page, root) in enumerate(zip(pages, roots, strict=True)):
            namespace = "Ext" if kind == "extenders_shared" else f"Ext{index}"
            page.namespace = "CMSMenu"
            root.namespace = namespace
            if kind == "extenders_unassigned":
                menus[namespace] = SimpleNamespace(cms_enabled=True)
            else:
                page.attr["navigation_extenders"] = [namespace]
        nodes = pages + roots
        expected = [item.id for item in (pages if kind == "extenders_unassigned" else nodes)]
        modifier = NavExtender(SimpleNamespace(menus=menus))
        return lambda: modifier.modify(None, nodes, None, None, False, False), verify

    root = node(0)
    root.level = 0
    if kind in ("descendants_deep", "cut_deep"):
        parent = root
        spine = []
        for index in range(1, size + 1):
            child = node(index)
            child.level = index
            child.parent = parent
            parent.children = [child]
            spine.append(child)
            parent = child
        leaves = [node(size + i) for i in range(1, size + 1)]
        for child in leaves:
            child.level = size + 1
            child.parent = parent
        parent.children = leaves
        if kind == "cut_deep":
            expected = [child.id for child in leaves]
            return lambda: cut_levels([root], size + 1), verify
        expected = [child.id for child in spine + leaves]
        return root.get_descendants, verify

    children = [node(i) for i in range(1, size + 1)]
    root.children = children[:]
    for child in children:
        child.parent = root
        child.level = 1
    if kind == "descendants_wide":
        expected = [child.id for child in children]
        return root.get_descendants, verify
    if kind == "auth_visibility":
        for child in children[size // 2 :]:
            child.attr["visible_for_anonymous"] = False
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))
        expected = [0, *range(1, size // 2 + 1)]
        return lambda: AuthVisibility(None).modify(request, [root, *children], None, None, False, False), verify

    # A selected root with many sibling soft roots, each owning two descendants.
    branch = node(-1)
    root.children = [branch]
    root.selected = True
    branch.parent = root
    branch.children = children
    descendants = []
    for child in children:
        child.parent = branch
        child.attr["soft_root"] = True
        if kind == "soft_roots_empty":
            continue
        first, second = node(size + child.id), node(2 * size + child.id)
        child.children = [first]
        first.children = [second]
        first.parent, second.parent = child, first
        descendants.extend([first, second])
    nodes = [root, branch, *children, *descendants]
    expected = [0, -1, *range(1, size + 1)]
    return lambda: SoftRootCutter(None).modify(None, nodes, None, None, False, False), verify


def database_fixture(kind, size):
    from django.contrib.auth import get_user_model
    from django.contrib.sites.models import Site
    from django.core.cache import cache
    from django.test import RequestFactory

    from cms.cms_menus import CMSMenu
    from cms.models import ACCESS_PAGE, ACCESS_PAGE_AND_DESCENDANTS, Page, PageContent, PagePermission, PageUrl
    from menus.menu_pool import _build_nodes_inner_for_one_menu

    Page.objects.all().delete()
    cache.clear()
    site = Site.objects.get(pk=1)
    user, _ = get_user_model().objects.get_or_create(username="benchmark-viewer")
    other, _ = get_user_model().objects.get_or_create(username="benchmark-other")
    root = Page.objects.create(path="0001", depth=1, numchild=size, site=site)
    pages = [
        root,
        *Page.objects.bulk_create(
            [Page(path=f"0001{i:04X}", depth=2, numchild=0, site=site, parent=root) for i in range(1, size + 1)]
        ),
    ]
    PageContent.objects.bulk_create(
        [
            PageContent(
                page=page, language="en", title=f"Page {index}", template="nav_playground.html", in_navigation=True
            )
            for index, page in enumerate(pages)
        ]
    )
    PageUrl.objects.bulk_create(
        [
            PageUrl(page=page, site=site, language="en", slug=f"page-{index}", path=f"page-{index}")
            for index, page in enumerate(pages)
        ]
    )
    expected = [page.pk for page in pages]
    if kind == "menu_shared_denied":
        PagePermission.objects.bulk_create(
            [
                PagePermission(page=root, user=other, can_view=True, grant_on=ACCESS_PAGE_AND_DESCENDANTS)
                for _ in range(size)
            ]
        )
        expected = []
    elif kind == "menu_mixed_restrictions":
        restricted = pages[1 + size // 2 :]
        PagePermission.objects.bulk_create(
            [PagePermission(page=page, user=other, can_view=True, grant_on=ACCESS_PAGE) for page in restricted]
        )
        expected = [page.pk for page in pages[: 1 + size // 2]]

    def prepare():
        request = RequestFactory().get("/")
        request.user = get_user_model().objects.get(pk=user.pk)
        request.LANGUAGE_CODE = "en"
        renderer = SimpleNamespace(site=site, request_language="en", menus={})
        menu = CMSMenu(renderer)

        def run():
            # Include fresh ORM evaluation, URL loading, visibility and tree build.
            return _build_nodes_inner_for_one_menu(menu.get_nodes(request), "CMSMenu")

        def verify(result):
            ids = [item.id for item in result]
            assert ids == expected, (kind, ids[:10], expected[:10])
            return [(item.title, item.url, len(item.children)) for item in result]

        return run, verify

    return prepare


def worker(args):
    sys.path.insert(0, str(Path(args.worker).resolve()))
    os.environ["DJANGO_SETTINGS_MODULE"] = "cms.tests.settings"
    os.environ["DATABASE_URL"] = "sqlite://:memory:"
    import django

    django.setup()
    from django.conf import settings
    from django.core.management import call_command
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    settings.DEBUG = False
    assert connection.settings_dict["NAME"] == ":memory:"
    call_command("migrate", run_syncdb=True, verbosity=0)
    operations = (
        "build_ordered",
        "build_reversed",
        "descendants_wide",
        "descendants_deep",
        "cut_deep",
        "auth_visibility",
        "extenders_shared",
        "extenders_distinct",
        "extenders_unassigned",
        "soft_roots_empty",
        "soft_roots_populated",
        "plugins_downcast",
        "plugins_bound",
    )
    results = []
    for kind in operations:
        sizes = DEEP_SIZES if kind.endswith("_deep") else SIZES
        for size in sizes:
            result = measure(lambda kind=kind, size=size: node_fixture(kind, size), args.repeats)
            results.append({"operation": kind, "size": size, **result})
        print(f"  {kind}: complete", flush=True)
    for kind in ("menu_unrestricted", "menu_mixed_restrictions", "menu_shared_denied"):
        for size in DB_SIZES:
            prepare = database_fixture(kind, size)
            result = measure(prepare, args.repeats)
            run, verify = prepare()
            # Query instrumentation is outside all timed samples.
            with CaptureQueriesContext(connection) as queries:
                verify(run())
            results.append({"operation": kind, "size": size, "queries": len(queries), **result})
        print(f"  {kind}: complete", flush=True)
    import cms

    output = {
        "python": sys.version,
        "django": django.get_version(),
        "sqlite": sqlite3.sqlite_version,
        "platform": platform.platform(),
        "cms_path": cms.__file__,
        "gc_enabled": gc.isenabled(),
        "results": results,
    }
    Path(args.output).write_text(json.dumps(output, indent=2) + "\n")


def compare(args):
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[1]
    revisions = [subprocess.check_output(["git", "rev-parse", ref], cwd=repo, text=True).strip() for ref in args.refs]
    manifest = {"revisions": revisions, "rounds": args.rounds, "repeats": args.repeats, "warmups": WARMUPS}
    if args.resume:
        assert json.loads((output / "manifest.json").read_text()) == manifest, "Resume settings differ"
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    combined = {}
    with tempfile.TemporaryDirectory(prefix="cms-benchmark-") as temporary:
        for revision in revisions:
            target = Path(temporary) / revision
            target.mkdir()
            archive = subprocess.check_output(["git", "archive", revision], cwd=repo)
            with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
                contents.extractall(target, filter="data")
        # Rotate order across rounds to reduce ordering and thermal bias.
        for round_index in range(args.rounds):
            order = revisions[round_index % len(revisions) :] + revisions[: round_index % len(revisions)]
            for revision in order:
                print(f"Round {round_index + 1}: {revision[:9]}", flush=True)
                target = Path(temporary) / revision
                destination = output / f"{revision[:9]}-{round_index + 1}.json"
                env = dict(os.environ, PYTHONHASHSEED="0", PYTHONPATH=str(target))
                if not (args.resume and destination.exists()):
                    subprocess.run(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--worker",
                            str(target),
                            "--output",
                            str(destination),
                            "--repeats",
                            str(args.repeats),
                        ],
                        cwd=target,
                        env=env,
                        check=True,
                    )
                data = json.loads(destination.read_text())
                assert Path(data["cms_path"]).parent.parent.name == revision, "Imported wrong checkout"
                for result in data["results"]:
                    key = (result["operation"], result["size"])
                    record = combined.setdefault(key, {}).setdefault(
                        revision,
                        {
                            "samples_ms": [],
                            "signature": result["signature"],
                            "queries": result.get("queries"),
                            "error": result.get("error"),
                        },
                    )
                    assert record["signature"] == result["signature"]
                    record["samples_ms"].extend(result["samples_ms"])
    lines = [
        "| Operation | N | " + " | ".join(ref[:9] + " ms" for ref in revisions) + " | Speedup |",
        "|---|---:|" + "---:|" * (len(revisions) + 1),
    ]
    for (operation, size), versions in combined.items():
        signatures = {record["signature"] for record in versions.values() if not record["error"]}
        assert len(signatures) == 1, (operation, size)
        medians = [
            statistics.median(versions[revision]["samples_ms"]) if versions[revision]["samples_ms"] else None
            for revision in revisions
        ]
        speedup = f"{medians[0] / medians[-1]:.2f}x" if medians[0] and medians[-1] else "n/a"
        lines.append(
            f"| {operation} | {size} | "
            + " | ".join(f"{value:.3f}" if value is not None else "RecursionError" for value in medians)
            + f" | {speedup} |"
        )
    (output / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refs", nargs="+", default=DEFAULT_REFS)
    parser.add_argument("--output", required=True)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--worker")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return
    compare(args)


if __name__ == "__main__":
    main()
