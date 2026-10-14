import importlib
import pkgutil
import warnings

from django.test import TestCase

import cms
from cms import compat
from cms.compat import moved, registry, resolve
from cms.utils.compat.warnings import RemovedInDjangoCMS70Warning

SKIP_PREFIXES = (
    "cms.tests",
    "cms.test_utils",
    "cms.migrations",
    "menus.migrations",
)


def _import_cms_tree():
    """Import every non-test CMS module, so the move registry is complete."""
    import cms
    import menus

    for package in (cms, menus):
        for module_info in pkgutil.walk_packages(package.__path__, f"{package.__name__}."):
            if module_info.name.startswith(SKIP_PREFIXES):
                continue
            try:
                importlib.import_module(module_info.name)
            except ImportError:
                # Optional integrations (e.g. a management command whose backend
                # is not installed) must not turn into a shim failure.
                continue


class MovedRegistryTest(TestCase):
    """The move registry is the deprecation schedule; keep it honest."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _import_cms_tree()

    def test_every_entry_resolves(self):
        """A typo in a dotted string fails here, not at a downstream import."""
        for entry in registry():
            with self.subTest(old=entry.old_path):
                resolve(entry.new_path)

    def test_old_path_is_new_object(self):
        """Shims re-export the moved object itself -- not a copy, not a subclass.

        This is what keeps ``isinstance``, ``issubclass`` and ``sender=Page``
        signal wiring working through either path.
        """
        for entry in registry():
            with self.subTest(old=entry.old_path):
                module_path, _, attribute = entry.old_path.rpartition(".")
                old = getattr(importlib.import_module(module_path), attribute)
                self.assertIs(old, resolve(entry.new_path))

    def test_shim_modules_declare_dunder_all(self):
        """``from shim import *`` does not consult PEP 562 ``__getattr__``."""
        shim_modules = {entry.old_path.rpartition(".")[0] for entry in registry()}
        for module_path in sorted(shim_modules):
            with self.subTest(module=module_path):
                module = importlib.import_module(module_path)
                self.assertTrue(
                    getattr(module, "__all__", None),
                    f"{module_path} declares moved names but has no __all__, so "
                    f"star-imports of it would silently lose them",
                )

    def test_shims_are_silent_in_the_release_that_moved_them(self):
        """A release performs its moves; it does not warn about them.

        Downstream code cannot import the new location from any released
        version yet, so warning immediately would turn every project's test
        suite red over a change its authors cannot act on. Warnings get
        switched on in a *later* release, by editing ``warn=``.
        """
        current = ".".join(cms.__version__.split(".")[:2])
        noisy = [entry.old_path for entry in registry() if entry.since == current and entry.warn is not None]
        self.assertEqual(
            noisy,
            [],
            f"shims moved in {current} must ship with warn=None; warn in a later release instead",
        )


class MovedHelperTest(TestCase):
    def setUp(self):
        # The fake shims below must not outlive the test: the registry is global,
        # and every test reading ``registry()`` afterwards would try to import them.
        snapshot = dict(compat._registry)

        def restore():
            compat._registry.clear()
            compat._registry.update(snapshot)

        self.addCleanup(restore)

    def test_returns_getattr_dir_and_all(self):
        __getattr__, __dir__, __all__ = moved(
            "cms.tests.test_compat_shims._fake_a",
            {"resolve": "cms.compat.resolve"},
            since="6.0",
        )
        self.assertIs(__getattr__("resolve"), resolve)
        self.assertEqual(__dir__(), ["resolve"])
        self.assertEqual(__all__, ["resolve"])

    def test_unknown_name_raises_attribute_error(self):
        __getattr__, _, _ = moved(
            "cms.tests.test_compat_shims._fake_b",
            {"resolve": "cms.compat.resolve"},
            since="6.0",
        )
        with self.assertRaises(AttributeError):
            __getattr__("nope")

    def test_silent_by_default(self):
        __getattr__, _, _ = moved(
            "cms.tests.test_compat_shims._fake_c",
            {"resolve": "cms.compat.resolve"},
            since="6.0",
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            __getattr__("resolve")

    def test_warns_when_asked(self):
        __getattr__, _, _ = moved(
            "cms.tests.test_compat_shims._fake_d",
            {"resolve": "cms.compat.resolve"},
            since="6.0",
            warn=RemovedInDjangoCMS70Warning,
        )
        with self.assertWarns(RemovedInDjangoCMS70Warning):
            __getattr__("resolve")

    def test_conflicting_redeclaration_is_rejected(self):
        moved(
            "cms.tests.test_compat_shims._fake_e",
            {"thing": "cms.compat.resolve"},
            since="6.0",
        )
        with self.assertRaises(RuntimeError):
            moved(
                "cms.tests.test_compat_shims._fake_e",
                {"thing": "cms.compat.registry"},
                since="6.0",
            )
