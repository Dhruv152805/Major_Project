cmake_minimum_required(VERSION 3.8)
project(arjuna_odometry)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -std=c++17)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

# Executables
add_executable(arjuna_ekf_odom_pub src/arjuna_ekf_odom_pub.cpp)
target_include_directories(arjuna_ekf_odom_pub PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(arjuna_ekf_odom_pub
  rclcpp
  std_msgs
  sensor_msgs
  geometry_msgs
  nav_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
)

add_executable(arjuna_rviz_data_pub src/arjuna_rviz_data_pub.cpp)
target_include_directories(arjuna_rviz_data_pub PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
ament_target_dependencies(arjuna_rviz_data_pub
  rclcpp
  std_msgs
  sensor_msgs
  geometry_msgs
  nav_msgs
  tf2
  tf2_ros
  tf2_geometry_msgs
)

# Install targets
install(TARGETS
  arjuna_ekf_odom_pub
  arjuna_rviz_data_pub
  DESTINATION lib/${PROJECT_NAME}
)

# Install config and launch directories
install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line addresses ament_lint_auto's requirement
  # for all packages to contain at least some tests or be configured accordingly
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
