"""
Script for checking alphabetical order of specs.

The script relies on Python introspection capabilities and on the fact that starting
from Python 3.7, dictionaries preserve insertion order.

Additional resources:
https://mail.python.org/pipermail/python-dev/2017-December/151283.html
https://docs.python.org/3.7/whatsnew/3.7.html
https://docs.python.org/3/library/stdtypes.html#dictionary-view-objects
"""
import glob
import importlib
import inspect
import re
import sys

SPECDIR = "./ccx_ocp_core/specs/"


class Colors:
    HEADER = "\033[95m"
    OKGREEN = "\033[92m"
    OKCYAN = "\033[96m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_violations(out_of_order):
    print(
        Colors.BOLD
        + Colors.OKCYAN
        + "\n\nThe following specs violate alphabetical order: \n\n"
        + Colors.ENDC
    )
    for k, v in out_of_order.items():
        print(
            Colors.BOLD
            + Colors.HEADER
            + Colors.UNDERLINE
            + "module: {}, spec class: {}".format(k, v[0])
            + Colors.ENDC
        )
        misordered_specs = v[1]
        ordered_specs = sorted(v[1])
        max_spec_length = max([len(spec) for spec in misordered_specs])
        for i in range(len(ordered_specs)):
            if ordered_specs[i] == misordered_specs[i]:
                print(
                    "  ---  "
                    + Colors.OKGREEN
                    + ordered_specs[i]
                    + " " * (max_spec_length - len(ordered_specs[i]))
                    + "\t\t\t"
                    + misordered_specs[i]
                    + Colors.ENDC
                )
            else:
                print(
                    "  ---  "
                    + Colors.OKGREEN
                    + ordered_specs[i]
                    + Colors.ENDC
                    + " " * (max_spec_length - len(ordered_specs[i]))
                    + "\t\t\t"
                    + Colors.FAIL
                    + misordered_specs[i]
                    + Colors.ENDC
                )
        print("\n\n")


def check_specs_order(specs_classes):
    misorder = False
    # specs added by SpecSetMeta to any spec class that inherits from SpecSet
    meta_class_specs = ["context_handlers", "registry"]
    out_of_order = {}
    for specs_module, specs_cls in specs_classes.items():
        specs = [
            spec
            for spec in specs_cls.__dict__
            if not spec.startswith("__")
            and not spec.endswith("__")
            and spec not in meta_class_specs
        ]
        if specs != sorted(specs):
            misorder = True
            out_of_order[specs_module] = [specs_cls, specs.copy()]
    if misorder:
        print_violations(out_of_order)
        sys.exit(-1)
    return 0


def retrieve_spec_classes(spec_modules):
    from insights.core.spec_factory import SpecSet

    specs_classes = {}
    for module in spec_modules:
        loaded_module = importlib.import_module(module)
        members = inspect.getmembers(
            loaded_module,
            lambda member: inspect.isclass(member)
            and inspect.getmodule(member).__name__ == loaded_module.__name__
            and SpecSet in inspect.getmro(member),
        )
        if not members:  # InstallGather does not inherit from SpecSet. Make sure it is included
            members = inspect.getmembers(
                loaded_module,
                lambda member: inspect.isclass(member)
                and inspect.getmodule(member).__name__ == loaded_module.__name__,
            )
        assert len(members) == 1
        specs_classes[loaded_module] = members[0][1]
    return specs_classes


def main():
    specs_modules = glob.glob(SPECDIR + "*.py")
    if specs_modules:
        specs_modules.remove(SPECDIR + "__init__.py")
        specs_modules = [module[2:-3] for module in specs_modules]
        specs_modules = [re.sub("/", ".", module) for module in specs_modules]
        check_specs_order(retrieve_spec_classes(specs_modules))


if __name__ == "__main__":
    main()
