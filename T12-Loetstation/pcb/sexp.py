"""Minimaler S-Expression-Parser/Writer fuer KiCad-Dateien."""
import re

_TOKEN = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)', re.S)


class Sym(str):
    """Unquoted Atom (Schluesselwort/Zahl)."""


def parse(text):
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("Parse-Fehler bei %d" % pos)
        tok = m.group(1)
        pos = m.end()
        if tok == "(":
            stack.append([])
        elif tok == ")":
            lst = stack.pop()
            stack[-1].append(lst)
        elif tok.startswith('"'):
            stack[-1].append(tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            stack[-1].append(Sym(tok))
    return stack[0][0]


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(node, indent=0):
    """Schreibt Liste als S-Expression (Strings quoted, Sym unquoted)."""
    tab = "\t" * indent
    if not isinstance(node, list):
        if isinstance(node, Sym):
            return str(node)
        if isinstance(node, bool):
            return "yes" if node else "no"
        if isinstance(node, (int, float)):
            return fmt(node)
        return q(node)
    head = [str(node[0])] if node else []
    rest = node[1:]
    simple = all(not isinstance(x, list) for x in rest)
    if simple:
        return tab + "(" + " ".join(head + [dump(x) for x in rest]) + ")"
    out = tab + "(" + " ".join(head + [dump(x) for x in rest if not isinstance(x, list)])
    for x in rest:
        if isinstance(x, list):
            out += "\n" + dump(x, indent + 1)
    out += "\n" + tab + ")"
    return out


def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def find(node, key):
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
