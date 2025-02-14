#!/usr/bin/env python

"""The setup script."""
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test

def run_tests(*args):
    from arcsde.tests import run_tests
    errors = run_tests()
    if errors:
        sys.exit(1)
    else:
        sys.exit(0)

test.run_tests = run_tests


with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
        'Django>=3.2.18,<5.0',
    ]

test_requirements = [ ]

setup(
    author="powderflask",
    author_email='powderflask@gmail.com',
    python_requires='>=3.10, <4',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ],
    description="Abstractions and base classes for creating django models from Arc SDE feature tables.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords='django arc sde',
    name='django-arcsde',
    packages=find_packages(include=['arcsde*']),
    test_suite='arcsde.tests',
    tests_require=test_requirements,
    url='https://github.com/powderflask/django-arcsde',
    version='1.4.5',
    zip_safe=False,
)
