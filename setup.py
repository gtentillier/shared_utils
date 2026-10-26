from setuptools import find_packages, setup

setup(
    name="shared_utils",
    version="0.3.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
