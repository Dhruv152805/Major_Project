// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from arjuna_camera:srv/ListObjects.idl
// generated code does not contain a copyright notice

#ifndef ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__STRUCT_H_
#define ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/ListObjects in the package arjuna_camera.
typedef struct arjuna_camera__srv__ListObjects_Request
{
  uint8_t structure_needs_at_least_one_member;
} arjuna_camera__srv__ListObjects_Request;

// Struct for a sequence of arjuna_camera__srv__ListObjects_Request.
typedef struct arjuna_camera__srv__ListObjects_Request__Sequence
{
  arjuna_camera__srv__ListObjects_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} arjuna_camera__srv__ListObjects_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'labels'
#include "rosidl_runtime_c/string.h"
// Member 'poses'
#include "geometry_msgs/msg/detail/pose_stamped__struct.h"

/// Struct defined in srv/ListObjects in the package arjuna_camera.
typedef struct arjuna_camera__srv__ListObjects_Response
{
  rosidl_runtime_c__String__Sequence labels;
  geometry_msgs__msg__PoseStamped__Sequence poses;
  bool success;
} arjuna_camera__srv__ListObjects_Response;

// Struct for a sequence of arjuna_camera__srv__ListObjects_Response.
typedef struct arjuna_camera__srv__ListObjects_Response__Sequence
{
  arjuna_camera__srv__ListObjects_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} arjuna_camera__srv__ListObjects_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__STRUCT_H_
