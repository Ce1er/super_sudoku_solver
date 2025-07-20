from __future__ import annotations
from typing import Generator, Optional


class Node:
    """
    Attributes:
        left: Node to the left
        right: Node to the right
        up: Node above
        down: Node below
    """

    # Reference to the column header node
    # Is not assigned in __init__ as it cannot be known at this stage
    column: HeaderNode

    def __init__(self) -> None:
        # Set node to be its own neighbour in all 4 directions
        self.left: Node = self
        self.right: Node = self
        self.up: Node = self
        self.down: Node = self

    def left_sweep(self) -> Generator[Node, None, None]:
        """
        self.left, self.left.left, self.left.left.left ...
        up until but not including reaching the starting point

        Yields:
            Nodes to the left of this Node
        """
        x = self.left
        while x is not self:
            yield x
            x = x.left  # Traverse left through matrix

    def right_sweep(self) -> Generator[Node, None, None]:
        """
        self.right, self.right.right, self.right.right.right ...
        up until but not including reaching the starting point

        Yields:
            Nodes to the right of this Node
        """
        x = self.right
        while x is not self:
            yield x
            x = x.right  # Traverse right through matrix

    def up_sweep(self) -> Generator[Node, None, None]:
        """
        self.up, self.up.up, self.up.up.up ...
        up until but not including reaching the starting point

        Yields:
            Nodes above this Node
        """
        x = self.up
        while x is not self:
            yield x
            x = x.up  # Traverse up through matrix

    def down_sweep(self) -> Generator[Node, None, None]:
        """
        self.down, self.down.down, self.down.down.down ...
        up until but not including reaching the starting point

        Yields:
            Nodes below this Node
        """
        x = self.down
        while x is not self:
            yield x
            x = x.down  # Traverse down through matrix


class HeaderNode(Node):
    """
    Attributes:
        label: The name of the node.
        size: The number of nodes in the column
    """

    # Technically left and right are now type HeaderNode not type Node
    # But subclasses can't have narrower types to their parents
    label: int
    size: int

    def __init__(self, label: int) -> None:
        super().__init__()
        self.label = label
        self.size = 0


class Matrix:
    """
    Attributes:
        root: Root node. Not a real node in the matrix but allows header nodes to be linked from it
            and regular nodes linked to those header nodes.

        column_header: Maps labels to their root nodes for faster access.
        search_calls: List with number of calls to search method
            for each level in the recursion.
    """

    def __init__(self, labels: list[int], rows: list[list[int]]) -> None:
        """
        Args:
            labels: List with labels to identify each column
            rows: Each list in rows represents a row.
                Each int in that list refers to a column.
        """
        self.root: Node = Node()
        self.column_header: dict[int, HeaderNode] = {}

        # At the start 0 calls to search method have been made
        # The 0 will represent the lowest level of recursion
        # As recursive calls to search() happen more ints will be added to this list
        # Gets assigned in generate_solutions() method
        self.search_calls: list[int]

        # Root will be the first node in the structure
        prev = self.root

        # Create the column headers
        # Loop through each column and create links
        for label in labels:
            # Create header for column
            column = HeaderNode(label)
            column.column = column  # Header points to itself

            self.column_header[label] = column

            # Will start by linking first column to the root node
            # In subsequent iterations it will link to previous column
            column.left = prev

            # Root will be to the right of the final column
            column.right = self.root

            # right of previous node now points to this one
            prev.right = column

            # left of root now points to this column
            self.root.left = column

            prev = column

        # Add rows to the matrix
        for row in rows:
            # last tracks the last Node added in the row
            last = None

            # Each row is a list containing the label of the columns they are in
            # So this loop traverses through each Node in the row using the
            # column label as the identifier for the Node.
            for row_label in row:
                node = Node()

                node.column = self.column_header[row_label]

                # A new node is being added to the column
                # So the size is increased by 1
                node.column.size += 1

                # Connect the old bottom node's down to point to the new node
                node.column.up.down = node

                # Set the new node's up to point to the old bottom node
                node.up = node.column.up

                # As this is now the bottom node. The HeaderNode should be below it.
                node.down = node.column

                # As this is now the bottom node. It is above the HeaderNode.
                node.column.up = node

                # Don't do for first node
                if last:
                    # Old node is to the left of current node.
                    node.left = last

                    # Set right to point to first node in row.
                    node.right = last.right

                    # Sets the first node in the row to point towards this one.
                    last.right.left = node

                    # Sets last node to point to this one.
                    last.right = node

                last = node

    def _cover(self, column: HeaderNode) -> None:
        """
        Args:
            column: The HeaderNode of the column to cover
        """
        # Set column to the right to point to column to the left of current one.
        column.right.left = column.left

        # Set column to the left to point to column to the right of current one.
        column.left.right = column.right

        # Iterate through nodes in column
        for column_node in column.down_sweep():
            # Iterate through nodes in in row of column_node
            for node in column_node.right_sweep():
                # Set the node below the current node to point to the node above the current node.
                node.down.up = node.up

                # Set the node above the current node to point to the node below the current node.
                node.up.down = node.down

                # This node is being removed from the column. So decrement the size of the column.
                node.column.size -= 1

    def _uncover(self, column: HeaderNode) -> None:
        """
        Args:
            column: The HeaderNode of the column to uncover
        """
        # Goes in opposite direction to cover() for both column and row traversals.
        for column_node in column.up_sweep():
            for node in column_node.left_sweep():
                # Node is being (re)added so size is increased
                node.column.size += 1

                # Set node below current node to point to current node
                node.down.up = node

                # Set node above current node to point to current node
                node.up.down = node

        # Set column to right of current column to point to current column
        column.right.left = column

        # Set column to left of current column to point to current column
        column.left.right = column

    def _search(
        self, recursion_level: int = 0, solution: Optional[list[Node]] = None
    ) -> Generator[list[Node], None, None]:
        """Recursive search algorithm to find exact cover solutions.
        Args:
            recursion_level: Level of the recursive call.
            solution: List of rows in the (partial) solution
        Yields:
            List of rows consisting a solution
        """
        if solution is None:
            solution = []

        # Check if there is already an int for the current level of recursion in search_calls
        if len(self.search_calls) <= recursion_level:
            self.search_calls.append(0)

        # This is a call to search() so increment counter in search_calls based on recursion level
        self.search_calls[recursion_level] += 1

        if self.root.right == self.root:
            # If there are no columns to the right of root. Then all must be covered. So there is a solution.
            yield solution
            return

        size = float("inf")
        # Iterate over HeaderNodes
        smallest = None
        for column in self.root.right_sweep():
            # Everything linked from left/right to the root node is a HeaderNode except the root node itself
            # So they do have the size attribute, thus typechecker warnings can be ignored
            if column.size < size:  # type: ignore[attr-defined]
                size = column.size  # type: ignore[attr-defined]
                smallest = column  # type: ignore[attr-defined]

        if not smallest:
            raise Exception("_search() failed. No columns to cover.")
            # This Exception should never be raised as a solution should be yielded if there are no more columns
            # It is just here to avoid typechecker warnings from smallest being unbound
            # Despite that being impossible due to the afformentioned check

        self._cover(smallest.column)

        # Iterate over nodes in column
        for column_node in smallest.down_sweep():
            # This will be added to solution later
            x = column_node

            # Iterate over nodes in row to cover all columns this row has nodes in
            for node in column_node.right_sweep():
                self._cover(node.column)

            # Recursive call to search(), extending the partial solution with x.
            # yield from passes up all valid solutions found before.
            # When search() ends a generator function with all solutions will be given.
            yield from self._search(
                recursion_level=recursion_level + 1, solution=solution + [x]
            )

            # If a solution wasn't found then uncover all nodes that we just covered.
            # Direction is arbritrary but must be the opposite of the one used when covering columns
            for j in column_node.left_sweep():
                self._uncover(j.column)
        self._uncover(smallest.column)

    def _get_row_labels(self, node: Node) -> list[int]:
        """
        Args:
            row: Node in the row to get labels from

        Returns:
            List of all column labels in the row
        """
        # Start with label the node given is in
        labels = [node.column.label]

        # Add the rest of the labels
        for x in node.right_sweep():
            labels.append(x.column.label)

        return labels

    def generate_solutions(self) -> Generator[list[list[int]], None, None]:
        """Wrapper for the search method

        Yields:
            All possible exact cover matrices.
            Gives each row as an array of their Node's column label.
        """
        self.search_calls = [0]

        for solution in self._search():
            # Yielding here allows processing solutions as soon as they are found instead of waiting for them all
            yield [self._get_row_labels(s) for s in solution]


# TODO: remove some unneeded comments
