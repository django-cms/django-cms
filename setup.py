from setuptools import setup, find_packages
import os, fnmatch
import cms

media_files = []

for dirpath, dirnames, filenames in os.walk(os.path.join('cms', 'media')):
    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        failed = False
        for pattern in ('*.py', '*.pyc', '*~', '.*', '*.bak', '*.swp*'):
            if fnmatch.fnmatchcase(filename, pattern):
                failed = True
        if failed:
            continue
        media_files.append(os.path.join(*filepath.split(os.sep)[1:]))
        
if cms.VERSION[-1] == 'final':
    CLASSIFIERS = ['Development Status :: 5 - Stable']
elif 'beta' in cms.VERSION[-1]:
    CLASSIFIERS = ['Development Status :: 4 - Beta']
else:
    CLASSIFIERS = ['Development Status :: 3 - Alpha']

CLASSIFIERS += [
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
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    url='http://www.django-cms.org/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'Django>=1.2',
        'django-classy-tags>=0.2.2',
    ],
    packages=find_packages(exclude=["example", "example.*"]),
    package_data={
        'cms': [
            'templates/admin/*.html',
            'templates/admin/cms/mail/*.html',
            'templates/admin/cms/mail/*.txt',
            'templates/admin/cms/page/*.html',
            'templates/admin/cms/page/*/*.html',
            'templates/cms/*.html',
            'templates/cms/*/*.html',
            'plugins/*/templates/cms/plugins/*.html',
            'plugins/*/templates/cms/plugins/*/*.html',
            'plugins/*/templates/cms/plugins/*/*.js',
            'locale/*/LC_MESSAGES/*',
        ] + media_files,
        'example': [
            'media/css/*.css',
            'media/img/*.jpg',
            'templates/*.html',
            'sampleapp/media/sampleapp/img/gift.jpg',
            'sampleapp/templates/sampleapp/*.html',
        ],
        'menus': [
            'templates/menu/*.html',
        ],
    },
    zip_safe = False
)
