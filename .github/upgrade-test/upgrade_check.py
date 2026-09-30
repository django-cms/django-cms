#!/usr/bin/env python
"""
Upgrade smoke test for django CMS.

    python upgrade_check.py populate   # run with the previous release installed
    python upgrade_check.py verify     # run after upgrading and migrating

``populate`` creates users, a small page tree in two languages with text
plugins and page permissions, and stores a snapshot of what it created.
``verify`` checks that the data survived the upgrade, that pages render for
anonymous visitors and editors, that the admin works, and that the upgraded
schema accepts new content and tree operations.
"""

import json
import os
import sys
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "upgradeproject.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import transaction  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from cms import __version__ as cms_version  # noqa: E402
from cms.api import add_plugin, assign_user_to_page, create_page, create_page_content  # noqa: E402
from cms.models import (  # noqa: E402
    CMSPlugin,
    GlobalPagePermission,
    Page,
    PageContent,
    PagePermission,
    Placeholder,
)
from cms.toolbar.utils import get_object_edit_url, get_object_preview_url, get_object_structure_url  # noqa: E402

SNAPSHOT = Path(__file__).resolve().parent / "snapshot.json"
TEMPLATE = "base.html"
LANGUAGES = ("en", "de")
PAGES = (
    # (reverse_id, parent reverse_id, {language: title})
    ("home", None, {"en": "Home", "de": "Startseite"}),
    ("about", "home", {"en": "About", "de": "Über uns"}),
    ("team", "about", {"en": "Team", "de": "Team"}),
    ("contact", None, {"en": "Contact", "de": "Kontakt"}),
    ("members", "home", {"en": "Members", "de": "Mitglieder"}),  # view restricted
)
RESTRICTED = {"members"}

failures = []


def check(condition, message):
    print(("  ok    " if condition else "  FAIL  ") + message)
    if not condition:
        failures.append(message)


def marker(reverse_id, language, index):
    return f"upgrade-marker-{reverse_id}-{language}-{index}"


def get_counts():
    return {
        "users": get_user_model().objects.count(),
        "pages": Page.objects.count(),
        "page_contents": PageContent.admin_manager.count(),
        "placeholders": Placeholder.objects.count(),
        "plugins": CMSPlugin.objects.count(),
        "page_permissions": PagePermission.objects.count(),
        "global_page_permissions": GlobalPagePermission.objects.count(),
    }


def get_content(page, language):
    return PageContent.admin_manager.get(page=page, language=language)


@transaction.atomic
def create_content():
    User = get_user_model()
    User.objects.create_superuser("admin", "admin@example.com", "admin")
    editor = User.objects.create_user("editor", "editor@example.com", "editor", is_staff=True)

    pages = {}
    expected = []
    for reverse_id, parent_id, titles in PAGES:
        page = create_page(
            titles["en"],
            TEMPLATE,
            "en",
            parent=pages.get(parent_id),
            reverse_id=reverse_id,
            in_navigation=True,
            created_by="upgrade-test",
        )
        for language in LANGUAGES[1:]:
            create_page_content(language, titles[language], page, created_by="upgrade-test", in_navigation=True)
        if reverse_id == "home":
            page.set_as_homepage()
        pages[reverse_id] = page

    for reverse_id, page in pages.items():
        page.refresh_from_db()
        for language in LANGUAGES:
            content = get_content(page, language)
            placeholder = content.rescan_placeholders()["content"]
            markers = [marker(reverse_id, language, index) for index in range(3)]
            for text in markers:
                add_plugin(placeholder, "TextPlugin", language, body=f"<p>{text}</p>")
            expected.append(
                {
                    "reverse_id": reverse_id,
                    "language": language,
                    "url": page.get_absolute_url(language),
                    "title": content.title,
                    "markers": markers,
                    "restricted": reverse_id in RESTRICTED,
                }
            )

    # Permissions granting view rights restrict the page for everybody else
    assign_user_to_page(pages["about"], editor, can_add=True, can_change=True, can_delete=True, can_move_page=True)
    assign_user_to_page(pages["members"], editor, can_view=True)
    assign_user_to_page(pages["contact"], editor, can_change=True, global_permission=True)

    return expected


def populate():
    print(f"Populating with django CMS {cms_version}")
    snapshot = {"cms_version": cms_version, "pages": create_content()}

    # Make sure the populated site actually works before upgrading, so that a
    # failure after the upgrade can be attributed to the upgrade.
    check_rendering(snapshot)

    # Count after rendering: the toolbar lazily creates a clipboard per user
    snapshot["counts"] = get_counts()
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


def check_rendering(snapshot):
    anonymous = Client()
    viewer = Client()
    check(viewer.login(username="editor", password="editor"), "editor can log in")
    for entry in snapshot["pages"]:
        response = anonymous.get(entry["url"])
        if entry["restricted"]:
            check(response.status_code != 200, f"anonymous GET {entry['url']} is denied -> {response.status_code}")
            response = viewer.get(entry["url"])
        check(response.status_code == 200, f"GET {entry['url']} -> {response.status_code}")
        body = response.content.decode()
        for text in entry["markers"]:
            check(text in body, f"{entry['url']} contains {text}")

    editor = Client()
    check(editor.login(username="admin", password="admin"), "superuser can log in")
    for entry in snapshot["pages"]:
        content = get_content(Page.objects.get(reverse_id=entry["reverse_id"]), entry["language"])
        for label, url in (
            ("edit", get_object_edit_url(content)),
            ("preview", get_object_preview_url(content)),
            ("structure", get_object_structure_url(content)),
        ):
            response = editor.get(url)
            check(response.status_code == 200, f"{label} GET {url} -> {response.status_code}")
            if label != "structure":
                check(entry["markers"][0] in response.content.decode(), f"{label} {url} contains page content")

    for url in (
        reverse("admin:index"),
        reverse("admin:cms_pagecontent_changelist") + "?language=en",
        reverse("admin:cms_pagecontent_get_tree") + "?language=en",
        reverse("admin:cms_pagecontent_get_tree") + "?language=de",
        reverse("admin:auth_user_changelist"),
        reverse("admin:cms_globalpagepermission_changelist"),
    ):
        response = editor.get(url)
        check(response.status_code == 200, f"admin GET {url} -> {response.status_code}")
    for entry in snapshot["pages"]:
        if entry["language"] == "en":
            content = get_content(Page.objects.get(reverse_id=entry["reverse_id"]), "en")
            url = reverse("admin:cms_pagecontent_change", args=(content.pk,))
            response = editor.get(url)
            check(response.status_code == 200, f"admin GET {url} -> {response.status_code}")


@transaction.atomic
def write_after_upgrade():
    parent = Page.objects.get(reverse_id="about")
    page = create_page("After upgrade", TEMPLATE, "en", parent=parent, reverse_id="after-upgrade", in_navigation=True)
    create_page_content("de", "Nach dem Upgrade", page, in_navigation=True)
    for language in LANGUAGES:
        placeholder = get_content(page, language).rescan_placeholders()["content"]
        add_plugin(placeholder, "TextPlugin", language, body=f"<p>{marker('after-upgrade', language, 0)}</p>")
    page.move_page(Page.objects.get(reverse_id="contact"), position="first-child")
    page.refresh_from_db()
    check(page.parent == Page.objects.get(reverse_id="contact"), "new page moved below contact page")
    return page


def verify():
    print(f"Verifying with django CMS {cms_version}")
    snapshot = json.loads(SNAPSHOT.read_text())
    print(f"Snapshot was taken with django CMS {snapshot['cms_version']}")
    check(snapshot["cms_version"] != cms_version, f"version changed ({snapshot['cms_version']} -> {cms_version})")

    counts = get_counts()
    for key, value in snapshot["counts"].items():
        check(counts[key] == value, f"{key}: {value} before, {counts[key]} after")

    for entry in snapshot["pages"]:
        page = Page.objects.get(reverse_id=entry["reverse_id"])
        check(
            page.get_absolute_url(entry["language"]) == entry["url"],
            f"url of {entry['reverse_id']}/{entry['language']} is still {entry['url']}",
        )
        check(
            get_content(page, entry["language"]).title == entry["title"],
            f"title of {entry['reverse_id']}/{entry['language']} is still {entry['title']}",
        )
    check(Page.objects.get(reverse_id="home").is_home, "home page is still the home page")

    check_rendering(snapshot)

    print("Writing to the upgraded schema")
    page = write_after_upgrade()
    response = Client().get(page.get_absolute_url("en"))
    check(response.status_code == 200, f"new page {page.get_absolute_url('en')} -> {response.status_code}")
    check(marker("after-upgrade", "en", 0) in response.content.decode(), "new page shows its content")

    with transaction.atomic():
        Page.objects.get(reverse_id="team").delete()
    check(not Page.objects.filter(reverse_id="team").exists(), "page can be deleted")


if __name__ == "__main__":
    commands = {"populate": populate, "verify": verify}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(commands)}}}")
    commands[sys.argv[1]]()
    if failures:
        print(f"\n{len(failures)} check(s) failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    print("\nAll checks passed.")
