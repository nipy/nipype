"""
Handles custom functions used in Function interface. Future imports
are avoided to keep namespace as clear as possible.
"""

import inspect
from textwrap import dedent


def getsource(function):
    """Returns the source code of a function"""
    return dedent(inspect.getsource(function))


def create_function_from_source(function_source, imports=None):
    """Return a function object from a function source

    Parameters
    ----------
    function_source : unicode string
        unicode string defining a function
    imports : list of strings
        list of import statements in string form that allow the function
        to be executed in an otherwise empty namespace
    """
    ns = {}
    import_keys = []

    try:
        if imports is not None:
            for statement in imports:
                exec(statement, ns)
            import_keys = list(ns.keys())
        exec(function_source, ns)

    except Exception as e:
        msg = f"Error executing function\n{function_source}\n"
        msg += (
            "Functions in connection strings have to be standalone. "
            "They cannot be declared either interactively or inside "
            "another function or inline in the connect string. Any "
            "imports should be done inside the function."
        )
        raise RuntimeError(msg) from e
    ns_funcs = list(set(ns) - set(import_keys + ["__builtins__"]))
    assert len(ns_funcs) == 1, "Function or inputs are ill-defined"
    func = ns[ns_funcs[0]]
    return func
