"""
subdown2
----------

subdown2 is a script that automatically downloads all images from a certain subreddit.
"""

from setuptools import setup, find_packages

setup(
    name='subdown2',
    version='0.8.0',
    author='Kunal Mehta',
    author_email='legoktm@gmail.com',
    packages=find_packages(),
    url='https://github.com/legoktm/subdown2/',
    license='MIT License',
    description='A script that automatically downloads all images from a certain subreddit.',
    long_description=open('README.md').read(),
    install_requires=open('requirements.txt').read().split("\n"),
    package_data={
        '': ['*.txt', '*.md']
    },
    classifiers=[
      'License :: OSI Approved :: MIT License',
      'Operating System :: MacOS :: MacOS X',
      'Operating System :: Microsoft :: Windows',
      'Operating System :: POSIX',
      'Intended Audience :: End Users/Desktop',
      'Environment :: Console',
      'Programming Language :: Python',
    ],
    entry_points = {
        'console_scripts': [
            'subdown2 = subdown2:main'
        ],
    }
)
