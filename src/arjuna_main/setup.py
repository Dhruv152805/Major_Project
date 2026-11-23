from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'arjuna_main'

setup(
    name=package_name,
    version='2.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('arjuna_main/launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('arjuna_main/config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('arjuna_main/rviz/*.rviz')),
        (os.path.join('share', package_name, 'maps'), glob('arjuna_main/maps/*')),
        (os.path.join('share', package_name, 'webpage'), glob('arjuna_main/webpage/*')),
        (os.path.join('share', package_name, 'behavior_trees'), glob('arjuna_main/behavior_trees/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Newrro Tech (Tushar S)',
    maintainer_email='info@newrro.in',
    description='Arjuna main autonomous robot ROS 2 package',
    license='MIT',
    entry_points={
        'console_scripts': [
            # OpenCV scripts
            'camera_pub = arjuna_main.scripts.Arjuna_opencv.Arjuna_camera_pub:main',
            'camera_sub = arjuna_main.scripts.Arjuna_opencv.Arjuna_camera_sub:main',
            'QR_Recog = arjuna_main.scripts.Arjuna_opencv.Arjuna_QR_Rec:main',
            'QR_Tracking = arjuna_main.scripts.Arjuna_opencv.Arjuna_QR_tracking:main',
            'QR_CT = arjuna_main.scripts.Arjuna_opencv.Arjuna_QR_CT:main',
            
            # Navigation scripts
            'go_to_point_terminal = arjuna_main.scripts.Arjuna_navigation.Arjuna_go_to_point_terminal:main',
            'arjuna_terminal_goal = arjuna_main.scripts.Arjuna_navigation.arjuna_terminal_goal:main',
            'multi_point_terminal = arjuna_main.scripts.Arjuna_navigation.Arjuna_multi_point_terminal:main',
            'obstacle_avoidance = arjuna_main.scripts.Arjuna_navigation.Arjuna_obstacle_avoidance:main',
            'rviz_goal_bridge = arjuna_main.scripts.Arjuna_navigation.rviz_goal_bridge:main',
            # Sensor & I2C scripts
            'data_code = arjuna_main.scripts.Data_code:main',
            # Fleet Dashboard Server
            'fleet_dashboard = arjuna_main.fleet_dashboard_server:main',
        ],
    },
)
