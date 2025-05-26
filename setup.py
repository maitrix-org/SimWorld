"""Setup script for SimWorld package."""

from setuptools import find_packages, setup

setup(
    name='simworld',
    version='0.1.0',
    author='SimWorld Team',
    author_email='example@example.com',
    description='A simulation framework for urban environments and traffic',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/example/simworld',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'simworld.config': ['*.yaml'],
        'simworld.data': ['*.json', 'sample_dataset/*.png'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    install_requires=[
        'numpy',
        'pandas',
        'pyqtgraph',
        'PyQt5',
        'unrealcv',
        'opencv-python',
        'pillow',
    ],
    extras_require={
        'dev': [
            'pytest',
            'flake8',
            'black',
        ],
    },
)
