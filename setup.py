from setuptools import setup, find_packages
import os
import cms
media_files = []

for dirpath, dirnames, filenames in os.walk('cms/media'):
    media_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

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
    classifiers=[
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
    ],
    requires=[
        'django (>1.1.0)',
    ],
    
    packages=find_packages(),
    package_dir={
        'cms': 'cms',
        'mptt': 'mptt',
        'publisher': 'publisher',
    },
    data_files = media_files,
    package_data = {
        'cms': [
            'templates/admin/cms/mail/*.html',
            'templates/admin/cms/mail/*.txt',
            'templates/admin/cms/page/*.html',
            'templates/admin/cms/page/*/*.html',
            'templates/cms/*.html',
            'plugins/*/templates/cms/plugins/*.html',
            'plugins/*/templates/cms/plugins/*/*.html',
            'plugins/*/templates/cms/plugins/*/*.js',
            'locale/*/LC_MESSAGES/*'
        ]
    },
    zip_safe = False
)
