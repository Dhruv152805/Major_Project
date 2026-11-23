// generated from rosidl_typesupport_cpp/resource/idl__type_support.cpp.em
// with input from arjuna_camera:srv/ListObjects.idl
// generated code does not contain a copyright notice

#include "cstddef"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "arjuna_camera/srv/detail/list_objects__struct.hpp"
#include "rosidl_typesupport_cpp/identifier.hpp"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
#include "rosidl_typesupport_cpp/visibility_control.h"
#include "rosidl_typesupport_interface/macros.h"

namespace arjuna_camera
{

namespace srv
{

namespace rosidl_typesupport_cpp
{

typedef struct _ListObjects_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _ListObjects_Request_type_support_ids_t;

static const _ListObjects_Request_type_support_ids_t _ListObjects_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _ListObjects_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _ListObjects_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _ListObjects_Request_type_support_symbol_names_t _ListObjects_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, arjuna_camera, srv, ListObjects_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, arjuna_camera, srv, ListObjects_Request)),
  }
};

typedef struct _ListObjects_Request_type_support_data_t
{
  void * data[2];
} _ListObjects_Request_type_support_data_t;

static _ListObjects_Request_type_support_data_t _ListObjects_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _ListObjects_Request_message_typesupport_map = {
  2,
  "arjuna_camera",
  &_ListObjects_Request_message_typesupport_ids.typesupport_identifier[0],
  &_ListObjects_Request_message_typesupport_symbol_names.symbol_name[0],
  &_ListObjects_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t ListObjects_Request_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_ListObjects_Request_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace srv

}  // namespace arjuna_camera

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<arjuna_camera::srv::ListObjects_Request>()
{
  return &::arjuna_camera::srv::rosidl_typesupport_cpp::ListObjects_Request_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, arjuna_camera, srv, ListObjects_Request)() {
  return get_message_type_support_handle<arjuna_camera::srv::ListObjects_Request>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "arjuna_camera/srv/detail/list_objects__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace arjuna_camera
{

namespace srv
{

namespace rosidl_typesupport_cpp
{

typedef struct _ListObjects_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _ListObjects_Response_type_support_ids_t;

static const _ListObjects_Response_type_support_ids_t _ListObjects_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _ListObjects_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _ListObjects_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _ListObjects_Response_type_support_symbol_names_t _ListObjects_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, arjuna_camera, srv, ListObjects_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, arjuna_camera, srv, ListObjects_Response)),
  }
};

typedef struct _ListObjects_Response_type_support_data_t
{
  void * data[2];
} _ListObjects_Response_type_support_data_t;

static _ListObjects_Response_type_support_data_t _ListObjects_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _ListObjects_Response_message_typesupport_map = {
  2,
  "arjuna_camera",
  &_ListObjects_Response_message_typesupport_ids.typesupport_identifier[0],
  &_ListObjects_Response_message_typesupport_symbol_names.symbol_name[0],
  &_ListObjects_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t ListObjects_Response_message_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_ListObjects_Response_message_typesupport_map),
  ::rosidl_typesupport_cpp::get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace srv

}  // namespace arjuna_camera

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<arjuna_camera::srv::ListObjects_Response>()
{
  return &::arjuna_camera::srv::rosidl_typesupport_cpp::ListObjects_Response_message_type_support_handle;
}

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_cpp, arjuna_camera, srv, ListObjects_Response)() {
  return get_message_type_support_handle<arjuna_camera::srv::ListObjects_Response>();
}

#ifdef __cplusplus
}
#endif
}  // namespace rosidl_typesupport_cpp

// already included above
// #include "cstddef"
#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "arjuna_camera/srv/detail/list_objects__struct.hpp"
// already included above
// #include "rosidl_typesupport_cpp/identifier.hpp"
#include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_cpp/service_type_support_dispatch.hpp"
// already included above
// #include "rosidl_typesupport_cpp/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace arjuna_camera
{

namespace srv
{

namespace rosidl_typesupport_cpp
{

typedef struct _ListObjects_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _ListObjects_type_support_ids_t;

static const _ListObjects_type_support_ids_t _ListObjects_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_cpp",  // ::rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
    "rosidl_typesupport_introspection_cpp",  // ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  }
};

typedef struct _ListObjects_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _ListObjects_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _ListObjects_type_support_symbol_names_t _ListObjects_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, arjuna_camera, srv, ListObjects)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, arjuna_camera, srv, ListObjects)),
  }
};

typedef struct _ListObjects_type_support_data_t
{
  void * data[2];
} _ListObjects_type_support_data_t;

static _ListObjects_type_support_data_t _ListObjects_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _ListObjects_service_typesupport_map = {
  2,
  "arjuna_camera",
  &_ListObjects_service_typesupport_ids.typesupport_identifier[0],
  &_ListObjects_service_typesupport_symbol_names.symbol_name[0],
  &_ListObjects_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t ListObjects_service_type_support_handle = {
  ::rosidl_typesupport_cpp::typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_ListObjects_service_typesupport_map),
  ::rosidl_typesupport_cpp::get_service_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_cpp

}  // namespace srv

}  // namespace arjuna_camera

namespace rosidl_typesupport_cpp
{

template<>
ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<arjuna_camera::srv::ListObjects>()
{
  return &::arjuna_camera::srv::rosidl_typesupport_cpp::ListObjects_service_type_support_handle;
}

}  // namespace rosidl_typesupport_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_cpp, arjuna_camera, srv, ListObjects)() {
  return ::rosidl_typesupport_cpp::get_service_type_support_handle<arjuna_camera::srv::ListObjects>();
}

#ifdef __cplusplus
}
#endif
