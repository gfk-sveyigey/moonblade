import pathlib
from setuptools import setup


path = pathlib.Path(__file__).parent

long_description = (path / "README.md").read_text(encoding="utf-8")

setup(
    name = "moonblade",
    version = "1.1.4",
    description = "An asynchronous Python 3 library designed to communicate with the LOL server via the LCU API in a simple and flexible way.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/gfk-sveyigey/moonblade",
    author = "gfk-sveyigey",
    author_email = "gfk_sveyigey@163.com",
    license = "MIT",
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3 :: Only",
    ],
    packages = ["moonblade"],
    install_requires = [
        "httpx", "psutil", "websockets"
    ],
)