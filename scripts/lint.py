import os
import argparse

from scripts.share.util import gs
from scripts.share.util import printf
from scripts.share.util import call


def main(argv):
    # Parse the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-linter", help="Choose the linters (separated by ,)", default="all")

    args = parser.parse_args(argv)

    supportedLinters = ["pylint", "flake8"]
    printf("Supported linters: " + ','.join(supportedLinters))
    if args.linter != "all":
        linters = args.linter.split(',')
    else:
        linters = supportedLinters

    os.chdir(str(gs.GitDir))
    for linter in linters:
        if linter in supportedLinters:
            printf("Running linter %s..." % linter, color=gs.GREEN)
            ret = call("python -m %s scripts" % linter)
            print(ret[0])
        else:
            printf("Unsupported linter %s!" % linter, color=gs.RED)
