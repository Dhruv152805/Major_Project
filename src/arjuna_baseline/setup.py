from setuptools import find_packages, setup

package_name = 'arjuna_baseline'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='arjuna',
    maintainer_email='you@example.com',
    description='Centralized nearest-robot-first baseline controller for TerrainFleet',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'nearest_robot_controller = arjuna_baseline.nearest_robot_controller:main',
        ],
    },
)
