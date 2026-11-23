// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from arjuna_camera:srv/GetObjectPose.idl
// generated code does not contain a copyright notice

#ifndef ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__TRAITS_HPP_
#define ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "arjuna_camera/srv/detail/get_object_pose__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace arjuna_camera
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetObjectPose_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: label
  {
    out << "label: ";
    rosidl_generator_traits::value_to_yaml(msg.label, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetObjectPose_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: label
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "label: ";
    rosidl_generator_traits::value_to_yaml(msg.label, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetObjectPose_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace arjuna_camera

namespace rosidl_generator_traits
{

[[deprecated("use arjuna_camera::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const arjuna_camera::srv::GetObjectPose_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  arjuna_camera::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use arjuna_camera::srv::to_yaml() instead")]]
inline std::string to_yaml(const arjuna_camera::srv::GetObjectPose_Request & msg)
{
  return arjuna_camera::srv::to_yaml(msg);
}

template<>
inline const char * data_type<arjuna_camera::srv::GetObjectPose_Request>()
{
  return "arjuna_camera::srv::GetObjectPose_Request";
}

template<>
inline const char * name<arjuna_camera::srv::GetObjectPose_Request>()
{
  return "arjuna_camera/srv/GetObjectPose_Request";
}

template<>
struct has_fixed_size<arjuna_camera::srv::GetObjectPose_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<arjuna_camera::srv::GetObjectPose_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<arjuna_camera::srv::GetObjectPose_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'pose'
#include "geometry_msgs/msg/detail/pose_stamped__traits.hpp"

namespace arjuna_camera
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetObjectPose_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: pose
  {
    out << "pose: ";
    to_flow_style_yaml(msg.pose, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetObjectPose_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: pose
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pose:\n";
    to_block_style_yaml(msg.pose, out, indentation + 2);
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetObjectPose_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace arjuna_camera

namespace rosidl_generator_traits
{

[[deprecated("use arjuna_camera::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const arjuna_camera::srv::GetObjectPose_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  arjuna_camera::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use arjuna_camera::srv::to_yaml() instead")]]
inline std::string to_yaml(const arjuna_camera::srv::GetObjectPose_Response & msg)
{
  return arjuna_camera::srv::to_yaml(msg);
}

template<>
inline const char * data_type<arjuna_camera::srv::GetObjectPose_Response>()
{
  return "arjuna_camera::srv::GetObjectPose_Response";
}

template<>
inline const char * name<arjuna_camera::srv::GetObjectPose_Response>()
{
  return "arjuna_camera/srv/GetObjectPose_Response";
}

template<>
struct has_fixed_size<arjuna_camera::srv::GetObjectPose_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<arjuna_camera::srv::GetObjectPose_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<arjuna_camera::srv::GetObjectPose_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<arjuna_camera::srv::GetObjectPose>()
{
  return "arjuna_camera::srv::GetObjectPose";
}

template<>
inline const char * name<arjuna_camera::srv::GetObjectPose>()
{
  return "arjuna_camera/srv/GetObjectPose";
}

template<>
struct has_fixed_size<arjuna_camera::srv::GetObjectPose>
  : std::integral_constant<
    bool,
    has_fixed_size<arjuna_camera::srv::GetObjectPose_Request>::value &&
    has_fixed_size<arjuna_camera::srv::GetObjectPose_Response>::value
  >
{
};

template<>
struct has_bounded_size<arjuna_camera::srv::GetObjectPose>
  : std::integral_constant<
    bool,
    has_bounded_size<arjuna_camera::srv::GetObjectPose_Request>::value &&
    has_bounded_size<arjuna_camera::srv::GetObjectPose_Response>::value
  >
{
};

template<>
struct is_service<arjuna_camera::srv::GetObjectPose>
  : std::true_type
{
};

template<>
struct is_service_request<arjuna_camera::srv::GetObjectPose_Request>
  : std::true_type
{
};

template<>
struct is_service_response<arjuna_camera::srv::GetObjectPose_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__TRAITS_HPP_
