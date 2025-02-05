from setuptools import setup, find_packages

setup(
    name="nkuwiki",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        open("etl/crawler/requirements.txt").read().splitlines()
    ]
) 