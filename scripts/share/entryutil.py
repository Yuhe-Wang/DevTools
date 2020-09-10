import importlib


def entry(modules, name, file, argv):
    ret = 0
    if argv:
        module = argv[0]
        passArgv = argv[1:]
    else:
        module = "-h"
        passArgv = []

    shortcutMarker = "=> "
    if module in modules:
        description = modules[module]
        if description.startswith("=> "):
            # It's a short cut
            extraArgv = description[len(shortcutMarker):].split()
            module = extraArgv[0]
            assert module in modules  # The shortcut target must in modules
            assert not modules[module].startswith(shortcutMarker)  # No chained shortcut is allowed
            passArgv = extraArgv[1:] + passArgv  # May insert extra parameters
        ret = importlib.import_module(name + '.' + module).main(passArgv)
    else:
        if module in ("-h", "--help"):
            printHelp(modules, file)
            if "default" in modules:
                assert modules["default"] in modules
                print("\n---------------- Default module: [%s] ----------------\n" % modules["default"])
                ret = importlib.import_module(name + '.' + modules["default"]).main(["-h"])
        else:
            if "default" in modules:
                assert modules["default"] in modules
                ret = importlib.import_module(name + '.' + modules["default"]).main(argv)
            else:
                print("Unrecognized arguments! Please read the following help.\n")
                printHelp(modules, file)
    return ret


def printHelp(modules, file):
    maxWidth = max([len(m) for m in modules if m != "default"])
    # Merge shortcut with the target
    shortcutMarker = "=> "
    dt = dict()
    for m in modules:
        if m == "default":
            continue
        description = modules[m]
        item = (m, description)
        if description.startswith("=> "):
            # It's a short cut
            m = description[len(shortcutMarker):].split()[0]
            assert m in modules  # The shortcut target must in modules
            assert not modules[m].startswith(shortcutMarker)  # No chained shortcut is allowed
        if m in dt:
            if item[0] == m:  # The main item should stay ahead
                dt[m] = [item] + dt[m]
            else:
                dt[m].append(item)
        else:
            dt[m] = [item]

    print("Help for [ %s ]:\n" % file)
    print("%{}s: Print this help and exit".format(maxWidth) % "-h")
    for key in sorted(dt.keys()):
        for item in dt[key]:
            print("%{}s: %s".format(maxWidth) % (item[0], item[1]))
