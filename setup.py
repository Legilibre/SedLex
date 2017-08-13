from setuptools import setup

setup(
    name='SedLex',
    version='0.1',
    install_requires=[
        'html5lib',
        'beautifulsoup4',
        'requests',
        'jinja2',
        'python-gitlab'
    ],
    scripts=[
        'bin/sedlex'
    ]
)
