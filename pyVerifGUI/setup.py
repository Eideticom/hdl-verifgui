import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as fh:
    install_requires = list(fh.readlines())

setuptools.setup(
    name="pyVerifGUI",
    version = "0.1.0",
    author = "David Lenfesty",
    author_email="david.lenfesty@eideticom.com",
    description="Qt-based RTL verification tools GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Eideticom/pyVerifGUI",
    packages=setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Windows and Linux",
    ],
    python_requires='>=3.7',
    entry_points={
        "gui_scripts": [
            "VerifGUI = pyVerifGUI.__main__:main",
        ],
    },
    install_requires=install_requires,
    package_data={
        'pyVerifGUI': ['assets/help/*.md', 'assets/images/*']
    }
)