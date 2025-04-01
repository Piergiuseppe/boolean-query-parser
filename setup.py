from setuptools import find_packages, setup

setup(
    name="boolean_query_parser",
    version="0.1.0",
    author="Piergiuseppe D'Abbraccio",
    author_email="piergiuseppedabbraccio@gmail.com",
    description="A Python package for parsing and evaluating boolean text queries",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Piergiuseppe/boolean-query-parser",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.9",
    install_requires=[
        "regex>=2021.8.3",
    ],
    keywords="boolean, query, parser, text, search",
    project_urls={
        "Bug Reports": "https://github.com/Piergiuseppe/boolean-query-parser/issues",
        "Source": "https://github.com/Piergiuseppe/boolean-query-parser",
    },
)
