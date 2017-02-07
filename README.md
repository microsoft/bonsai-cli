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

Alpha users:
1 - On the alpha site, generate an Access Key.
2 - Patch `~/.bonsai` with:
```
bonsai switch alpha --url https://alpha-api.int.bons.ai
bonsai configure
```

Load a new or existing brain and initiate training:
```
$ bonsai create brain_name
$ bonsai load
$ bonsai train start
```
