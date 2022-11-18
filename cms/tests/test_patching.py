from django.core.exceptions import ImproperlyConfigured

from cms.test_utils.testcases import CMSTestCase
from cms.utils.patching import patch_cms, patch_hook


class PatchingAPITests(CMSTestCase):

    def this_should_not_be_patchable(self):
        return "Never ever patch me"

    @patch_hook
    def this_can_be_patched(self):
        return "So far I have not been patched, but I could be."

    def test_method_patching(self):
        patch = lambda self: "I have been patched"
        repatch = lambda self: "I have been re-patched"

        # First test, if patching works
        self.assertEqual(self.this_can_be_patched(), "So far I have not been patched, but I could be.")
        patch_cms(PatchingAPITests, "this_can_be_patched", patch)
        self.assertEqual(self.this_can_be_patched(), "I have been patched")

        # Second test, if re-patching works
        patch_cms(PatchingAPITests, "this_can_be_patched", repatch)
        self.assertEqual(self.this_can_be_patched(), "I have been re-patched")

        # Third test, if patching unmarked methods fails
        self.assertEqual(self.this_should_not_be_patchable(), "Never ever patch me")
        with self.assertRaises(ImproperlyConfigured):
            patch_cms(PatchingAPITests, "this_should_not_be_patchable", patch)
        self.assertEqual(self.this_should_not_be_patchable(), "Never ever patch me")

    @property
    def not_patchable_prop(self):
        return "Never ever patch me"

    @patch_hook
    @property
    def patchable_prop(self):
        return "So far I have not been patched, but I could be."

    def test_property_patching(self):
        patch = lambda self: "I have been patched"
        repatch = lambda self: "I have been re-patched"

        # First test, if patching works
        self.assertEqual(self.patchable_prop, "So far I have not been patched, but I could be.")
        patch_cms(PatchingAPITests, "patchable_prop", property(patch))
        self.assertEqual(self.patchable_prop, "I have been patched")

        # Second test, if re-patching works
        patch_cms(PatchingAPITests, "patchable_prop", property(repatch))
        self.assertEqual(self.patchable_prop, "I have been re-patched")

        # Third test, if patching unmarked properties fails
        self.assertEqual(self.not_patchable_prop, "Never ever patch me")
        with self.assertRaises(ImproperlyConfigured):
            patch_cms(PatchingAPITests, "not_patchable_prop", property(patch))
        self.assertEqual(self.not_patchable_prop, "Never ever patch me")
