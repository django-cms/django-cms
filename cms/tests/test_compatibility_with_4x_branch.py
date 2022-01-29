import os

from django.test import testcases


class Compatibility4xTestCase(testcases.TestCase):


    def test_ensure_no_migration_is_added(self):
        """
        to ensure the next version is compatible with the 4.x branch, we need to make sure no new migration is added
        (otherwise, this will then conflicts with what is present in the 4.x branch
        """

        migration = os.path.join("cms", "migrations")
        MAX = 22

        for root, _, files in os.walk(migration):
            for name in files:
                if name == "__init__.py" or not name.endswith(".py"):
                    continue

                mid = int(name.split("_")[0])
                self.assertTrue(mid <= MAX, "migration %s conflicts with 4.x upgrade!" % name)
