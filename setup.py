#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
# get the requirements from the requirements.txt
requirements = [line.strip()
                for line in open('requirements.txt').readlines()
                if line.strip() and not line.startswith('#')]
# get the test requirements from the test_requirements.txt
test_requirements = [line.strip()
                     for line in
                     open('dev-requirements.txt').readlines()
                     if line.strip() and not line.startswith('#')]

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
version = open('.VERSION').read()


setup(
    name='''enpassreadercli''',
    version=version,
    description='''A cli to access enpass 6 encrypted databases and read, list and search values.''',
    long_description=readme + '\n\n' + history,
    author='''Costas Tyfoxylos''',
    author_email='''costas.tyf@gmail.com''',
    url='''https://github.com/costastf/enpassreadercli''',
    packages=find_packages(where='.', exclude=('tests', 'hooks', '_CI*')),
    package_dir={'''enpassreadercli''':
                 '''enpassreadercli'''},
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    python_requires='>=3.11',
    zip_safe=False,
    keywords='''enpassreadercli enpass''',
    entry_points = {
                   'console_scripts': [
                       # enable this to automatically generate a script in /usr/local/bin called myscript that points to your
                       #  enpassreadercli.enpassreadercli:main method
                       'enpass-reader = enpassreadercli.enpassreadercli:main'
                   ]},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        ],
    test_suite='tests',
    tests_require=test_requirements
)
