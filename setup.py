import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="topsis-sameer-102316089",
    version="1.0.3",
    author="Sameer",
    author_email="sameer@example.com",
    description=(
        "A Python package implementing TOPSIS "
        "(Technique for Order of Preference by Similarity to Ideal Solution) "
        "for multi-criteria decision making."
    ),
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/sameer/Topsis-Sameer-102316089",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "numpy",
        "openpyxl",
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_sameer_102316089.topsis:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
