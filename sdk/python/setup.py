from setuptools import find_packages, setup

setup(
    name="ptn-sdk",
    version="0.1.0",
    description="Python SDK for Pakistan Trust Network",
    packages=find_packages(),
    install_requires=["httpx>=0.27"],
    python_requires=">=3.10",
)
