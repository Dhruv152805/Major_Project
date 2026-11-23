# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target arjuna_camera::arjuna_camera
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${arjuna_camera_TARGETS}.
if(arjuna_camera_TARGETS AND NOT TARGET arjuna_camera::arjuna_camera)
  add_library(arjuna_camera::arjuna_camera INTERFACE IMPORTED)
  set_target_properties(arjuna_camera::arjuna_camera PROPERTIES
    INTERFACE_LINK_LIBRARIES "${arjuna_camera_TARGETS}")
endif()
