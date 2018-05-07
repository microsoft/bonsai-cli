#!/usr/bin/env python3
"""
This file is the entrypoint for the bonsai cli tool when run directly
from within the brain repository. It should not be distributed with
the pip package. Run this file directly to perform API commands via the CLI.
"""

from bonsai_cli.bonsai import main

if __name__ != '__main__':
    raise RuntimeError("This file should not be imported")

main()
