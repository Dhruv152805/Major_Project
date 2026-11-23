// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from arjuna_camera:srv/ListObjects.idl
// generated code does not contain a copyright notice

#ifndef ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__BUILDER_HPP_
#define ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "arjuna_camera/srv/detail/list_objects__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace arjuna_camera
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::arjuna_camera::srv::ListObjects_Request>()
{
  return ::arjuna_camera::srv::ListObjects_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace arjuna_camera


namespace arjuna_camera
{

namespace srv
{

namespace builder
{

class Init_ListObjects_Response_success
{
public:
  explicit Init_ListObjects_Response_success(::arjuna_camera::srv::ListObjects_Response & msg)
  : msg_(msg)
  {}
  ::arjuna_camera::srv::ListObjects_Response success(::arjuna_camera::srv::ListObjects_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return std::move(msg_);
  }

private:
  ::arjuna_camera::srv::ListObjects_Response msg_;
};

class Init_ListObjects_Response_poses
{
public:
  explicit Init_ListObjects_Response_poses(::arjuna_camera::srv::ListObjects_Response & msg)
  : msg_(msg)
  {}
  Init_ListObjects_Response_success poses(::arjuna_camera::srv::ListObjects_Response::_poses_type arg)
  {
    msg_.poses = std::move(arg);
    return Init_ListObjects_Response_success(msg_);
  }

private:
  ::arjuna_camera::srv::ListObjects_Response msg_;
};

class Init_ListObjects_Response_labels
{
public:
  Init_ListObjects_Response_labels()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ListObjects_Response_poses labels(::arjuna_camera::srv::ListObjects_Response::_labels_type arg)
  {
    msg_.labels = std::move(arg);
    return Init_ListObjects_Response_poses(msg_);
  }

private:
  ::arjuna_camera::srv::ListObjects_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::arjuna_camera::srv::ListObjects_Response>()
{
  return arjuna_camera::srv::builder::Init_ListObjects_Response_labels();
}

}  // namespace arjuna_camera

#endif  // ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__BUILDER_HPP_
