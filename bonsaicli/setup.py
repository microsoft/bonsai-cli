from codecs import open
from setuptools import find_packages, setup

from bonsai_cli import __version__

setup(
    name='bonsai-cli',
    version=__version__,
    description='A python library for making API calls to Bonsai BRAIN.',
    long_description=open('README.rst').read(),
    url='https://github.com/BonsaiAI/bonsai-cli',
    author='Bonsai Engineering',
    author_email='opensource@bons.ai',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Natural Language :: English'
    ],
    keywords='bonsai',
    install_requires=[
        'click>=6.6',
        'requests>=2.11',
        'tabulate>=0.7.5',
        'websocket-client>=0.40.0',
        'bonsai-ai>=2.0.4',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'bonsai=bonsai_cli.bonsai:main',
        ],
    }
    )
