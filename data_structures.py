# data_structures.py

class DynamicArray:
    """
    A simple dynamic array (vector) implementation in Python.
    Internally uses a fixed-size list and resizes when needed.
    """
    def __init__(self, capacity=2):
        self.capacity = capacity
        self.size = 0
        self.data = [None] * capacity

    def __len__(self):
        return self.size

    def _resize(self, new_cap):
        new_data = [None] * new_cap
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data
        self.capacity = new_cap

    def append(self, value):
        if self.size == self.capacity:
            self._resize(2 * self.capacity)
        self.data[self.size] = value
        self.size += 1

    def get(self, index):
        if index < 0 or index >= self.size:
            raise IndexError("DynamicArray index out of range.")
        return self.data[index]

    def set(self, index, value):
        if index < 0 or index >= self.size:
            raise IndexError("DynamicArray index out of range.")
        self.data[index] = value

    def to_list(self):
        """Utility to convert the dynamic array to a normal Python list."""
        return [self.data[i] for i in range(self.size)]


class SinglyLinkedList:
    """
    A singly linked list with basic insert and traversal.
    """

    class _Node:
        def __init__(self, value):
            self.value = value
            self.next = None

    def __init__(self):
        self.head = None
        self._size = 0

    def __len__(self):
        return self._size

    def insert_at_head(self, value):
        new_node = self._Node(value)
        new_node.next = self.head
        self.head = new_node
        self._size += 1

    def insert_at_tail(self, value):
        new_node = self._Node(value)
        if self.head is None:
            self.head = new_node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = new_node
        self._size += 1

    def to_list(self):
        result = []
        cur = self.head
        while cur:
            result.append(cur.value)
            cur = cur.next
        return result


class Stack:
    """
    A stack implemented with a dynamic array internally.
    """
    def __init__(self):
        self._da = DynamicArray()

    def push(self, item):
        self._da.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("Pop from empty stack")
        top_item = self._da.get(len(self._da) - 1)
        # We can't truly "remove" from the dynamic array easily,
        # but we'll just reduce size logically:
        self._da.size -= 1
        return top_item

    def peek(self):
        if self.is_empty():
            return None
        return self._da.get(len(self._da) - 1)

    def is_empty(self):
        return len(self._da) == 0

    def __len__(self):
        return len(self._da)


class BytePairEncoder:
    """
    A simplified Byte Pair Encoding (BPE) compressor and decompressor.
    This is a demonstration of a custom compression technique.
    """

    @staticmethod
    def _get_stats(text):
        """
        Returns a dictionary of pairs => frequency.
        """
        stats = {}
        for i in range(len(text) - 1):
            pair = (text[i], text[i + 1])
            stats[pair] = stats.get(pair, 0) + 1
        return stats

    @staticmethod
    def compress(data, num_merges=10):
        """
        Perform a certain number of merges (num_merges) on the data.
        Returns (compressed_data, merges_map).
        merges_map is used for decompression.
        """
        text = list(data)  # treat data as a list of characters
        merges_map = []

        for _ in range(num_merges):
            stats = BytePairEncoder._get_stats(text)
            if not stats:
                break
            # find best pair
            best_pair = max(stats, key=stats.get)
            merges_map.append("".join(best_pair))

            # merge occurrences of best_pair
            merged_text = []
            i = 0
            while i < len(text):
                if i < len(text) - 1 and (text[i], text[i+1]) == best_pair:
                    merged_text.append("".join(best_pair))  # single token
                    i += 2
                else:
                    merged_text.append(text[i])
                    i += 1

            text = merged_text

        # compressed data is a list of tokens
        return " ".join(text), merges_map

    @staticmethod
    def decompress(compressed_data, merges_map):
        """
        Reverse the merges: each item in merges_map is a token that should be split.
        We'll do it in reverse order of merges.
        """
        tokens = compressed_data.split(" ")
        # merges_map is in the order they were created, so revert in reverse
        for pair_str in reversed(merges_map):
            new_tokens = []
            for token in tokens:
                # if token is the merged pair, split into individual chars
                if token == pair_str:
                    new_tokens.extend(list(token))  # separate characters
                else:
                    new_tokens.append(token)
            tokens = new_tokens
        return "".join(tokens)

