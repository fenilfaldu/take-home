## Implement a Singly Linked List

Create a file `/app/linked_list.py` that implements a singly linked list with the following classes and methods.

### `Node` class

- `__init__(self, data)`: Store `data` and set `next` to `None`.

### `LinkedList` class

- `__init__(self)`: Initialize an empty linked list with `head` set to `None`.
- `append(self, data)`: Add a node with the given data to the **end** of the list.
- `prepend(self, data)`: Add a node with the given data to the **beginning** of the list.
- `delete(self, data)`: Remove the **first** node whose data matches the given value. Do nothing if the value is not found.
- `find(self, data)`: Return the first `Node` whose data matches the given value, or `None` if not found.
- `to_list(self)`: Return a Python `list` of all node data values in order.
- `__len__(self)`: Return the number of nodes in the list.
- `__repr__(self)`: Return a string in the format `"Node1 -> Node2 -> Node3 -> None"` (use `repr()` for each node's data value).

### Examples

```python
ll = LinkedList()
ll.append(1)
ll.append(2)
ll.prepend(0)
print(ll)          # 0 -> 1 -> 2 -> None
print(len(ll))     # 3
print(ll.to_list())  # [0, 1, 2]
ll.delete(1)
print(ll)          # 0 -> 2 -> None
print(ll.find(2).data)  # 2
print(ll.find(99))      # None
```
