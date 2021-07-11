import argparse
import os

from scripts.share.util import gs
from scripts.share.util import printf

from scripts.share.winutil import regQuery
from scripts.share.winutil import regAdd
from scripts.share.winutil import notifyEnvChange


def main(argv):
    # Parse the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-path", help="The path to add")

    args = parser.parse_args(argv)

    if not args.path:
        args.path = os.getcwd()

    userPath = regQuery(r"HKCU\Environment", "Path")[0]
    pathList = [p.strip() for p in userPath.split(';')]
    if args.path not in pathList:
        pathList.insert(0, args.path)
        regAdd(r"HKCU\Environment", "Path", ";".join(pathList))
        notifyEnvChange()
        printf("Added %s to user env path" % args.path, color=gs.GREEN)
    else:
        printf("%s was already in user env path" % args.path, color=gs.YELLOW)
