#!/usr/bin/env python
import os

from cms import __version__
from setuptools import find_packages, setup


REQUIREMENTS = [
    'Django>=3.2,<5.0',
    'django-classy-tags>=0.7.2',
    'django-formtools>=2.1',
    'django-treebeard>=4.3',
    'django-sekizai>=0.7',
    'djangocms-admin-style>=1.2',
    'packaging',
]


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Framework :: Django',
    'Framework :: Django :: 2.2',
    'Framework :: Django :: 3.1',
    'Framework :: Django :: 3.2',
    'Framework :: Django :: 4.0',
    'Framework :: Django :: 4.1',
    'Framework :: Django :: 4.2',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]


setup(
    name='django-cms',
    version=__version__,
    author='Django CMS Association and contributors',
    author_email='info@django-cms.org',
    url='https://www.django-cms.org/',
    license='BSD-3-Clause',
    description='Lean enterprise content management powered by Django.',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    long_description_content_type='text/x-rst',
    packages=find_packages(exclude=['project', 'project.*']),
    python_requires='>=3.7',
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    classifiers=CLASSIFIERS,
    test_suite='runtests.main',
)
