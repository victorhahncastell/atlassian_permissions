#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import sys
from controller.cli import CliController


def main():
    if sys.version_info < (3, 4):
        raise RuntimeError("must use python 3.4 or greater")
        # TODO: maybe 3.2 works as well...

    cli = CliController.run()
    # if we ever get a GUI or something, place some logic here to decide which Controller to use


if __name__ == '__main__':
    main()
