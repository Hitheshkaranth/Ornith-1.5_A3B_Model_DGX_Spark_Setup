"""Run a hidden unittest file against a workspace and print a JSON summary.

usage: python run_hidden.py <workspace_dir> <test_file>
"""
import importlib.util
import io
import json
import os
import sys
import unittest


def method_id(t):
    return getattr(t, "test_case", t).id()


def main():
    ws, test_file = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    os.chdir(ws)
    sys.path.insert(0, ws)
    out = {"import_error": None}
    try:
        spec = importlib.util.spec_from_file_location("_hidden_test", test_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
    except BaseException as e:  # solution missing / syntax error / import-time crash
        out.update(tests=0, passed=0, failed=[], import_error="%s: %s" % (type(e).__name__, e))
        print(json.dumps(out)); return
    all_ids = [t.id() for t in _flatten(suite)]
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    bad = {method_id(t) for t, _ in res.failures + res.errors}
    if any(not i.startswith("_hidden_test.") for i in bad):  # class/module-level error
        bad = set(all_ids)
    out.update(tests=len(all_ids), passed=len([i for i in all_ids if i not in bad]), failed=sorted(bad))
    print(json.dumps(out))


def _flatten(s):
    for t in s:
        if isinstance(t, unittest.TestSuite):
            yield from _flatten(t)
        else:
            yield t


if __name__ == "__main__":
    main()
