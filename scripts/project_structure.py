import os

def print_directory_structure(root_dir, indent_level=0):

    items = os.listdir(root_dir)

    items = [item for item in items if item != '__pycache__']

    for index, item in enumerate(items):

        item_path = os.path.join(root_dir, item)

        if index == len(items) - 1:
            prefix = '└── '
        else:
            prefix = '├── '

        print('    ' * indent_level + prefix + item)

        if os.path.isdir(item_path):
            print_directory_structure(item_path, indent_level + 1)


root_directory = os.getcwd()
print("Project Structure:")
print_directory_structure(root_directory)
