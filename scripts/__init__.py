import importlib


def main(argv):
    entryutil = importlib.import_module(__name__.split('.')[0] + ".share.entryutil")
    return entryutil.entry(modules, __name__, __file__, argv)


modules = {
    "setup": "Setup the dev tools",
    "lint": "Run linter of the scripts"
}
