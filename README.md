Bonsai CLI
==========
A python library for making API calls to Bonsai BRAIN.

Installation
------------

Install the latest stable from PyPI:
```
$ pip install bonsai-cli
```

Install the latest in-development version:
```
$ pip install https://github.com/BonsaiAI/bonsai-cli
```

Usage
-----
After first install, or when authentication credentials need to be refreshed:
```
$ bonsai configure
```
Load a new or existing brain and initiate training:
```
$ bonsai brain load brain_name /path/to/file.ink
$ bonsai brain train brain_name
```
Load an existing brain and deploy it for production use:
```
$ bonsai brain load brain_name /path/to/file.ink
$ bonsai brain deploy brain_name
```
