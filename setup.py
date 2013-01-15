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
        'Django>=1.3.1,<1.5',
        'django-classy-tags>=0.3.4.1',
        'south>=0.7.2',
        'html5lib',
        'django-mptt>=0.5.1,<0.5.3',
        'django-sekizai>=0.6.1',
    ],
    tests_require=[
        'django-reversion>=1.6',
        'Pillow==1.7.7',
        'Sphinx==1.1.3',
        'Jinja2==2.6',
        'Pygments==1.5',
        'dj-database-url==0.2.1',
    ],
    packages=find_packages(exclude=["project","project.*"]),
    include_package_data=True,
    zip_safe = False,
    test_suite = 'runtests.main',
)
