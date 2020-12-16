import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as fh:
    install_requires = list(fh.readlines())

setuptools.setup(
    name="sv_hierarchy",
    version = "0.1.0",
    author = "David Lenfesty",
    author_email="david.lenfesty@eideticom.com",
    description="SystemVerilog file and hierarchy parsing utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Eideticom/hdl-verifgui",
    packages=setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Windows and Linux",
    ],
    python_requires='>=3.7',
    entry_points={
        "gui_scripts": [
            "hier_builder = sv_hierarchy.parser:main",
        ],
    },
    install_requires=install_requires,
)
