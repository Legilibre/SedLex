from setuptools import setup

import os

template_files = []
for root, dirs, files in os.walk('sedlex/template'):
    for f in files:
        template_files.append(os.path.join(root, f).replace('sedlex/', ''))

setup(
    name='SedLex',
    version='0.1',
    install_requires=[
        'html5lib',
        'beautifulsoup4',
        'requests',
        'jinja2',
        'python-gitlab',
        'PyGithub'
    ],
    package_dir={
        'sedlex': 'sedlex'
    },
    package_data={
        'sedlex': template_files
    },
    packages=[
        'sedlex'
    ],
    # data_files=[('template', template_files)],
    scripts=[
        'bin/sedlex'
    ]
)
