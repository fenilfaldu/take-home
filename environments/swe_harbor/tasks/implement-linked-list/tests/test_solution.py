import sys

sys.path.insert(0, "/app")

from linked_list import LinkedList, Node


# --- Basic construction ---


def test_empty_list():
    ll = LinkedList()
    assert len(ll) == 0, "Empty list should have length 0"
    assert ll.to_list() == [], "Empty list to_list should return []"
    assert repr(ll) == "None", "Empty list repr should be 'None'"


def test_node_creation():
    node = Node(42)
    assert node.data == 42, "Node data should be 42"
    assert node.next is None, "New node next should be None"


# --- Append ---


def test_append_to_empty():
    ll = LinkedList()
    ll.append(1)
    assert ll.to_list() == [1], "Appending to empty list should give [1]"
    assert len(ll) == 1


def test_append_multiple():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    assert ll.to_list() == [1, 2, 3], "Append should add to end"
    assert len(ll) == 3


# --- Prepend ---


def test_prepend_to_empty():
    ll = LinkedList()
    ll.prepend(1)
    assert ll.to_list() == [1], "Prepending to empty list should give [1]"


def test_prepend_multiple():
    ll = LinkedList()
    ll.prepend(3)
    ll.prepend(2)
    ll.prepend(1)
    assert ll.to_list() == [1, 2, 3], "Prepend should add to beginning"


# --- Delete ---


def test_delete_head():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.delete(1)
    assert ll.to_list() == [2, 3], "Deleting head should remove first element"


def test_delete_tail():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.delete(3)
    assert ll.to_list() == [1, 2], "Deleting tail should remove last element"


def test_delete_middle():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(3)
    ll.delete(2)
    assert ll.to_list() == [1, 3], "Deleting middle should remove that element"


def test_delete_only_element():
    ll = LinkedList()
    ll.append(1)
    ll.delete(1)
    assert ll.to_list() == [], "Deleting only element should give empty list"
    assert len(ll) == 0


def test_delete_missing_value():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.delete(99)
    assert ll.to_list() == [1, 2], "Deleting missing value should not change list"


def test_delete_from_empty():
    ll = LinkedList()
    ll.delete(1)
    assert ll.to_list() == [], "Deleting from empty list should do nothing"


def test_delete_first_occurrence_only():
    ll = LinkedList()
    ll.append(1)
    ll.append(2)
    ll.append(1)
    ll.delete(1)
    assert ll.to_list() == [2, 1], "Delete should only remove the first occurrence"


# --- Find ---


def test_find_existing():
    ll = LinkedList()
    ll.append(10)
    ll.append(20)
    result = ll.find(20)
    assert result is not None, "find(20) should return a Node"
    assert result.data == 20, "Found node data should be 20"


def test_find_missing():
    ll = LinkedList()
    ll.append(1)
    assert ll.find(99) is None, "find(99) should return None when not in list"


def test_find_returns_first_match():
    ll = LinkedList()
    ll.append("a")
    ll.append("b")
    ll.append("a")
    result = ll.find("a")
    assert result is not None
    assert result.data == "a"
    # The found node should be the head (first occurrence)
    assert result is ll.head, "find should return the first matching node"


# --- Repr ---


def test_repr_with_elements():
    ll = LinkedList()
    ll.append(1)
    ll.append("hello")
    ll.append(3)
    assert repr(ll) == "1 -> 'hello' -> 3 -> None", (
        "repr should use repr() for each data value"
    )


# --- Mixed types ---


def test_mixed_types():
    ll = LinkedList()
    ll.append(1)
    ll.append("two")
    ll.append(3.0)
    assert ll.to_list() == [1, "two", 3.0], "List should support mixed types"
    assert len(ll) == 3


# --- Combined operations ---


def test_prepend_and_append():
    ll = LinkedList()
    ll.append(2)
    ll.prepend(1)
    ll.append(3)
    ll.prepend(0)
    assert ll.to_list() == [0, 1, 2, 3], (
        "Mixed prepend/append should maintain correct order"
    )
