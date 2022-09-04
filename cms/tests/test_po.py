import os
import shutil
import subprocess
import sys
from pathlib import Path

from django.core.management.base import CommandError
from django.core.management.commands.compilemessages import has_bom
from django.test.testcases import TestCase

from cms.test_utils.util.context_managers import TemporaryDirectory
from cms.utils.compat import DJANGO_2_2, DJANGO_3_0, DJANGO_3_1

THIS_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', 'locale'))


def compile_messages():
    # check if gettext is installed
    try:
        pipe = subprocess.Popen(['msgfmt', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        raise CommandError('Unable to run msgfmt (gettext) command. You probably don\'t have gettext installed. {}'.format(e))

    basedirs = [os.path.join('conf', 'locale'), 'locale']
    if os.environ.get('DJANGO_SETTINGS_MODULE'):
        from django.conf import settings
        basedirs.extend(settings.LOCALE_PATHS)

    # Gather existing directories.
    basedirs = set(map(os.path.abspath, filter(os.path.isdir, basedirs)))

    if not basedirs:
        raise CommandError("This script should be run from the Django SVN tree or your project or app tree, or with the settings module specified.")

    for basedir in basedirs:
        for dirpath, dirnames, filenames in os.walk(basedir):
            for f in filenames:
                if f.endswith('.po'):
                    if DJANGO_2_2 or DJANGO_3_0 or DJANGO_3_1:
                        pfn = os.path.join(dirpath, f)
                    else:
                        # for django3.2 and above. The change happened in djang3.2 to pathlib.
                        pfn = Path(dirpath) / f
                    if has_bom(pfn):
                        raise CommandError("The %s file has a BOM (Byte Order Mark). Django only supports .po files encoded in UTF-8 and without any BOM." % pfn)
                    pf = os.path.splitext(pfn)[0]
                    # Store the names of the .mo and .po files in an environment
                    # variable, rather than doing a string replacement into the
                    # command, so that we can take advantage of shell quoting, to
                    # quote any malicious characters/escaping.
                    # See http://cyberelk.net/tim/articles/cmdline/ar01s02.html
                    if sys.platform == 'win32': # Different shell-variable syntax
                        bits = ['msgfmt', '--check-format',  '-o',  pf + '.mo', pf + '.po']
                    else:
                        bits = ['msgfmt', '--check-format',  '-o',  pf + '.mo', pf + '.po']
                    pipe = subprocess.Popen(bits, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stderr = pipe.communicate()[-1]
                    if pipe.returncode != 0:
                        return False, stderr
    return True, ''


class PoTest(TestCase):
    def test_po_sanity(self):
        with TemporaryDirectory() as tmpdir:
            shutil.copytree(SOURCE_DIR, os.path.join(tmpdir, 'locale'))
            olddir = os.getcwd()
            os.chdir(tmpdir)
            try:
                ok, stderr = compile_messages()
            finally:
                os.chdir(olddir)
        self.assertTrue(ok, stderr)
