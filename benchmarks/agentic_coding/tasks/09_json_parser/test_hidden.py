import unittest, json, random, pathlib
from minijson import loads

VALID = ['0', '-0', '12', '-3.5', '1e3', '1E-2', '2.5e+3', '"abc"', '""', 'true', 'false', 'null', '[]', '{}',
         ' [1, 2 ,3] ', '{"a":1,"b":[true,false,null],"c":{"d":"e"}}',
         r'"esc \" \\ \/ \b \f \n \r \t"', r'"é中"', r'"😀"', r'"😀x"', '[[[[]]]]',
         '{"a":1,"a":2}', '"unicode é 中 \U0001F600"', '[1.5e10, -0.0, 0.25, 1E400]', '{"":""}',
         '  \n\t{ "x" : [ ] }  \r\n', '-12.5e-3', '[0,1,-1]']

INVALID = ['', ' ', '01', '1.', '.5', '+1', '[1,]', '{"a":1,}', "{'a':1}", '{"a" 1}', '[1 2]', '"abc', r'"\x"',
           r'"\u12"', r'"\u12G4"', 'tru', 'nul', 'NaN', 'Infinity', '-Infinity', '[1]]', '{"a":1}x', '"a\nb"', '"tab\there"',
           '-', '1e', '1e+', '{1:2}', '[', '{"a":}', '--1', '0x10', '[,1]', '{,}', 'True', '"\\']


def gen(rnd, depth=0):
    k = rnd.randint(0, 7 if depth < 4 else 4)
    if k == 0: return rnd.randint(-10**12, 10**12)
    if k == 1: return rnd.uniform(-1e6, 1e6)
    if k == 2: return ''.join(rnd.choice('ab"\\/\n\té中\U0001F600 \x01') for _ in range(rnd.randint(0, 8)))
    if k == 3: return rnd.choice([True, False, None])
    if k == 4: return rnd.random() * 10 ** rnd.randint(-30, 30)
    if k in (5, 6): return [gen(rnd, depth + 1) for _ in range(rnd.randint(0, 4))]
    return {''.join(rnd.choice('kxyé') for _ in range(rnd.randint(0, 3))): gen(rnd, depth + 1) for _ in range(rnd.randint(0, 4))}


class T(unittest.TestCase):
    def same(self, s):
        self.assertEqual(json.dumps(loads(s)), json.dumps(json.loads(s)), s)

    def test_valid(self):
        for s in VALID:
            with self.subTest(s=s): self.same(s)

    def test_invalid(self):
        for s in INVALID:
            with self.subTest(s=s):
                with self.assertRaises(ValueError): loads(s)

    def test_types(self):
        self.assertIs(type(loads('1')), int); self.assertIs(type(loads('1.0')), float); self.assertIs(type(loads('1e2')), float)

    def test_nested(self):
        s = '[' * 150 + ']' * 150; self.same(s)

    def test_random_roundtrip(self):
        rnd = random.Random(11)
        for _ in range(300):
            v = gen(rnd)
            s = json.dumps(v, ensure_ascii=rnd.random() < 0.5, indent=rnd.choice([None, 2]))
            self.same(s)

    def test_no_json_module(self):
        src = pathlib.Path(__import__('minijson').__file__).read_text(encoding="utf-8")
        self.assertNotIn('import json', src); self.assertNotIn('from json', src)
