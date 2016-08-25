from codecs import open
from setuptools import find_packages, setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bonsai-cli',
    version='0.3.2',
    description='A python library for making API calls to Bonsai BRAIN.',
    long_description=long_description,
    url='http://github.com/BonsaiAI/bonsai-cli',
    author='Bonsai Engineering',
    author_email='opensource@bons.ai',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: BSD License',
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
        'bonsai_config==0.2.0',
    ],
    dependency_links=[
        # Temporary until we get bonsai-config on PyPI
        ('git+https://github.com/BonsaiAI/bonsai-config.git'
            '#egg=bonsai-config-0.2.0'),
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'bonsai=bonsai_cli.bonsai:main',
        ],
    }
    )
