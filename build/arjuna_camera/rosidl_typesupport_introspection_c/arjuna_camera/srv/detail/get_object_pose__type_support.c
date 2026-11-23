// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from arjuna_camera:srv/GetObjectPose.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "arjuna_camera/srv/detail/get_object_pose__rosidl_typesupport_introspection_c.h"
#include "arjuna_camera/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "arjuna_camera/srv/detail/get_object_pose__functions.h"
#include "arjuna_camera/srv/detail/get_object_pose__struct.h"


// Include directives for member types
// Member `label`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  arjuna_camera__srv__GetObjectPose_Request__init(message_memory);
}

void arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_fini_function(void * message_memory)
{
  arjuna_camera__srv__GetObjectPose_Request__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_member_array[1] = {
  {
    "label",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(arjuna_camera__srv__GetObjectPose_Request, label),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_members = {
  "arjuna_camera__srv",  // message namespace
  "GetObjectPose_Request",  // message name
  1,  // number of fields
  sizeof(arjuna_camera__srv__GetObjectPose_Request),
  arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_member_array,  // message members
  arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_type_support_handle = {
  0,
  &arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_arjuna_camera
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, arjuna_camera, srv, GetObjectPose_Request)() {
  if (!arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_type_support_handle.typesupport_identifier) {
    arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &arjuna_camera__srv__GetObjectPose_Request__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "arjuna_camera/srv/detail/get_object_pose__rosidl_typesupport_introspection_c.h"
// already included above
// #include "arjuna_camera/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "arjuna_camera/srv/detail/get_object_pose__functions.h"
// already included above
// #include "arjuna_camera/srv/detail/get_object_pose__struct.h"


// Include directives for member types
// Member `pose`
#include "geometry_msgs/msg/pose_stamped.h"
// Member `pose`
#include "geometry_msgs/msg/detail/pose_stamped__rosidl_typesupport_introspection_c.h"
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  arjuna_camera__srv__GetObjectPose_Response__init(message_memory);
}

void arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_fini_function(void * message_memory)
{
  arjuna_camera__srv__GetObjectPose_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_member_array[3] = {
  {
    "success",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(arjuna_camera__srv__GetObjectPose_Response, success),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "pose",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(arjuna_camera__srv__GetObjectPose_Response, pose),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "message",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(arjuna_camera__srv__GetObjectPose_Response, message),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_members = {
  "arjuna_camera__srv",  // message namespace
  "GetObjectPose_Response",  // message name
  3,  // number of fields
  sizeof(arjuna_camera__srv__GetObjectPose_Response),
  arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_member_array,  // message members
  arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_type_support_handle = {
  0,
  &arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_arjuna_camera
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, arjuna_camera, srv, GetObjectPose_Response)() {
  arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, geometry_msgs, msg, PoseStamped)();
  if (!arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_type_support_handle.typesupport_identifier) {
    arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &arjuna_camera__srv__GetObjectPose_Response__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "arjuna_camera/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "arjuna_camera/srv/detail/get_object_pose__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_service_members = {
  "arjuna_camera__srv",  // service namespace
  "GetObjectPose",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_Request_message_type_support_handle,
  NULL  // response message
  // arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_Response_message_type_support_handle
};

static rosidl_service_type_support_t arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_service_type_support_handle = {
  0,
  &arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, arjuna_camera, srv, GetObjectPose_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, arjuna_camera, srv, GetObjectPose_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_arjuna_camera
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, arjuna_camera, srv, GetObjectPose)() {
  if (!arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_service_type_support_handle.typesupport_identifier) {
    arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, arjuna_camera, srv, GetObjectPose_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, arjuna_camera, srv, GetObjectPose_Response)()->data;
  }

  return &arjuna_camera__srv__detail__get_object_pose__rosidl_typesupport_introspection_c__GetObjectPose_service_type_support_handle;
}
