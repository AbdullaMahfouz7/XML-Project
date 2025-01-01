# data_structures.py
# This file contains custom data structures often covered in a Data Structures course.
# It includes a DynamicArray, a SinglyLinkedList, a Stack, and a BytePairEncoder
# implementation for simple compression/decompression.

class DynamicArray:
    """
    A simple dynamic array (like a vector in C++).
    The underlying list resizes automatically if we exceed its capacity.
    """
    def __init__(self, capacity=2):
        self.capacity = capacity
        self.size = 0
        self.data = [None] * capacity

    def __len__(self):
        return self.size

    def _resize(self, new_cap):
        # Create a new list with the requested capacity and
        # copy over the existing elements.
        new_data = [None] * new_cap
        for i in range(self.size):
            new_data[i] = self.data[i]
        self.data = new_data
        self.capacity = new_cap

    def append(self, value):
        # Append a new value to the end. If there's no space, resize first.
        if self.size == self.capacity:
            self._resize(2 * self.capacity)
        self.data[self.size] = value
        self.size += 1

    def get(self, index):
        # Return the element at a certain index.
        # Raises an error if index is out of range.
        if index < 0 or index >= self.size:
            raise IndexError("DynamicArray index out of range.")
        return self.data[index]

    def set(self, index, value):
        # Modify the element at a certain index.
        if index < 0 or index >= self.size:
            raise IndexError("DynamicArray index out of range.")
        self.data[index] = value

    def to_list(self):
        # Convert the valid portion of the dynamic array into a regular Python list.
        return [self.data[i] for i in range(self.size)]


class SinglyLinkedList:
    """
    A singly linked list that supports insertion at the head or tail.
    Useful when we don't need random access but want efficient inserts.
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
        # Insert a new node at the start of the list.
        new_node = self._Node(value)
        new_node.next = self.head
        self.head = new_node
        self._size += 1

    def insert_at_tail(self, value):
        # Insert a new node at the end of the list.
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
        # Traverse the linked list and collect the values in a Python list.
        result = []
        cur = self.head
        while cur:
            result.append(cur.value)
            cur = cur.next
        return result


class Stack:
    """
    A stack implemented using our DynamicArray.
    We can push and pop items in O(1) amortized time.
    """
    def __init__(self):
        self._da = DynamicArray()

    def push(self, item):
        self._da.append(item)

    def pop(self):
        # Remove and return the top item. Raises an error if the stack is empty.
        if self.is_empty():
            raise IndexError("Pop from empty stack")
        top_item = self._da.get(len(self._da) - 1)
        self._da.size -= 1  # we effectively remove the last element
        return top_item

    def peek(self):
        # Return the top item without removing it.
        if self.is_empty():
            return None
        return self._da.get(len(self._da) - 1)

    def is_empty(self):
        return len(self._da) == 0

    def __len__(self):
        return len(self._da)


class BytePairEncoder:
    """
    A simple approach to Byte Pair Encoding (BPE).
    We combine frequent pairs of characters into new tokens
    to reduce the overall size of the string.
    """

    @staticmethod
    def _get_stats(text):
        """
        Count how often each pair of adjacent characters occurs in the text.
        Returns a dictionary mapping pairs to their frequency.
        """
        stats = {}
        for i in range(len(text) - 1):
            pair = (text[i], text[i + 1])
            stats[pair] = stats.get(pair, 0) + 1
        return stats

    @staticmethod
    def compress(data, num_merges=10):
        """
        Compress the input string by repeatedly merging the most common pairs.
        num_merges sets how many times we do this.
        Returns the compressed text and a merges_map so we can undo it later.
        """
        text = list(data)  # treat data as a list of individual chars
        merges_map = []

        for _ in range(num_merges):
            stats = BytePairEncoder._get_stats(text)
            if not stats:
                break
            best_pair = max(stats, key=stats.get)
            merges_map.append("".join(best_pair))

            # merge every occurrence of best_pair
            merged_text = []
            i = 0
            while i < len(text):
                if i < len(text) - 1 and (text[i], text[i+1]) == best_pair:
                    merged_text.append("".join(best_pair))  # treat them as one token
                    i += 2
                else:
                    merged_text.append(text[i])
                    i += 1
            text = merged_text

        # The compressed data is just the tokens joined by a space
        return " ".join(text), merges_map

    @staticmethod
    def decompress(compressed_data, merges_map):
        """
        Decompress the text by reversing each merge from merges_map in reverse order.
        Each merged token is split back into its original two-character form.
        """
        tokens = compressed_data.split(" ")
        for pair_str in reversed(merges_map):
            new_tokens = []
            for token in tokens:
                if token == pair_str:
                    new_tokens.extend(list(token))  # split the merged token
                else:
                    new_tokens.append(token)
            tokens = new_tokens
        return "".join(tokens)
