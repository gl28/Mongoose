from setuptools import setup, find_packages


# name of the console entrance
CONSOLE_NAME = 'mongoose'

setup(
    name="mongoose",
    version="0.0.1",
    python_requires='>=3.8.0',
    packages=find_packages(),
    install_requires=[
        "click==8.0.3",
        "pyserial==3.5",
    ],
    entry_points={
        "console_scripts": [f"{CONSOLE_NAME} = mongoose.entry_point:cli"]
    }
)