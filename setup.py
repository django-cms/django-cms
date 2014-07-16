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
        'Django>=1.4',
        'django-classy-tags>=0.5',
        'south>=0.7.2',
        'html5lib',
        'django-mptt==0.5.2,==0.6,==0.6.1',
        'django-sekizai>=0.7',
        'djangocms-admin-style'
    ],
    tests_require=[
        'django-reversion==1.8.1',
        'Pillow==2.5.0',
        'Sphinx==1.2.2',
        'Jinja2==2.7.3',
        'Pygments==1.6',
        'dj-database-url==0.3.0',
        'django-hvad',
        'djangocms-text-ckeditor>=2.1.1',
        'djangocms-column',
        'djangocms-style',
    ],
    packages=find_packages(exclude=["project", "project.*"]),
    include_package_data=True,
    zip_safe=False,
    test_suite='runtests.main',
)
