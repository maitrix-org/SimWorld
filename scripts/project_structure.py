"""Print the project structure in a tree-like format."""
import os


def print_directory_structure(root_dir, indent_level=0):
    """Print the directory structure in a tree-like format.

    Args:
        root_dir: Root directory path to start printing from.
        indent_level: Current indentation level (used for recursion).
    """
    items = os.listdir(root_dir)

    # Filter out __pycache__ directories
    items = [item for item in items if item != '__pycache__']

    for index, item in enumerate(items):
        item_path = os.path.join(root_dir, item)

        # Determine prefix based on whether this is the last item
        if index == len(items) - 1:
            prefix = '└── '
        else:
            prefix = '├── '

        print('    ' * indent_level + prefix + item)

        # Recursively process subdirectories
        if os.path.isdir(item_path):
            print_directory_structure(item_path, indent_level + 1)


# Print the project structure starting from the current directory
root_directory = os.getcwd()
print('Project Structure:')
print_directory_structure(root_directory)
