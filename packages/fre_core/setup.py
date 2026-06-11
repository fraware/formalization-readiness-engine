from setuptools import find_packages, setup

setup(
    name="fre-core",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    install_requires=["pydantic>=2.8", "typer>=0.12", "rich>=13.7"],
)
