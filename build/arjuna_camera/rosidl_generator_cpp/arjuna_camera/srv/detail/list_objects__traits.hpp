// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from arjuna_camera:srv/ListObjects.idl
// generated code does not contain a copyright notice

#ifndef ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__TRAITS_HPP_
#define ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "arjuna_camera/srv/detail/list_objects__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace arjuna_camera
{

namespace srv
{

inline void to_flow_style_yaml(
  const ListObjects_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ListObjects_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ListObjects_Request & msg, bool use_flow_style = false)
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
  const arjuna_camera::srv::ListObjects_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  arjuna_camera::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use arjuna_camera::srv::to_yaml() instead")]]
inline std::string to_yaml(const arjuna_camera::srv::ListObjects_Request & msg)
{
  return arjuna_camera::srv::to_yaml(msg);
}

template<>
inline const char * data_type<arjuna_camera::srv::ListObjects_Request>()
{
  return "arjuna_camera::srv::ListObjects_Request";
}

template<>
inline const char * name<arjuna_camera::srv::ListObjects_Request>()
{
  return "arjuna_camera/srv/ListObjects_Request";
}

template<>
struct has_fixed_size<arjuna_camera::srv::ListObjects_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<arjuna_camera::srv::ListObjects_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<arjuna_camera::srv::ListObjects_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'poses'
#include "geometry_msgs/msg/detail/pose_stamped__traits.hpp"

namespace arjuna_camera
{

namespace srv
{

inline void to_flow_style_yaml(
  const ListObjects_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: labels
  {
    if (msg.labels.size() == 0) {
      out << "labels: []";
    } else {
      out << "labels: [";
      size_t pending_items = msg.labels.size();
      for (auto item : msg.labels) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: poses
  {
    if (msg.poses.size() == 0) {
      out << "poses: []";
    } else {
      out << "poses: [";
      size_t pending_items = msg.poses.size();
      for (auto item : msg.poses) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ListObjects_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: labels
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.labels.size() == 0) {
      out << "labels: []\n";
    } else {
      out << "labels:\n";
      for (auto item : msg.labels) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: poses
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.poses.size() == 0) {
      out << "poses: []\n";
    } else {
      out << "poses:\n";
      for (auto item : msg.poses) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ListObjects_Response & msg, bool use_flow_style = false)
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
  const arjuna_camera::srv::ListObjects_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  arjuna_camera::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use arjuna_camera::srv::to_yaml() instead")]]
inline std::string to_yaml(const arjuna_camera::srv::ListObjects_Response & msg)
{
  return arjuna_camera::srv::to_yaml(msg);
}

template<>
inline const char * data_type<arjuna_camera::srv::ListObjects_Response>()
{
  return "arjuna_camera::srv::ListObjects_Response";
}

template<>
inline const char * name<arjuna_camera::srv::ListObjects_Response>()
{
  return "arjuna_camera/srv/ListObjects_Response";
}

template<>
struct has_fixed_size<arjuna_camera::srv::ListObjects_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<arjuna_camera::srv::ListObjects_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<arjuna_camera::srv::ListObjects_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<arjuna_camera::srv::ListObjects>()
{
  return "arjuna_camera::srv::ListObjects";
}

template<>
inline const char * name<arjuna_camera::srv::ListObjects>()
{
  return "arjuna_camera/srv/ListObjects";
}

template<>
struct has_fixed_size<arjuna_camera::srv::ListObjects>
  : std::integral_constant<
    bool,
    has_fixed_size<arjuna_camera::srv::ListObjects_Request>::value &&
    has_fixed_size<arjuna_camera::srv::ListObjects_Response>::value
  >
{
};

template<>
struct has_bounded_size<arjuna_camera::srv::ListObjects>
  : std::integral_constant<
    bool,
    has_bounded_size<arjuna_camera::srv::ListObjects_Request>::value &&
    has_bounded_size<arjuna_camera::srv::ListObjects_Response>::value
  >
{
};

template<>
struct is_service<arjuna_camera::srv::ListObjects>
  : std::true_type
{
};

template<>
struct is_service_request<arjuna_camera::srv::ListObjects_Request>
  : std::true_type
{
};

template<>
struct is_service_response<arjuna_camera::srv::ListObjects_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__TRAITS_HPP_
