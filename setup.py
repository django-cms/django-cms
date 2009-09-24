from setuptools import setup, find_packages
import os

media_files = []

for dirpath, dirnames, filenames in os.walk('cms/media'):
    media_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name='django-cms',
    version='2.0.0.alpha',
    description='An Advanced Django CMS',
    url='http://github.com/digi604/django-cms-2.0/',
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
)
