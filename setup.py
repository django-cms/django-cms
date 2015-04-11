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
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
]

setup(
    author="Patrick Lauber",
    author_email="digi@treepy.com",
    name='django-cms',
    version=cms.__version__,
    description='An Advanced Django CMS',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    url='https://www.django-cms.org/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'Django>=1.6,<1.8',
        'django-classy-tags>=0.5',
        'html5lib',
        'django-treebeard==3.0',
        'django-sekizai>=0.7',
        'djangocms-admin-style'
    ],
    extras_require={
        'south': ['south>=1.0.0'],
    },
    packages=find_packages(exclude=["project", "project.*"]),
    include_package_data=True,
    zip_safe=False,
    test_suite='runtests.main',
)
