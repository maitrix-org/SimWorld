"""This script is used to package the simworld project."""
import fnmatch
import os
import zipfile
from pathlib import Path


def read_gitignore():
    """Read the .gitignore file and return a list of ignore patterns."""
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        return []

    patterns = []
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
    return patterns


def should_ignore(path, patterns):
    """Check if the file should be ignored."""
    path_str = str(path)
    for pattern in patterns:
        if fnmatch.fnmatch(path_str, pattern):
            return True
        if fnmatch.fnmatch(path_str, f'**/{pattern}'):
            return True
    return False


def create_zip(output_name='simworld.zip'):
    """Create a zip file, automatically ignoring the contents of .gitignore."""
    ignore_patterns = read_gitignore()
    # Add some common files and directories to ignore
    ignore_patterns.extend([
        '*.pyc',
        '__pycache__',
        '*.zip',
        '.git',
        '.git/*',
        '.vscode',
        '.idea',
        '*.egg-info',
        'dist',
        'build',
    ])

    with zipfile.ZipFile(output_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Skip the zip file in the root directory
            if root == '.' and output_name in files:
                files.remove(output_name)

            # Filter out directories that should be ignored
            dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d, ignore_patterns)]

            for file in files:
                file_path = Path(root) / file
                if not should_ignore(file_path, ignore_patterns):
                    # Store the file using the relative path
                    arcname = str(file_path.relative_to('.'))
                    zipf.write(file_path, arcname)


if __name__ == '__main__':
    create_zip()
    print('Packaging completed!')
