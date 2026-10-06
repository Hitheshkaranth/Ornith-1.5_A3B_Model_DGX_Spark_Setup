import heapq


class _TrieNode:
    __slots__ = ("children", "end", "heap")

    def __init__(self):
        self.children = {}
        self.end = False
        self.heap = []


class Autocomplete:
    """Case-insensitive autocomplete backed by a trie.

    Each trie node carries a lazy-deletion max-heap (stored as a min-heap of
    negative weights) of every word that passes through it. The heap gives the
    top-k highest-weight words for any prefix without scanning all stored words.
    """

    __slots__ = ("_root", "_weights")

    def __init__(self):
        self._root = _TrieNode()
        self._weights = {}

    def _validate(self, word, weight):
        if not isinstance(word, str) or word == "":
            raise ValueError("word must be a non-empty string")
        if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
            raise ValueError("weight must be a positive integer")

    def add(self, word, weight=1):
        self._validate(word, weight)
        w = word.lower()

        self._weights[w] = self._weights.get(w, 0) + weight
        total = self._weights[w]

        node = self._root
        heapq.heappush(node.heap, (-total, w))
        for ch in w:
            node = node.children.setdefault(ch, _TrieNode())
            heapq.heappush(node.heap, (-total, w))
        node.end = True

    def remove(self, word):
        w = word.lower()
        if w not in self._weights:
            return False
        del self._weights[w]

        path = [(self._root, None)]
        node = self._root
        for ch in w:
            nxt = node.children.get(ch)
            if nxt is None:
                break
            path.append((nxt, ch))
            node = nxt

        if len(path) > 1:
            path[-1][0].end = False
            i = len(path) - 1
            while i >= 1:
                n, ch = path[i]
                if not n.children and not n.end:
                    del path[i - 1][0].children[ch]
                    i -= 1
                else:
                    break

        return True

    def weight(self, word):
        return self._weights.get(word.lower(), 0)

    def suggest(self, prefix, k=5):
        if k <= 0:
            return []

        node = self._root
        for ch in prefix.lower():
            node = node.children.get(ch)
            if node is None:
                return []

        heap = node.heap
        result = []
        seen = set()
        popped = []

        while len(result) < k and heap:
            item = heapq.heappop(heap)
            popped.append(item)
            neg_weight, word = item
            cur = self._weights.get(word)
            if cur is None or cur <= 0 or -neg_weight != cur:
                continue
            if word in seen:
                continue
            seen.add(word)
            result.append(word)

        for item in popped:
            neg_weight, word = item
            cur = self._weights.get(word)
            if cur is not None and cur > 0 and -neg_weight == cur:
                heapq.heappush(heap, item)

        return result

    def __len__(self):
        return len(self._weights)

    def __contains__(self, word):
        return word.lower() in self._weights
