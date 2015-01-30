from contextlib import contextmanager
import os
import subprocess

SCRIPT = 'https://gist.githubusercontent.com/henrikhodne/9322897/raw/sauce-connect.sh'  # nopep8


def connect(username, api_key, script=SCRIPT):
    os.environ['SAUCE_USERNAME'] = username
    os.environ['SAUCE_ACCESS_KEY'] = api_key
    curl = subprocess.Popen(['curl', script], stdout=subprocess.PIPE)
    bash = subprocess.Popen(['bash'], stdin=curl.stdout)
    curl.stdout.close()
    _, basherr = bash.communicate()
    if bash.returncode != 0:
        raise Exception(basherr)


def disconnect():
    if os.path.exists('/tmp/sc_client.pid'):
        with open('/tmp/sc_client.pid') as fobj:
            pid = fobj.read().strip()
            subprocess.call(['kill', pid])


@contextmanager
def sauce_connect(username, api_key, script=SCRIPT):
    try:
        connect(username, api_key, script)
        yield
    finally:
        disconnect()
