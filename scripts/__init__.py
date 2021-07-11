import importlib


def main(argv):
    if argv and '.' in argv[0]:
        dotIdx = argv[0].rfind('.')
        moduleName = argv[0][0: dotIdx]
        funcName = argv[0][dotIdx + 1:]
        module = importlib.import_module(__name__.split('.')[0] + '.' + moduleName)
        getattr(module, funcName)(*argv[1:])
        return 0
    entryutil = importlib.import_module(__name__.split('.')[0] + ".share.entryutil")
    return entryutil.entry(modules, __name__, __file__, argv)


modules = {
    "addpath": "Add given path to user env path list",
    "adminCmd": "Open a admin cmd window",
    "delpath": "delete given path from user env path list",
    "lint": "Run linter of the scripts",
    "setup": "Setup the dev tools",
}
