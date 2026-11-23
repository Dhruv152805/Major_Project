from setuptools import find_packages
from setuptools import setup

setup(
    name='arjuna_camera',
    version='0.0.1',
    packages=find_packages(
        include=('arjuna_camera', 'arjuna_camera.*')),
)
