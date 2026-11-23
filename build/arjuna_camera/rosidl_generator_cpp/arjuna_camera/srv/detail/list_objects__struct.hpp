// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from arjuna_camera:srv/ListObjects.idl
// generated code does not contain a copyright notice

#ifndef ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__STRUCT_HPP_
#define ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__arjuna_camera__srv__ListObjects_Request __attribute__((deprecated))
#else
# define DEPRECATED__arjuna_camera__srv__ListObjects_Request __declspec(deprecated)
#endif

namespace arjuna_camera
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ListObjects_Request_
{
  using Type = ListObjects_Request_<ContainerAllocator>;

  explicit ListObjects_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit ListObjects_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    arjuna_camera::srv::ListObjects_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const arjuna_camera::srv::ListObjects_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      arjuna_camera::srv::ListObjects_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      arjuna_camera::srv::ListObjects_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__arjuna_camera__srv__ListObjects_Request
    std::shared_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__arjuna_camera__srv__ListObjects_Request
    std::shared_ptr<arjuna_camera::srv::ListObjects_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ListObjects_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const ListObjects_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ListObjects_Request_

// alias to use template instance with default allocator
using ListObjects_Request =
  arjuna_camera::srv::ListObjects_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace arjuna_camera


// Include directives for member types
// Member 'poses'
#include "geometry_msgs/msg/detail/pose_stamped__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__arjuna_camera__srv__ListObjects_Response __attribute__((deprecated))
#else
# define DEPRECATED__arjuna_camera__srv__ListObjects_Response __declspec(deprecated)
#endif

namespace arjuna_camera
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct ListObjects_Response_
{
  using Type = ListObjects_Response_<ContainerAllocator>;

  explicit ListObjects_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
    }
  }

  explicit ListObjects_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
    }
  }

  // field types and members
  using _labels_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _labels_type labels;
  using _poses_type =
    std::vector<geometry_msgs::msg::PoseStamped_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<geometry_msgs::msg::PoseStamped_<ContainerAllocator>>>;
  _poses_type poses;
  using _success_type =
    bool;
  _success_type success;

  // setters for named parameter idiom
  Type & set__labels(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->labels = _arg;
    return *this;
  }
  Type & set__poses(
    const std::vector<geometry_msgs::msg::PoseStamped_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<geometry_msgs::msg::PoseStamped_<ContainerAllocator>>> & _arg)
  {
    this->poses = _arg;
    return *this;
  }
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    arjuna_camera::srv::ListObjects_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const arjuna_camera::srv::ListObjects_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      arjuna_camera::srv::ListObjects_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      arjuna_camera::srv::ListObjects_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__arjuna_camera__srv__ListObjects_Response
    std::shared_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__arjuna_camera__srv__ListObjects_Response
    std::shared_ptr<arjuna_camera::srv::ListObjects_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ListObjects_Response_ & other) const
  {
    if (this->labels != other.labels) {
      return false;
    }
    if (this->poses != other.poses) {
      return false;
    }
    if (this->success != other.success) {
      return false;
    }
    return true;
  }
  bool operator!=(const ListObjects_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ListObjects_Response_

// alias to use template instance with default allocator
using ListObjects_Response =
  arjuna_camera::srv::ListObjects_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace arjuna_camera

namespace arjuna_camera
{

namespace srv
{

struct ListObjects
{
  using Request = arjuna_camera::srv::ListObjects_Request;
  using Response = arjuna_camera::srv::ListObjects_Response;
};

}  // namespace srv

}  // namespace arjuna_camera

#endif  // ARJUNA_CAMERA__SRV__DETAIL__LIST_OBJECTS__STRUCT_HPP_
