from setuptools import setup, find_packages

setup(
    name="codereview",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "codereview=codereview.cli:main",
            "code-profiler=codereview.cli:main",
        ],
    },
)

