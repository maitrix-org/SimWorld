import os

def print_directory_structure(root_dir, indent_level=0):
    # 获取当前目录下的所有文件和文件夹
    items = os.listdir(root_dir)
    # 过滤掉 __pycache__ 目录
    items = [item for item in items if item != '__pycache__']
    # 遍历每个项目
    for index, item in enumerate(items):
        # 构建完整路径
        item_path = os.path.join(root_dir, item)
        # 确定树形符号
        if index == len(items) - 1:
            prefix = '└── '
        else:
            prefix = '├── '
        # 打印缩进和项目名称
        print('    ' * indent_level + prefix + item)
        # 如果是目录，则递归调用
        if os.path.isdir(item_path):
            print_directory_structure(item_path, indent_level + 1)

# 设置根目录为当前工作目录
root_directory = os.getcwd()
print("Project Structure:")
print_directory_structure(root_directory)
