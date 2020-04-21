import setuptools

from zeetoo import __author__, __verison__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zeetoo",
    version=__verison__,
    author=__author__,
    author_email="mwieclaw@icho.edu.pl",
    license='MIT',
    description="A humble collection of various everyday utility scripts "
                "from Team II IChO PAS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mishioo/zeetoo",
    packages=['zeetoo'],
    entry_points={
        'console_scripts': ['zeetoo=zeetoo.__main__:main']
    },
    install_requires=["openpyxl", "olefile"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Development Status :: 4 - Beta"
    ],
)
