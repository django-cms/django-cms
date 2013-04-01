from setuptools import setup, find_packages
import sys

import os
import re


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__\s*=\s*(.*)", init_py).group(1)


version = get_version('cms')

if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist upload")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]

setup(
    author="Patrick Lauber",
    author_email="digi@treepy.com",
    name='django-cms',
    version=version,
    description='An Advanced Django CMS',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='https://www.django-cms.org/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'Django>=1.4,<1.6',
        'django-classy-tags>=0.3.4.1',
        'south>=0.7.2',
        'html5lib',
        'django-mptt>=0.5.1,<0.5.3',
        'django-sekizai>=0.7',
    ],
    tests_require=[
        'django-reversion>=1.6',
        'Pillow==1.7.7',
        'Sphinx==1.1.3',
        'Jinja2==2.6',
        'Pygments==1.5',
        'dj-database-url==0.2.1',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    test_suite='runtests.main',
)
