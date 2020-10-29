# pyright:reportUnknownArgumentType =false
from codecs import open
from setuptools import find_packages, setup

from bonsai_cli import __version__

setup(
    name="bonsai-cli",
    version=__version__,
    description="A python library for making API calls to the Bonsai Platform.",
    long_description=open("README.rst").read(),
    url="https://github.com/BonsaiAI/bonsai-cli",
    author="Microsoft Bonsai",
    author_email="opensource@bons.ai",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Natural Language :: English",
    ],
    keywords="bonsai",
    install_requires=[
        "click>=7.1.2",
        "requests>=2.11",
        "tabulate>=0.7.5",
        "websocket-client>=0.40.0",
        "msal-extensions>=0.1.3",
        "opencensus-ext-azure>=1.0.4",
    ],
    packages=find_packages(),
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "bonsai=bonsai_cli.commands.bonsai:main",
        ],
    },
)
