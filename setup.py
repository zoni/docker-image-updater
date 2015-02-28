import os
from pkg_resources import parse_requirements
from setuptools import setup


def read(file):
    """Read file relative to the current directory and return it's contents"""
    return open(os.path.join(os.path.dirname(__file__), file)).read()


def read_requirements(file):
    """Return a list of requirements from file relative to current directory"""
    with open(os.path.join(os.path.dirname(__file__), file)) as f:
        return [str(r) for r in parse_requirements(f)]


setup(
    name="docker-image-updater",
    version="0.0.1",
    author="Nick Groenen",
    author_email="nick@groenen.me",
    description="Update docker images and trigger commands in response to updates",
    long_description=read('README.rst'),
    license="MIT",
    keywords="docker image update container",
    url="https://github.com/zoni/docker-image-updater",
    install_requires=read_requirements("requirements/base"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "Topic :: System :: Systems Administration",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ],
    packages=['diu'],
    entry_points={
        'console_scripts': ['docker-image-updater=diu.main:main']
    },
    include_package_data=True,
)
