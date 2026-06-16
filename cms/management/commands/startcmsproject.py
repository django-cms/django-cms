#!/usr/bin/env python
import argparse
import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

from django.core.checks.security.base import SECRET_KEY_INSECURE_PREFIX
from django.core.management import CommandError
from django.core.management.templates import TemplateCommand
from django.core.management.utils import get_random_secret_key

from cms import __version__ as cms_version


class ShellMixin:  # pragma: no cover
    """Run subprocesses / management commands and echo them to the user.

    Shared by both the new-project and existing-project flows. Expects the
    ``COMMAND`` style callable and ``stdout``/``stderr`` provided by the
    command class it is mixed into.
    """

    def write_command(self, command):
        self.stderr.write(self.COMMAND(command))

    def run_management_command(self, commands, capture_output=False):
        self.write_command("python -m manage " + " ".join(commands))
        result = subprocess.run([sys.executable, "-m", "manage"] + commands, capture_output=capture_output, check=False)
        if result.returncode:
            if capture_output:
                self.stderr.write(self.style.ERROR(result.stderr.decode()))
            raise CommandError(f"{sys.executable} -m manage {' '.join(commands)} failed.")

    @staticmethod
    def running_in_venv():
        return sys.prefix != sys.base_prefix


class PromptMixin:  # pragma: no cover
    """Interactive prompting for the project name and the project options."""

    # Effective defaults for the project options. The arguments themselves
    # default to ``None`` so that ``--interactive`` can tell apart an option
    # that was given on the command line from one that needs to be asked for.
    OPTION_DEFAULTS = {
        "mode": "traditional",
        "versioning": True,
        "moderation": False,
        "alias": True,
        "stories": False,
    }

    def ask(self, label, default=None):
        suffix = f" [{default}]" if default not in (None, "") else ""
        return input(f"{label}{suffix}: ").strip() or default

    def ask_choice(self, label, choices, default):
        while True:
            value = self.ask(f"{label} ({'/'.join(choices)})", default)
            if value in choices:
                return value
            self.stderr.write(self.style.ERROR(f"Please choose one of: {', '.join(choices)}"))

    def ask_bool(self, label, default):
        while True:
            value = self.ask(f"{label} (yes/no)", "yes" if default else "no").lower()
            if value in ("y", "yes", "true", "1", "on"):
                return True
            if value in ("n", "no", "false", "0", "off"):
                return False
            self.stderr.write(self.style.ERROR("Please answer yes or no."))

    def prompt_for_options(self, name, options):
        """Ask for the project name and any option still unset (``None``)."""
        self.stdout.write(self.HEADING(f"Create django CMS {cms_version} project"))
        if not name:
            while not name:
                name = self.ask("Project name")
                if not name:
                    self.stderr.write(self.style.ERROR("A project name is required."))
        if options.get("mode") is None:
            options["mode"] = self.ask_choice(
                "CMS mode", ("traditional", "headless", "hybrid"), self.OPTION_DEFAULTS["mode"]
            )
        if options.get("versioning") is None:
            options["versioning"] = self.ask_bool("Enable content versioning", self.OPTION_DEFAULTS["versioning"])
        if options.get("moderation") is None:
            # Moderation builds on top of versioning, so only offer it when
            # versioning is enabled; otherwise it stays off.
            options["moderation"] = (
                self.ask_bool("Enable content moderation", self.OPTION_DEFAULTS["moderation"])
                if options["versioning"]
                else False
            )
        if options.get("alias") is None:
            options["alias"] = self.ask_bool("Add reusable aliases", self.OPTION_DEFAULTS["alias"])
        if options.get("stories") is None:
            options["stories"] = self.ask_bool("Add the stories component library", self.OPTION_DEFAULTS["stories"])
        return name


class SourceEditorMixin:
    """Best-effort, regex-based editing of a project's ``settings.py`` / ``urls.py``.

    A self-contained toolkit of (mostly static) text-manipulation helpers used
    when adding django CMS to an existing project. It knows nothing about the
    command options; the install rules in :class:`ExistingProjectMixin` decide
    *what* to insert, these helpers decide *how* to splice it into the source.
    """

    @staticmethod
    def _read(path):
        with open(path, encoding="utf-8") as handle:
            return handle.read()

    @staticmethod
    def _write(path, text):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def _show_diff(self, path, original, new):
        """Print a coloured unified diff of an edit (for ``--dry-run``).

        An empty ``original`` renders as a new file (``--- /dev/null``).
        """
        if original == new:
            return
        rel = os.path.relpath(path)
        diff = difflib.unified_diff(
            original.splitlines(), new.splitlines(),
            fromfile="/dev/null" if not original else rel, tofile=rel, lineterm="",
        )
        for line in diff:
            if line.startswith(("+++", "---")):
                self.stdout.write(line)
            elif line.startswith("+"):
                self.stdout.write(self.style.SUCCESS(line))
            elif line.startswith("-"):
                self.stdout.write(self.style.ERROR(line))
            elif line.startswith("@@"):
                self.stdout.write(self.style.WARNING(line))
            else:
                self.stdout.write(line)

    @staticmethod
    def module_to_path(module):
        """Resolve a dotted module path to a file below the current directory."""
        parts = module.split(".")
        base = os.path.join(os.getcwd(), *parts)
        if os.path.isfile(base + ".py"):
            return base + ".py"
        if os.path.isfile(os.path.join(base, "__init__.py")):
            return os.path.join(base, "__init__.py")
        return None

    def get_settings_module(self, manage_py):
        """Extract the DJANGO_SETTINGS_MODULE value from a manage.py file."""
        text = self._read(manage_py)
        match = re.search(r"""DJANGO_SETTINGS_MODULE['"]?\s*,\s*['"]([\w.]+)['"]""", text)
        if not match:
            raise CommandError("Could not determine DJANGO_SETTINGS_MODULE from manage.py.")
        return match.group(1)

    def get_urlconf(self, settings_text, settings_module):
        """Return the ROOT_URLCONF module, falling back to ``<project>.urls``."""
        match = re.search(r"""(?m)^ROOT_URLCONF\s*=\s*['"]([\w.]+)['"]""", settings_text)
        if match:
            return match.group(1)
        return settings_module.rsplit(".", 1)[0] + ".urls"

    @staticmethod
    def _get_setting_value(text, name):
        """Return the quoted string value of a top-level ``NAME = "..."`` setting."""
        match = re.search(rf"""(?m)^{name}\s*=\s*['"]([^'"]+)['"]""", text)
        return match.group(1) if match else None

    @staticmethod
    def _language_name(language_code):
        """Human-readable name for a language code, falling back to the code."""
        try:
            from django.utils.translation import get_language_info

            return get_language_info(language_code)["name"]
        except KeyError:
            return language_code

    @staticmethod
    def _uses_i18n_patterns(text):
        """Whether the urls module already routes patterns through ``i18n_patterns``."""
        return bool(re.search(r"\bi18n_patterns\s*\(", text))

    @staticmethod
    def _append_i18n_patterns(text, items):
        """Append ``urlpatterns += i18n_patterns(...)`` with ``items`` to the module.

        A new block is added at the end of the file (after any existing
        ``i18n_patterns`` call) so the CMS catch-all stays last. The
        ``i18n_patterns`` import is assumed present -- this is only called when
        the module already uses it.
        """
        if not text.endswith("\n"):
            text += "\n"
        lines = "\n".join(f"    {item}," for item in items)
        block = "\n# django CMS URLs (added by `djangocms .`)\nurlpatterns += i18n_patterns(\n" + lines + "\n)\n"
        return text + block, list(items)

    @classmethod
    def _ensure_include_import(cls, text):
        """Make sure ``include`` is importable from ``django.urls`` in urls.py."""
        if re.search(r"(?m)^\s*from django\.urls import .*\binclude\b", text):
            return text
        return cls._insert_import(text, "from django.urls import include")

    @staticmethod
    def _insert_import(text, statement):
        """Insert an import ``statement`` at a safe top-level position.

        Inserts after the last existing top-level ``import``/``from`` line so the
        statement never lands before a shebang, encoding comment, module
        docstring, or ``from __future__`` imports (which must stay at the top).
        If the module has no imports yet, the statement is placed after any
        shebang, encoding declaration, and module docstring.
        """
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith(("import ", "from ")):
                insert_at = i + 1
        if insert_at == 0:
            # No imports found: skip over shebang, encoding comment and docstring.
            if insert_at < len(lines) and lines[insert_at].startswith("#!"):
                insert_at += 1
            if insert_at < len(lines) and re.match(r"#.*coding[:=]", lines[insert_at]):
                insert_at += 1
            match = re.match(r'\s*(?P<quote>"""|\'\'\')', lines[insert_at]) if insert_at < len(lines) else None
            if match:
                quote = match.group("quote")
                # Single-line docstring (opening and closing quotes on one line).
                if lines[insert_at].count(quote) >= 2:
                    insert_at += 1
                else:
                    insert_at += 1
                    while insert_at < len(lines) and quote not in lines[insert_at]:
                        insert_at += 1
                    if insert_at < len(lines):
                        insert_at += 1
        lines.insert(insert_at, statement + "\n")
        return "".join(lines)

    @staticmethod
    def _insert_into_list(text, name, items, quote=True):
        """Insert ``items`` into a list/tuple assignment ``name = [...]``.

        Works for top-level assignments (``NAME = [`` / ``NAME += [``) as well as
        dict entries (``"name": [``). Existing entries are left untouched.
        Returns ``(new_text, added_items)``.
        """
        pattern = re.compile(rf"""(?m)^(?P<indent>[ \t]*)['"]?{re.escape(name)}['"]?\s*(?:\+?=|:)\s*[\[(]""")
        match = pattern.search(text)
        if not match:
            return text, []
        open_pos = match.end() - 1
        depth = 0
        close_pos = None
        for i in range(open_pos, len(text)):
            char = text[i]
            if char in "[(":
                depth += 1
            elif char in ")]":
                depth -= 1
                if depth == 0:
                    close_pos = i
                    break
        if close_pos is None:
            return text, []

        body = text[open_pos + 1:close_pos]
        # Derive the indentation of the list items.
        indent = None
        for line in body.splitlines():
            if line.strip():
                indent = line[: len(line) - len(line.lstrip())]
                break
        if indent is None:
            indent = match.group("indent") + "    "

        added, rendered = [], []
        for item in items:
            token = f'"{item}"' if quote else item
            present = (f'"{item}"' in body or f"'{item}'" in body) if quote else (item in body)
            if present:
                continue
            rendered.append(f"{indent}{token},")
            added.append(item)
        if not added:
            return text, []

        # Splice the new lines in just before the closing bracket, preserving
        # that bracket's own indentation when it sits on its own line.
        line_start = text.rfind("\n", 0, close_pos) + 1
        if text[line_start:close_pos].strip() == "":
            head, tail = text[:line_start], text[line_start:]
        else:
            # Inline list (e.g. ``"DIRS": []``): the closing bracket moves to its
            # own line, indented like the assignment for readability.
            head, tail = text[:close_pos], match.group("indent") + text[close_pos:]
        head = head.rstrip()
        if head and head[-1] not in "[(,":
            head += ","
        new_text = head + "\n" + "\n".join(rendered) + "\n" + tail
        return new_text, added

    def _insert_near_anchor(self, text, item, anchor, before=False, list_name=None):
        """Insert quoted ``item`` immediately before/after the ``anchor`` entry.

        Used for entries with a required position (e.g. Django's LocaleMiddleware
        after ``SessionMiddleware``, or the admin style before
        ``django.contrib.admin``). Falls back to appending to ``list_name`` when
        the anchor is not found.
        """
        if f'"{item}"' in text or f"'{item}'" in text:
            return text, []
        pattern = re.compile(rf"""(?m)^([ \t]*)(["']){re.escape(anchor)}\2(\s*,)?""")
        match = pattern.search(text)
        if not match:
            return self._insert_into_list(text, list_name, [item]) if list_name else (text, [])
        indent, quote, comma = match.group(1), match.group(2), match.group(3)
        if before:
            new_line = f"{indent}{quote}{item}{quote},\n"
            text = text[: match.start()] + new_line + text[match.start():]
        else:
            # Make sure the anchor line keeps its trailing comma.
            prefix = "" if comma else ","
            new_line = f"\n{indent}{quote}{item}{quote},"
            text = text[: match.end()] + prefix + new_line + text[match.end():]
        return text, [item]

    @staticmethod
    def _list_assignment_kind(text, name):
        """Classify the first top-level assignment to ``name``.

        Returns ``"literal"`` for an editable ``NAME = [`` / ``NAME = (`` list or
        tuple, ``"computed"`` for any other value (e.g. ``NAME = DJANGO + EXTRA``,
        which has no list literal to splice into), or ``"none"`` when there is no
        such assignment. The *first* assignment wins, so a recovery reassignment
        appended later (see :meth:`_append_list_extension`) does not flip a
        computed list back to "literal" on a rerun.
        """
        match = re.search(rf"(?m)^[ \t]*{re.escape(name)}\s*\+?=\s*(\S)", text)
        if not match:
            return "none"
        return "literal" if match.group(1) in "[(" else "computed"

    def _append_list_extension(self, text, name, before_items, after_items):
        """Recover when ``name`` is a computed value rather than a literal list.

        Appends a ``name = [before] + name + [after]`` reassignment to the end of
        the module so the new entries are added without rewriting the original
        expression. This is best-effort: exact ``before``/``after`` anchors are
        reduced to 'prepend' / 'append', so the caller flags the result for
        review. Items already present anywhere in the module are skipped, which
        keeps reruns idempotent. Returns ``(new_text, added_items)``.
        """
        before_new = [item for item in before_items if f'"{item}"' not in text and f"'{item}'" not in text]
        after_new = [item for item in after_items if f'"{item}"' not in text and f"'{item}'" not in text]
        if not before_new and not after_new:
            return text, []
        if not text.endswith("\n"):
            text += "\n"
        prefix = "[\n" + "".join(f'    "{item}",\n' for item in before_new) + "] + " if before_new else ""
        suffix = " + [\n" + "".join(f'    "{item}",\n' for item in after_new) + "]" if after_new else ""
        block = (
            f"\n# django CMS: {name} is a computed value, not a literal list, so the new\n"
            f"# entries were appended here instead of inserted in place (`djangocms .`).\n"
            f"# Review their position relative to your existing entries.\n"
            f"{name} = {prefix}{name}{suffix}\n"
        )
        return text + block, before_new + after_new


class NewProjectMixin:  # pragma: no cover
    """Create a brand-new project by cloning the cms-template, then bootstrap it.

    Covers the default flow (a project name other than ``"."``): rendering the
    template, installing its requirements, running migrations, creating the
    superuser and reporting success.
    """

    def get_default_template(self):
        return f"https://github.com/django-cms/cms-template/archive/{self.major_minor}.tar.gz"

    def handle_template(self, template, subdir):
        if not template:
            template = self.get_default_template()
        return super().handle_template(template, subdir)

    def postprocess(self, project, options):
        # Go to project dir
        self.write_command(f'cd "{project}"')
        os.chdir(project)

        # Install requirements
        self.install_requirements(project)

        # Create database by running migrations
        self.stdout.write(self.HEADING("Run migrations"))
        self.run_management_command(["migrate"], capture_output=True)

        # Create superuser (respecting command line arguments)
        self.stdout.write(self.HEADING("Create superuser"))
        command = ["createsuperuser"]
        if options.get("username"):
            command.append("--username")
            command.append(options.get("username"))
        if options.get("email"):
            command.append("--email")
            command.append(options.get("email"))
        if not options["interactive"]:
            if "--username" not in command:
                command.append("--username")
                command.append(os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin"))
            if "--email" not in command:
                command.append("--email")
                command.append(os.environ.get("DJANGO_SUPERUSER_EMAIL", "none@nowhere.com"))
            command.append("--noinput")
        self.run_management_command(command)

        # Check installation
        self.stdout.write(self.HEADING("Check installation"))
        self.run_management_command(["cms", "check"], capture_output=True)

        # Display success message
        message = f"django CMS {cms_version} installed successfully"
        separator = "*" * len(message)
        self.stdout.write(self.HEADING(f"{separator}\n{message}\n{separator}"))
        self.stdout.write(
            f"""
Congratulations! You have successfully installed django CMS,
the lean enterprise content management powered by Django!

Now, to start the development server first go to your newly
created project and then call the runserver management command:
$ {self.style.SUCCESS("cd " + project)}
$ {self.style.SUCCESS("python -m manage runserver")}

Learn more at https://docs.django-cms.org/
Join the django CMS Discord Server at https://discord-main-channel.django-cms.org

Enjoy!
"""
        )

    def install_requirements(self, project):
        for req_file in ("requirements.txt", "requirements.in"):
            requirements = os.path.join(project, req_file)
            if os.path.isfile(requirements):
                if self.running_in_venv() or os.environ.get("DJANGOCMS_ALLOW_PIP_INSTALL", "False") == "True":
                    self.stdout.write(self.HEADING(f"Install requirements in {requirements}"))
                    self.write_command(f"python -m pip install -r {shlex.quote(requirements)}")
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", requirements],
                        capture_output=True, check=False,
                    )
                    if result.returncode:
                        self.stderr.write(self.style.ERROR(result.stderr.decode()))
                        raise CommandError(f"Failed to install requirements in {requirements}")
                    break
                else:
                    self.stderr.write(
                        self.style.ERROR(
                            "To automatically install requirements for your new django CMS "
                            "project use this command in a virtual environment."
                        )
                    )
                    raise CommandError("Requirements not installed")


class ExistingProjectMixin:
    """Add django CMS to the existing Django project in the current directory.

    Covers the ``djangocms .`` flow: it reads the install rules (fetched from
    the cms-template repository, with a bundled fallback), edits the project's
    ``settings.py`` and ``urls.py`` through :class:`SourceEditorMixin`, and
    installs the resulting package set.
    """

    # The rules for installing django CMS into an *existing* project (name ".")
    # live in a JSON file that is fetched from the cms-template repository (the
    # branch matching the installed django CMS major.minor), with the file
    # bundled next to this command serving as the offline fallback.
    INSTALL_RULES_FILENAME = "djangocms_install_rules.json"

    # Package names may only contain letters, digits, underscores and minus signs.
    SAFE_PACKAGE_RE = re.compile(r"^[A-Za-z0-9_-]+$")

    def get_install_rules_url(self):
        return (
            "https://raw.githubusercontent.com/django-cms/cms-template/"
            f"{self.major_minor}/{self.INSTALL_RULES_FILENAME}"
        )

    def add_to_existing_project(self, options):
        """Add django CMS to the existing Django project in the current directory.

        The project's settings module is read from ``manage.py``; INSTALLED_APPS,
        MIDDLEWARE and the template context processors are updated according to
        the rules (and the given flags), and the project's ``urls.py`` (from
        ``ROOT_URLCONF``) is wired up for the selected mode.
        """
        cwd = os.getcwd()
        manage_py = os.path.join(cwd, "manage.py")
        if not os.path.isfile(manage_py):
            raise CommandError("Cannot add django CMS: no manage.py found in the current directory.")

        settings_module = self.get_settings_module(manage_py)
        settings_file = self.module_to_path(settings_module)
        if not settings_file:
            raise CommandError(f"Cannot locate the settings file for '{settings_module}'.")

        dry_run = options.get("dry_run")
        self.stdout.write(self.HEADING(f"Add django CMS {cms_version} to an existing project"))
        if dry_run:
            # Dry run: nothing is written, so there is nothing to confirm.
            self.stdout.write(
                f"Dry run: showing the changes that would be made to {os.path.relpath(settings_file, cwd)}\n"
                "and your project's urls. No files are created, modified or installed."
            )
        else:
            # Make sure the user understands these are automated, best-effort edits
            # to their own project files before anything is changed.
            self.stdout.write(
                f"This will make automated changes to {os.path.relpath(settings_file, cwd)} and your\n"
                "project's urls, and may create a templates directory. These edits are best-effort\n"
                "and must be reviewed afterwards, so make sure your project is under version control\n"
                "(or backed up) to inspect the changes."
            )
            if options.get("interactive", True) and not self.ask_bool("Continue", True):
                self.stdout.write("Aborted; no changes made.")
                return

        rules = self.load_install_rules()

        # Emit any warnings whose condition matches (e.g. an option that no
        # longer has an effect). These are defined by the rules file so they can
        # be added/updated without changing django CMS.
        for warning in rules.get("warnings", []):
            if self._rule_applies(warning.get("when"), options):
                self.stderr.write(self.style.WARNING(warning["message"]))

        self.stdout.write(self.HEADING(f"Add django CMS {cms_version} to {settings_module}"))

        # --- settings.py ---------------------------------------------------
        original_settings = self._read(settings_file)
        text = original_settings

        # Apps to add from the rules, honouring each rule's condition (a flag
        # and/or the selected mode). Rules with a `before`/`after` anchor are
        # positioned relative to an existing entry; the rest are appended.
        text, apps, added_apps, apps_recovered = self._apply_list_rules(
            text, "INSTALLED_APPS", rules.get("installed_apps", []), options
        )
        text, _, added_mw, mw_recovered = self._apply_list_rules(
            text, "MIDDLEWARE", rules.get("middleware", []), options
        )

        context_processors = []
        for rule in rules.get("context_processors", []):
            if self._rule_applies(rule.get("when"), options):
                context_processors += rule["items"]
        text, added_cp = self._insert_into_list(text, "context_processors", context_processors)

        text, added_dirs, created_paths = self._ensure_template_dir(text, cwd, rules.get("template_dir"), options)
        text, added_settings = self._append_cms_settings(text, rules.get("settings", []), options)

        if dry_run:
            # In a dry run the diff is the whole report: the settings change plus
            # any files that would be created (e.g. the base template).
            self._show_diff(settings_file, original_settings, text)
            template_content = (rules.get("template_dir") or {}).get("base_template_content", "")
            for path in created_paths:
                if not path.endswith("/"):
                    self._show_diff(path, "", template_content)
        else:
            self._write(settings_file, text)
            self.stdout.write(f"Updated {os.path.relpath(settings_file, cwd)}")
            for app in added_apps:
                self.stdout.write(f"  + INSTALLED_APPS: {app}")
            for mw in added_mw:
                self.stdout.write(f"  + MIDDLEWARE: {mw}")
            for cp in added_cp:
                self.stdout.write(f"  + context_processors: {cp}")
            for entry in added_dirs:
                self.stdout.write(f"  + TEMPLATES DIRS: {entry}")
            for setting in added_settings:
                self.stdout.write(f"  + {setting}")
            for path in created_paths:
                self.stdout.write(f"  + created {path}")

        # When a setting is a computed value rather than a literal list, the
        # entries could not be spliced in place and were appended through a
        # reassignment instead -- the order is a best-effort guess to review.
        if apps_recovered and added_apps:
            self.stderr.write(
                self.style.WARNING(
                    "INSTALLED_APPS is a computed value, so the new apps were appended via a "
                    "reassignment at the end of the settings file. Review their order."
                )
            )
        if mw_recovered and added_mw:
            self.stderr.write(
                self.style.WARNING(
                    "MIDDLEWARE is a computed value, so the new middleware was appended via a "
                    "reassignment at the end of the settings file. Review the order carefully, "
                    "as middleware ordering is significant."
                )
            )

        # --- urls.py -------------------------------------------------------
        urls_module = self.get_urlconf(text, settings_module)
        urls_file = self.module_to_path(urls_module)
        if urls_file:
            added_urls, urls_original, urls_text = self.update_urls(urls_file, options, rules.get("urls", []))
            if dry_run:
                self._show_diff(urls_file, urls_original, urls_text)
            else:
                self._write(urls_file, urls_text)
                self.stdout.write(f"Updated {os.path.relpath(urls_file, cwd)}")
                for url in added_urls:
                    self.stdout.write(f"  + urlpatterns: {url}")
        else:
            self.stderr.write(
                self.style.WARNING(
                    f"Could not locate the urls file for '{urls_module}'. "
                    "Please add the django CMS urls manually."
                )
            )

        self._finish_existing_project(apps, rules.get("packages", {}), options)

    def load_install_rules(self):
        """Fetch the install rules from GitHub, falling back to the bundled file."""
        url = self.get_install_rules_url()
        try:
            with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310 (https URL)
                rules = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            self.stderr.write(
                self.style.WARNING(f"Could not fetch installation rules from {url} ({exc}); using bundled defaults.")
            )
            bundled = os.path.join(os.path.dirname(__file__), self.INSTALL_RULES_FILENAME)
            rules = json.loads(self._read(bundled))
        if not isinstance(rules, dict):
            raise CommandError("Invalid installation rules: expected a JSON object.")
        # Metadata keys such as "$schema" or "comment" carry no rules.
        return {key: value for key, value in rules.items() if not key.startswith("$")}

    @staticmethod
    def _rule_applies(when, options):
        """Evaluate a rule condition against the command options.

        ``when`` may contain a ``flag`` (the option must be truthy) and/or a
        ``mode`` (a list of matching ``--mode`` values). A missing/empty
        condition always applies.
        """
        if not when:
            return True
        if "flag" in when and not options.get(when["flag"]):
            return False
        if "mode" in when and options.get("mode") not in when["mode"]:
            return False
        return True

    def update_urls(self, urls_file, options, url_rules):
        """Add the url patterns whose rule condition matches the options.

        Patterns flagged with ``"i18n": true`` (the CMS catch-all) must keep a
        language prefix, so they are added through ``i18n_patterns()`` -- but
        only when the project's urls.py already uses ``i18n_patterns``;
        otherwise they join the plain ``urlpatterns`` list like every other
        pattern.

        This computes the change but does not persist it; the caller writes the
        result (or shows a diff for ``--dry-run``). Returns
        ``(added_patterns, original_text, new_text)``.
        """
        original = self._read(urls_file)
        text = original
        uses_i18n = self._uses_i18n_patterns(text)
        plain_items, i18n_items = [], []
        for rule in url_rules:
            if not self._rule_applies(rule.get("when"), options):
                continue
            pattern = rule["pattern"]
            # Skip patterns whose include target is already routed.
            target = re.search(r"""include\(['"]([^'"]+)['"]\)""", pattern)
            if target and target.group(1) in text:
                continue
            if rule.get("i18n") and uses_i18n:
                i18n_items.append(pattern)
            else:
                plain_items.append(pattern)
        if not plain_items and not i18n_items:
            return [], original, original
        text = self._ensure_include_import(text)
        added = []
        if plain_items:
            text, just_added = self._insert_into_list(text, "urlpatterns", plain_items, quote=False)
            added += just_added
        if i18n_items:
            text, just_added = self._append_i18n_patterns(text, i18n_items)
            added += just_added
        return added, original, text

    def _ensure_template_dir(self, text, cwd, rule, options):
        """Create a project template directory if the project has none.

        When the rule's condition matches and the configured directory does not
        exist, it is created, registered in the ``TEMPLATES`` ``DIRS`` list, and
        seeded with the rule's base template. Returns
        ``(new_text, added_dirs, created_paths)``.
        """
        if not rule or not self._rule_applies(rule.get("when"), options):
            return text, [], []
        dir_name = rule.get("path", "templates")
        templates_dir = os.path.join(cwd, dir_name)
        if os.path.isdir(templates_dir):
            return text, [], []

        base_template = rule.get("base_template", "base.html")
        # In a dry run the DIRS entry is still added to the (in-memory) settings
        # text so the diff is accurate, but nothing is created on disk.
        if not options.get("dry_run"):
            os.makedirs(templates_dir)
            self._write(os.path.join(templates_dir, base_template), rule.get("base_template_content", ""))
        created_paths = [dir_name + "/", os.path.join(dir_name, base_template)]

        # Settings created before Django 3.1 define BASE_DIR with os.path
        # instead of pathlib, where the ``/`` operator does not work.
        if re.search(r"(?m)^BASE_DIR\s*=\s*Path\(", text):
            entry = f'BASE_DIR / "{dir_name}"'
        else:
            entry = f'os.path.join(BASE_DIR, "{dir_name}")'
            if not re.search(r"(?m)^import os\b", text):
                text = self._insert_import(text, "import os")
        text, added_dirs = self._insert_into_list(text, "DIRS", [entry], quote=False)
        return text, added_dirs, created_paths

    def _append_cms_settings(self, text, settings_rules, options):
        """Append the extra django CMS settings (from the rules) that are missing.

        Snippets may reference ``{language_code}`` / ``{language_name}``; these
        are derived from the project's LANGUAGE_CODE.
        """
        language_code = self._get_setting_value(text, "LANGUAGE_CODE") or "en-us"
        format_context = {"language_code": language_code, "language_name": self._language_name(language_code)}
        additions, added = [], []
        for rule in settings_rules:
            name = rule["name"]
            if not self._rule_applies(rule.get("when"), options):
                continue
            if re.search(rf"(?m)^{name}\s*=", text):
                continue
            additions.append(rule["snippet"].format(**format_context))
            added.append(name)
        if not additions:
            return text, []
        if not text.endswith("\n"):
            text += "\n"
        block = "\n# django CMS settings (added by `djangocms .`)\n" + "\n".join(additions) + "\n"
        return text + block, added

    def _apply_list_rules(self, text, list_name, list_rules, options):
        """Apply a set of list rules (e.g. INSTALLED_APPS / MIDDLEWARE).

        Each rule may carry a ``when`` condition and a ``before``/``after``
        anchor for positional insertion; rules without an anchor are appended in
        order.

        When the setting is a literal list this splices entries straight in. When
        it is a *computed* value (e.g. ``INSTALLED_APPS = DJANGO_APPS + EXTRA``)
        there is no literal to edit, so anchored entries are still positioned
        relative to their anchor wherever it occurs (often a sub-list literal),
        and everything else is added through a ``NAME = [..] + NAME + [..]``
        reassignment appended to the module -- a best-effort recovery the caller
        flags for review.

        Returns ``(new_text, all_items, added_items, recovered)`` where
        ``all_items`` is every item from matching rules (used for the install
        hint), ``added_items`` is what was actually inserted, and ``recovered``
        is whether the computed-value recovery path was taken.
        """
        recovery = self._list_assignment_kind(text, list_name) == "computed"
        all_items, added = [], []
        append_items, before_items, after_items = [], [], []
        for rule in list_rules:
            if not self._rule_applies(rule.get("when"), options):
                continue
            all_items += rule["items"]
            before, after = rule.get("before"), rule.get("after")
            if before or after:
                for item in rule["items"]:
                    # In recovery mode the anchor can still match a sub-list
                    # literal; only items whose anchor is absent fall back to the
                    # appended reassignment (grouped by before/after).
                    new_text, just_added = self._insert_near_anchor(
                        text, item, before or after, before=bool(before),
                        list_name=None if recovery else list_name,
                    )
                    if just_added:
                        text, added = new_text, added + just_added
                    elif recovery:
                        (before_items if before else after_items).append(item)
            elif recovery:
                after_items += rule["items"]
            else:
                append_items += rule["items"]
        if recovery:
            text, just_added = self._append_list_extension(text, list_name, before_items, after_items)
        else:
            text, just_added = self._insert_into_list(text, list_name, append_items)
        added += just_added
        return text, all_items, added, recovery

    def _finish_existing_project(self, apps, packages_map, options):
        """Offer to install the missing packages, then migrate and check."""
        packages = ["django-cms"]
        for app in apps:
            # Sub-apps like "djangocms_frontend.contrib.grid" ship with their
            # top-level package.
            app = app.split(".", 1)[0]
            if app in packages_map:
                packages.append(packages_map[app])
            elif app.startswith("djangocms"):
                packages.append(app.replace("_", "-"))
        packages = list(dict.fromkeys(packages))  # de-duplicate, keep order

        self.stdout.write(self.HEADING("Install dependencies"))
        self.stdout.write("django CMS needs the following packages:")
        self.stdout.write("  " + " ".join(packages))
        # A dry run never installs; otherwise ask (unless --noinput proceeds).
        dry_run = options.get("dry_run")
        if dry_run:
            install = False
        elif options.get("interactive", True):
            install = self.ask_bool("Install them now", True)
        else:
            install = True

        if not install:
            if dry_run:
                self.stdout.write("Dry run: would install the packages above, then run migrations and the check:")
            else:
                self.stdout.write("Skipped. Install them later, then run the migrations and check:")
            self.write_command("  python -m pip install " + " ".join(shlex.quote(p) for p in packages))
            self.write_command("  python -m manage migrate")
            self.write_command("  python -m manage cms check")
            return

        self.install_packages(packages)

        self.stdout.write(self.HEADING("Run migrations"))
        self.run_management_command(["migrate"])

        self.stdout.write(self.HEADING("Check installation"))
        self.run_management_command(["cms", "check"])

        message = f"django CMS {cms_version} added to your project"
        separator = "*" * len(message)
        self.stdout.write(self.HEADING(f"{separator}\n{message}\n{separator}"))
        self.stdout.write(
            f"""
Review the automated changes to your settings and urls, then
start the development server:
$ {self.style.SUCCESS("python -m manage runserver")}

Learn more at https://docs.django-cms.org/
Join the django CMS Discord Server at https://discord-main-channel.django-cms.org

Enjoy!
"""
        )

    def install_packages(self, packages):
        """pip install the given packages (guarded to a virtual environment)."""
        unsafe = [pkg for pkg in packages if not self.SAFE_PACKAGE_RE.match(pkg)]
        if unsafe:
            raise CommandError("Refusing to install packages with unexpected characters: " + ", ".join(unsafe))
        if not (self.running_in_venv() or os.environ.get("DJANGOCMS_ALLOW_PIP_INSTALL", "False") == "True"):
            self.stderr.write(
                self.style.ERROR(
                    "Refusing to install packages outside a virtual environment. "
                    "Activate one, or set DJANGOCMS_ALLOW_PIP_INSTALL=True, and install manually:"
                )
            )
            self.write_command("  python -m pip install " + " ".join(shlex.quote(p) for p in packages))
            raise CommandError("Packages not installed")
        self.stdout.write(self.HEADING("Install packages"))
        self.write_command("python -m pip install " + " ".join(shlex.quote(p) for p in packages))
        result = subprocess.run([sys.executable, "-m", "pip", "install", *(shlex.quote(p) for p in packages)], check=False)
        if result.returncode:
            raise CommandError("Failed to install the required packages.")


class Command(PromptMixin, NewProjectMixin, ExistingProjectMixin, SourceEditorMixin, ShellMixin, TemplateCommand):  # noqa: E501
    """Entry point: define the CLI and dispatch to the new/existing-project flow.

    The behaviour is split across focused mixins:

    * :class:`PromptMixin` -- interactive prompting and the option defaults,
    * :class:`NewProjectMixin` -- creating a project from the cms-template,
    * :class:`ExistingProjectMixin` -- adding django CMS to an existing project,
    * :class:`SourceEditorMixin` -- the regex-based settings/urls editing toolkit,
    * :class:`ShellMixin` -- running subprocesses and management commands.

    ``TemplateCommand`` is kept last in the MRO so every ``super()`` call
    (``create_parser``, ``add_arguments``, ``handle``, ``handle_template``)
    resolves to Django's implementation.
    """

    help = (
        "Creates a django CMS project directory structure for the given project "
        "name in the current directory or optionally in the given directory. "
        'Alternatively, use a project name of "." to add django CMS to the '
        "existing Django project in the current directory instead: its settings "
        "and urls are updated in place (best-effort, automated edits to review "
        "afterwards) and the required packages are installed."
    )
    missing_args_message = "You must provide a project name."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Version major.minor
        self.major_minor = ".".join(cms_version.split(".")[:2])

        # Configure formatting
        self.HEADING = lambda text: "\n" + self.style.SQL_FIELD(text)
        self.COMMAND = self.style.HTTP_SUCCESS

    def create_parser(self, *args, **kwargs):  # pragma: no cover -- argparse wiring; tests call handle() directly
        parser = super().create_parser(*args, **kwargs)
        # Allow running with no arguments at all: a missing project name drops
        # into interactive mode instead of erroring out. handle() still reports
        # a missing name when input is suppressed with --noinput.
        parser.missing_args_message = None
        return parser

    def add_arguments(self, parser):  # pragma: no cover -- argparse wiring; tests call handle() directly
        super().add_arguments(parser)
        # Make the project name optional so it can be asked for in interactive
        # mode; a missing name is reported by handle() otherwise.
        for action in parser._actions:
            if action.dest == "name":
                action.nargs = "?"
                break
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help=(
                "Tells django CMS to NOT prompt the user for input of any kind. "
                "Superusers created with --noinput will "
                "not be able to log in until they're given a valid password."
            ),
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            dest="prompt",
            default=False,
            help=(
                "Ask for the project name and any option not given on the command line. "
                "Interactive mode is also entered automatically when no project name is "
                "given (unless --noinput is used)."
            ),
        )
        parser.add_argument(
            "--username",
            help="Specifies the login for the superuser to be created (only when creating a new project).",
        )
        parser.add_argument(
            "--email",
            help="Specifies the email for the superuser to be created (only when creating a new project).",
        )
        parser.add_argument(
            "--stories",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds the stories component library (djangocms-stories) to the project (default: off)",
        )
        parser.add_argument(
            "--mode",
            choices=("traditional", "headless", "hybrid"),
            default=None,
            help="Selects the CMS mode: traditional, headless or hybrid (default: traditional).",
        )
        parser.add_argument(
            "--versioning",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds content versioning (djangocms-versioning) to the project (default: on).",
        )
        parser.add_argument(
            "--moderation",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds content moderation (djangocms-moderation) to the project (default: off).",
        )
        parser.add_argument(
            "--alias",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds reusable aliases (djangocms-alias) to the project (default: on).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help=(
                "Show the changes that would be made to an existing project (name '.') as a "
                "diff, without writing any files or installing packages."
            ),
        )

    def handle(self, **options):
        # Capture target and name for postprocessing
        name = options.pop("name", None)
        directory = options.pop("directory", None)

        # Interactively ask for the project name and any option not provided.
        # Prompting is enabled explicitly via --interactive, or implicitly when
        # no project name was given (unless input is suppressed with --noinput).
        prompt = options.pop("prompt", False) or (not name and options.get("interactive", True))
        if prompt:
            name = self.prompt_for_options(name, options)

        # Fill in the effective defaults for any option not given (and not
        # asked for interactively).
        for key, value in self.OPTION_DEFAULTS.items():
            if options.get(key) is None:
                options[key] = value

        if not name:
            raise CommandError(self.missing_args_message)

        # Content moderation builds on top of content versioning.
        if options["moderation"] and not options["versioning"]:
            raise CommandError("--moderation requires versioning; remove --no-versioning or drop --moderation.")

        # A project name of "." means: add django CMS to the existing project in
        # the current directory instead of cloning the project template.
        if name == ".":
            self.add_to_existing_project(options)
            return

        # --dry-run only makes sense for the in-place edits of an existing
        # project; there is nothing to diff when cloning a fresh template.
        if options.get("dry_run"):
            raise CommandError(
                "--dry-run is only supported when adding django CMS to an existing project (name '.')."
            )

        # Render requirements.in as a template too (django-admin only renders
        # files matching --extension or listed in --name by default); it
        # contains template variables for the selected options.
        options.setdefault("files", [])
        if "requirements.in" not in options["files"]:
            options["files"] = options["files"] + ["requirements.in"]

        # Create a random SECRET_KEY to put it in the main settings.
        options["secret_key"] = SECRET_KEY_INSECURE_PREFIX + get_random_secret_key()

        self.stdout.write(self.HEADING("Clone template using django-admin"))
        command = (
            f'django-admin startproject "{name}" ' f'--template {options["template"] or self.get_default_template()}'
        )
        if directory:
            command += f' --directory "{directory}"'
        self.write_command(command)

        if directory is None:
            top_dir = os.path.join(os.getcwd(), name)
        else:
            top_dir = os.path.abspath(os.path.expanduser(directory))
        # Only a directory created by this run may be cleaned up on failure;
        # an existing target (django-admin renders into it) is left untouched.
        created_dir = directory is None and not os.path.exists(top_dir)
        original_cwd = os.getcwd()

        try:
            # Run startproject command
            super().handle(
                "project", name, directory, cms_version=cms_version, cms_docs_version=self.major_minor, **options
            )
            self.postprocess(top_dir, options)
        except BaseException:
            # Remove the partially created project if the command fails or is
            # interrupted (e.g. Ctrl-C), but only when we created the directory.
            if created_dir and os.path.isdir(top_dir):
                os.chdir(original_cwd)
                self.stderr.write(self.style.WARNING(f"Removing partially created project at {top_dir}"))
                shutil.rmtree(top_dir, ignore_errors=True)
            raise
