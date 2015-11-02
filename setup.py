from setuptools import setup, find_packages
import os
import cms


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
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Framework :: Django',
    'Framework :: Django :: 1.6',
    'Framework :: Django :: 1.7',
    'Framework :: Django :: 1.8',
]

INSTALL_REQUIREMENTS = [
    'Django>=1.6.9,<1.9',
    'django-classy-tags>=0.5',
    'html5lib>=0.90,!=0.9999,!=0.99999',
    'django-formtools>=1.0',
    'django-treebeard==3.0',
    'django-sekizai>=0.7',
    'djangocms-admin-style',
]

#
# NOTE: divio/django-formtools is IDENTICAL to django/django-formtools except
# that its Django requirement has been relaxed to >=Django>=1.6. This is because
# this version of django CMS supports Django 1.6+. Internally, CMS will use
# django.contrib.formtools when available, then look for the external version if
# required. Unfortunately, SetupTools doesn't allow use to load the external
# library when using Django 1.7+ only.
#
# Further note that dependency links do not work by default. Current versions of
# Pip support it with the flag `--process-dependency-links`
#
# Remove these machinations in CMS v3.3 when Django 1.6 support is dropped.
#
DEPENDENCY_LINKS = [
    "https://github.com/divio/django-formtools/archive/master.zip#egg=django-formtools",
]

setup(
    author='Patrick Lauber',
    author_email='digi@treepy.com',
    name='django-cms',
    version=cms.__version__,
    description='An Advanced Django CMS',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='https://www.django-cms.org/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIREMENTS,
    dependency_links=DEPENDENCY_LINKS,
    extras_require={
        'south': ['south>=1.0.0'],
    },
    packages=find_packages(exclude=['project', 'project.*']),
    include_package_data=True,
    zip_safe=False,
    test_suite='runtests.main',
)
