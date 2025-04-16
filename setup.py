from setuptools import setup, find_packages

setup(
    name="trackshapeutils",
    version="0.3.5",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scipy'
    ],
    package_data={
        'trackshapeutils': ['tsection.dat'],
    },
    author="Peter Grønbæk Andersen",
    author_email="peter@grnbk.io",
    description="Collection of utilities to modify existing MSTS/ORTS track shapes",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/pgroenbaek/trackshape-utils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)