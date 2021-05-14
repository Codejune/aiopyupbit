# !/usr/bin/python
# -*- coding: utf-8 -*-
import setuptools

install_requires = [
    'pandas>=1.2.4',
    'aiohttp>=3.7.4',
    'pyjwt>=2.1.0',
    'pytz>=2020.5',
    'python-dateutil>=2.8.1',
    'six>=1.15.0'
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='aiopyupbit',
    version='0.1.7',
    author='Codejune',
    author_email='kbj9704@gmail.com',
    description='python wrapper for upbit API for asyncio and Python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/codejune/aiopyupbit',
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
