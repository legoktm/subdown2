"""
subdown.py
----------

subdown.py is a tool for downloading images from reddit.
"""

from setuptools import setup, find_packages

setup(
    name='subdown2',
    version='0.2',
    author='Kunal Mehta',
    author_email='legoktm@gmail.com',
    packages=find_packages(),
    url='http://github.com/legoktm/subdown2/',
    license='LICENSE.txt',
    description='A script that automatically downloads all images from a certain subreddit.',
    long_description=open('README.md').read(),
    install_requires=open('requirements.txt').read().split("\n"),
    package_data={
        '': ['*.txt', '*.md']
    },
    entry_points = {
        'console_scripts': [
            'subdown2 = subdown2:main'
        ],
    }
)
