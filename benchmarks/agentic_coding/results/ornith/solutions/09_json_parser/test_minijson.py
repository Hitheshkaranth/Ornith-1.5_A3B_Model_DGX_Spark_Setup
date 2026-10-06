"""Adversarial test comparing minijson.loads against json.loads."""
import json
import minijson

VALID_CASES = [
    "true", "false", "null",
    "0", "-0", "123", "-456", "1.5", "-0.0", "1e3", "1E-3", "2.5e+10",
    '""', '"hello"', '"with \\\\ slash"', '"tab\\ttab"', '"new\\nline"',
    '"unicode \\u00e9"', '"quote \\\\u0022 in"', '"emoji \\ud83d\\ude00"',
    '"mix \\ud800\\udc00a"',
    "[]", "{}",
    "[1, 2, 3]", '{"a": 1, "b": 2}', '{"a": [1, {"b": [2, 3]}], "c": {}}',
    "  1  ", "\n\t[1,\n2 ]\t", '  { "a" : 1 , "b": [ ] }  ',
    '{"a": 1, "b": 2, "a": 3}',
    "[" * 50 + "]" * 50,
    '"café"', "99999999999999999999999999999999",
    '{"x": [true, false, null, -1.5e-3], "y": {"z": {"w": []}}}',
]

SURROGATE_CASES = {
    '"\\uD800"': '\ud800',
    '"\\uDC00"': '\udc00',
    '"\\ud83d\\ude00"': '\U0001f600',
    '"\\uD800x"': '\ud800x',
    '"\\u0000\\u0020"': '\x00 ',
}

INVALID_CASES = [
    "", "   ", '"unterminated', '"\\x',
    "nul", "tru", "fals", "1..2", ".5", "1.",
    "1.0a", "01", "+1", "1e", "1e+", "-.5", "-1-1",
    "'single quoted'", '{"a": 1,}', '{1: 2}', "[1, 2,]",
    '{"a": 1, "b"}', "0x1F", "1, 2",
    "[1 2]", "truex", '"\\u12\\uX123"', '[,]', '"\\u"', '1.e5',
    '{"a": ]}', '  { : 1 }', '"\x00raw"',
]

# Strict RFC 8259 rejects these even though json.loads (lenient) accepts them.
STRICT_REJECTS = ["NaN", "Infinity", "-Infinity"]


def check_valid(s):
    expected = json.loads(s)  # must NOT raise for valid inputs
    got = minijson.loads(s)
    assert got == expected, f"mismatch for {s!r}: {got!r} != {expected!r}"
    assert type(got) is type(expected), f"type mismatch for {s!r}"


def check_surrogate(s, expected):
    got = minijson.loads(s)
    assert got == expected, f"surrogate mismatch {s!r}: {got!r} != {expected!r}"


def check_invalid(s):
    try:
        json.loads(s)
        json_accepts = True
    except ValueError:
        json_accepts = False
    except Exception:
        json_accepts = False

    try:
        got = minijson.loads(s)
    except ValueError:
        assert not json_accepts, f"{s!r} raised ValueError but json accepts it"
        return
    except Exception as exc:
        raise AssertionError(f"{s!r} raised non-ValueError: {exc}")

    assert not json_accepts, f"expected ValueError for {s!r}, got {got!r}"


def check_strict_reject(s):
    """JSON leniently accepts NaN/Infinity; strict parser must reject."""
    try:
        got = minijson.loads(s)
    except ValueError:
        return
    except Exception as exc:
        raise AssertionError(f"{s!r} raised non-ValueError: {exc}")
    raise AssertionError(f"{s!r} should raise ValueError, got {got!r}")


def main():
    for s in VALID_CASES:
        check_valid(s)
    for s, expected in SURROGATE_CASES.items():
        check_surrogate(s, expected)
    for s in STRICT_REJECTS:
        check_strict_reject(s)
    for s in INVALID_CASES:
        check_invalid(s)

    print(f"OK: {len(VALID_CASES)} valid + {len(SURROGATE_CASES)} surrogate "
          f"+ {len(STRICT_REJECTS)} strict + {len(INVALID_CASES)} invalid "
          f"cases passed.")


if __name__ == "__main__":
    main()