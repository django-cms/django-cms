from datetime import datetime
from requests import get

url = "https://raw.githubusercontent.com/django-cms/djangocms-ecosystem/refs/heads/main/README.md"

ecosystem = []

check = "\u2713  "
cross = "\u00d7  "


def read_ecosystem():
    global ecosystem

    if not ecosystem:
        ecosystem = _read_ecosystem()
    return ecosystem


def _read_ecosystem():
    ecosystem_md = get(url).text
    ecosystem = []
    chapter = {}
    content = {}

    lines = ecosystem_md.split("\n")
    while lines:
        line = lines.pop(0)
        if line.startswith("## "):
           chapter = {"title": line[3:], "description": "", "content": []}
           content = {}
           ecosystem.append(chapter)
        elif line.startswith("### ") and chapter and "content" in chapter:
            content = {"title": line[4:], "description": "", "properties": {}}
            chapter["content"].append(content)
        elif line.startswith("* "):
            if content and "properties" in content and ":" in line:
                key, value = line[2:].split(":", 1)
                if ", " in value:
                    value = [item.strip() for item in value.split(", ")]

                else:
                    value = value.strip()
                content["properties"][key] = value
        elif line:
            if "description" in content:
                content["description"] += line + " "
            elif "description" in chapter:
                chapter["description"] += line + " "
    return ecosystem


def get_chapter(name: str) -> dict:
    ecosystem = read_ecosystem()
    for chapter in ecosystem:
        if chapter["title"] == name:
            return chapter
    return None


def sorted_versions(versions: list) -> list:
    return sorted(versions, key=lambda x: tuple(map(int, x.split("."))), reverse=True)


def get_django_versions():
    djangocms = get_chapter("django CMS")
    if djangocms is None:
        return []
    versions = set()
    for content in djangocms["content"]:
        if "django" in content["properties"]:
            for version in content["properties"]["django"]:
                versions.add(version)
    return sorted_versions(versions)


def get_python_versions():
    djangocms = get_chapter("django CMS")
    versions = set()
    if djangocms:
        for content in djangocms["content"]:
            if "python" in content["properties"]:
                for version in content["properties"]["python"]:
                    versions.add(version)
    return sorted_versions(versions)


def get_djangocms_versions():
    djangocms = get_chapter("django CMS")
    versions = set()
    if djangocms:
        for content in djangocms["content"]:
            if "title" in content and content["title"].startswith("django CMS"):
                versions.add(content["title"][10:].strip())
    return sorted_versions(versions)


def get_python_support(version: str) -> list:
    if djangocms := get_chapter("django CMS"):
        for content in djangocms["content"]:
            if content["title"] == f"django CMS {version}":
                return content["properties"].get("python", [])
    return []


def get_django_support(version: str) -> list:
    djangocms = get_chapter("django CMS")
    if djangocms:
        for content in djangocms["content"]:
            if content["title"] == f"django CMS {version}":
                return content["properties"].get("django", [])
    return []


def get_LTS_support(version: str) -> str:
    djangocms = get_chapter("django CMS")
    if djangocms:
        for content in djangocms["content"]:
            if content["title"] == f"django CMS {version}":
                lts = content["properties"].get("LTS", [])
                if isinstance(lts, list):
                    return lts
                return [lts]
    return []


_english_months = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}


def english_date(number_string):
    try:
        month, year = number_string.split("/")
    except ValueError:
        return number_string
    if month in _english_months:
        return f"{_english_months[month]} {year}"
    return number_string


def write_LTS_table(f):
    djangocms = get_djangocms_versions()
    python_versions = get_python_versions()
    django_versions = get_django_versions()
    separator = "========== " + len(python_versions[:-1]) * "==== " + "==== " + len(django_versions[:-1]) * "==== " + "===="
    sep2      = "---------- " + len(python_versions[:-1]) * "-----" + "---- " + len(django_versions[:-1]) * "-----" + "----"
    print(separator, file=f)
    print(f"Django CMS {'Python':<{5 * len(python_versions)}}Django", file=f)
    print(sep2, file=f)
    print("\\          " + " ".join(f"{py:4}" for py in python_versions) + " " + "  ".join(django_versions), file=f)
    print(separator, file=f)
    for cms in djangocms:
        python_support = get_python_support(cms)
        django_support = get_django_support(cms)
        lts_support = get_LTS_support(cms)
        if any([python_support, django_support]):
            python = [f"{check if py in python_support else cross} " for py in python_versions]
            django = [('LTS' if dj in lts_support else check) if dj in django_support else cross
                    for dj in django_versions]
            print(f"{cms + '.x':10} " + " ".join(python) + " " + "  ".join(django), file=f)
    print(separator, file=f)


def write_current_LTS(f, current=True):
    djangocms = get_djangocms_versions()
    django = get_chapter("Django timelines")
    chapter = get_chapter("django CMS")
    if chapter:

        def get_end_of_support(version):
            for dj in django["content"]:
                if dj["title"] == version:
                    return dj["properties"].get("end-of-support", "unknown")
            return "unknown"

        print("========== ============== ====== ========================", file=f)
        print("django CMS Feature freeze Django End of long-term support", file=f)
        print("========== ============== ====== ========================", file=f)

        this_year = datetime.now().strftime("%Y")
        this_month = datetime.now().strftime("%m")
        for cms in chapter["content"]:
            if cms["title"].startswith("django CMS ") and "LTS" in cms["properties"]:
                lts_versions = cms["properties"].get("LTS", [])
                if not isinstance(lts_versions, list):
                    lts_versions = [lts_versions]
                for lts in lts_versions:
                    end_of_support = get_end_of_support(lts)
                    try:
                        month, year = end_of_support.split("/")
                    except ValueError:
                        month, year = "12", "2099"
                    if (year == this_year and month >= this_month or year > this_year) is current:
                        print(f"{cms['title'][11:] + '.x':10} "
                            f"{english_date(cms['properties'].get('feature-freeze', '-')):<14} "
                            f"{lts:<6} {english_date(end_of_support)}", file=f)
        print("========== ============== ====== ========================", file=f)


def split_description(description, max_length=60):
    words = description.split()
    lines = []
    current_line = []

    for word in words:
        if sum(len(w) for w in current_line) + len(current_line) + len(word) <= max_length:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def write_plugin_table(f, deprecated=False):
    chapter = get_chapter("CMS packages")

    if chapter:
        print("========================== ============================================================ =========== ==================", file=f)
        print("Package                    Description                                                  Status      Supported Versions", file=f)
        print("========================== ============================================================ =========== ==================", file=f)
        for plugin in chapter["content"]:
            if bool(plugin["properties"].get("deprecated", False)) is deprecated:
                status = plugin["properties"].get("grade", "unknown")
                versions = plugin["properties"].get("django CMS", [])
                if not isinstance(versions, list):
                    versions = [versions]
                versions = ", ".join(versions)
                description = plugin['description']
                lines = split_description(description)
                print(f"{plugin['title']:<26} {lines[0]:<60} {status:<13} {versions}", file=f)
                for line in lines[1:]:
                    print(f"{'':26} {line:<60}", file=f)
        print("========================== ============================================================ =========== ==================", file=f)
