// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from arjuna_camera:srv/GetObjectPose.idl
// generated code does not contain a copyright notice

#ifndef ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__BUILDER_HPP_
#define ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "arjuna_camera/srv/detail/get_object_pose__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace arjuna_camera
{

namespace srv
{

namespace builder
{

class Init_GetObjectPose_Request_label
{
public:
  Init_GetObjectPose_Request_label()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::arjuna_camera::srv::GetObjectPose_Request label(::arjuna_camera::srv::GetObjectPose_Request::_label_type arg)
  {
    msg_.label = std::move(arg);
    return std::move(msg_);
  }

private:
  ::arjuna_camera::srv::GetObjectPose_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::arjuna_camera::srv::GetObjectPose_Request>()
{
  return arjuna_camera::srv::builder::Init_GetObjectPose_Request_label();
}

}  // namespace arjuna_camera


namespace arjuna_camera
{

namespace srv
{

namespace builder
{

class Init_GetObjectPose_Response_message
{
public:
  explicit Init_GetObjectPose_Response_message(::arjuna_camera::srv::GetObjectPose_Response & msg)
  : msg_(msg)
  {}
  ::arjuna_camera::srv::GetObjectPose_Response message(::arjuna_camera::srv::GetObjectPose_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::arjuna_camera::srv::GetObjectPose_Response msg_;
};

class Init_GetObjectPose_Response_pose
{
public:
  explicit Init_GetObjectPose_Response_pose(::arjuna_camera::srv::GetObjectPose_Response & msg)
  : msg_(msg)
  {}
  Init_GetObjectPose_Response_message pose(::arjuna_camera::srv::GetObjectPose_Response::_pose_type arg)
  {
    msg_.pose = std::move(arg);
    return Init_GetObjectPose_Response_message(msg_);
  }

private:
  ::arjuna_camera::srv::GetObjectPose_Response msg_;
};

class Init_GetObjectPose_Response_success
{
public:
  Init_GetObjectPose_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetObjectPose_Response_pose success(::arjuna_camera::srv::GetObjectPose_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_GetObjectPose_Response_pose(msg_);
  }

private:
  ::arjuna_camera::srv::GetObjectPose_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::arjuna_camera::srv::GetObjectPose_Response>()
{
  return arjuna_camera::srv::builder::Init_GetObjectPose_Response_success();
}

}  // namespace arjuna_camera

#endif  // ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__BUILDER_HPP_
