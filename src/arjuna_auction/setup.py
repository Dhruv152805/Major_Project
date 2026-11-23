from setuptools import find_packages, setup

package_name = 'arjuna_auction'

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
    description='Decentralized auction-based task allocation for TerrainFleet',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'auction_node = arjuna_auction.auction_node:main',
            'heartbeat_monitor = arjuna_auction.heartbeat_monitor:main',
            'record_points = arjuna_auction.record_points:main',
            'set_home_poses = arjuna_auction.set_home_poses:main',
            'task_injector = arjuna_auction.task_injector:main',
            'task_marker_node = arjuna_auction.task_marker_node:main',
            'train_bid_model = arjuna_auction.train_bid_model:main',
            'analyze_runs = arjuna_auction.analyze_runs:main',
        ],
    },
)
