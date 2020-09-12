from scripts.share.util import gs
from scripts.share.util import printf

from scripts.share.winutil import isUserAdmin
from scripts.share.winutil import runAsAdmin


def main(argv):
    assert not argv
    if not isUserAdmin():
        printf("Current user is not an admin!")
    runAsAdmin("cmd /k cd /d %s" % str(gs.GitDir/"bin"), wait=False, show=True)
