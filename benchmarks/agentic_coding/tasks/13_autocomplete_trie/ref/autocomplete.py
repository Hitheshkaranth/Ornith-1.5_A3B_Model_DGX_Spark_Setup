class _Node:
    __slots__ = ("kids", "end")

    def __init__(self):
        self.kids = {}
        self.end = False


class Autocomplete:
    def __init__(self):
        self.root = _Node()
        self.w = {}

    def add(self, word, weight=1):
        if not isinstance(word, str) or not word:
            raise ValueError("word must be non-empty str")
        if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
            raise ValueError("weight must be positive int")
        word = word.lower()
        n = self.root
        for ch in word:
            n = n.kids.setdefault(ch, _Node())
        n.end = True
        self.w[word] = self.w.get(word, 0) + weight

    def remove(self, word):
        word = word.lower()
        if word not in self.w:
            return False
        del self.w[word]
        n = self.root
        for ch in word:
            n = n.kids[ch]
        n.end = False
        return True

    def weight(self, word):
        return self.w.get(word.lower(), 0)

    def suggest(self, prefix, k=5):
        if k <= 0:
            return []
        prefix = prefix.lower()
        n = self.root
        for ch in prefix:
            n = n.kids.get(ch)
            if n is None:
                return []
        found, stack = [], [(n, prefix)]
        while stack:
            node, s = stack.pop()
            if node.end:
                found.append(s)
            for ch, kid in node.kids.items():
                stack.append((kid, s + ch))
        found.sort(key=lambda x: (-self.w[x], x))
        return found[:k]

    def __len__(self):
        return len(self.w)

    def __contains__(self, word):
        return isinstance(word, str) and word.lower() in self.w
