// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from arjuna_camera:srv/ListObjects.idl
// generated code does not contain a copyright notice
#include "arjuna_camera/srv/detail/list_objects__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

bool
arjuna_camera__srv__ListObjects_Request__init(arjuna_camera__srv__ListObjects_Request * msg)
{
  if (!msg) {
    return false;
  }
  // structure_needs_at_least_one_member
  return true;
}

void
arjuna_camera__srv__ListObjects_Request__fini(arjuna_camera__srv__ListObjects_Request * msg)
{
  if (!msg) {
    return;
  }
  // structure_needs_at_least_one_member
}

bool
arjuna_camera__srv__ListObjects_Request__are_equal(const arjuna_camera__srv__ListObjects_Request * lhs, const arjuna_camera__srv__ListObjects_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // structure_needs_at_least_one_member
  if (lhs->structure_needs_at_least_one_member != rhs->structure_needs_at_least_one_member) {
    return false;
  }
  return true;
}

bool
arjuna_camera__srv__ListObjects_Request__copy(
  const arjuna_camera__srv__ListObjects_Request * input,
  arjuna_camera__srv__ListObjects_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // structure_needs_at_least_one_member
  output->structure_needs_at_least_one_member = input->structure_needs_at_least_one_member;
  return true;
}

arjuna_camera__srv__ListObjects_Request *
arjuna_camera__srv__ListObjects_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  arjuna_camera__srv__ListObjects_Request * msg = (arjuna_camera__srv__ListObjects_Request *)allocator.allocate(sizeof(arjuna_camera__srv__ListObjects_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(arjuna_camera__srv__ListObjects_Request));
  bool success = arjuna_camera__srv__ListObjects_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
arjuna_camera__srv__ListObjects_Request__destroy(arjuna_camera__srv__ListObjects_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    arjuna_camera__srv__ListObjects_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
arjuna_camera__srv__ListObjects_Request__Sequence__init(arjuna_camera__srv__ListObjects_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  arjuna_camera__srv__ListObjects_Request * data = NULL;

  if (size) {
    data = (arjuna_camera__srv__ListObjects_Request *)allocator.zero_allocate(size, sizeof(arjuna_camera__srv__ListObjects_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = arjuna_camera__srv__ListObjects_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        arjuna_camera__srv__ListObjects_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
arjuna_camera__srv__ListObjects_Request__Sequence__fini(arjuna_camera__srv__ListObjects_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      arjuna_camera__srv__ListObjects_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

arjuna_camera__srv__ListObjects_Request__Sequence *
arjuna_camera__srv__ListObjects_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  arjuna_camera__srv__ListObjects_Request__Sequence * array = (arjuna_camera__srv__ListObjects_Request__Sequence *)allocator.allocate(sizeof(arjuna_camera__srv__ListObjects_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = arjuna_camera__srv__ListObjects_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
arjuna_camera__srv__ListObjects_Request__Sequence__destroy(arjuna_camera__srv__ListObjects_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    arjuna_camera__srv__ListObjects_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
arjuna_camera__srv__ListObjects_Request__Sequence__are_equal(const arjuna_camera__srv__ListObjects_Request__Sequence * lhs, const arjuna_camera__srv__ListObjects_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!arjuna_camera__srv__ListObjects_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
arjuna_camera__srv__ListObjects_Request__Sequence__copy(
  const arjuna_camera__srv__ListObjects_Request__Sequence * input,
  arjuna_camera__srv__ListObjects_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(arjuna_camera__srv__ListObjects_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    arjuna_camera__srv__ListObjects_Request * data =
      (arjuna_camera__srv__ListObjects_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!arjuna_camera__srv__ListObjects_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          arjuna_camera__srv__ListObjects_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!arjuna_camera__srv__ListObjects_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `labels`
#include "rosidl_runtime_c/string_functions.h"
// Member `poses`
#include "geometry_msgs/msg/detail/pose_stamped__functions.h"

bool
arjuna_camera__srv__ListObjects_Response__init(arjuna_camera__srv__ListObjects_Response * msg)
{
  if (!msg) {
    return false;
  }
  // labels
  if (!rosidl_runtime_c__String__Sequence__init(&msg->labels, 0)) {
    arjuna_camera__srv__ListObjects_Response__fini(msg);
    return false;
  }
  // poses
  if (!geometry_msgs__msg__PoseStamped__Sequence__init(&msg->poses, 0)) {
    arjuna_camera__srv__ListObjects_Response__fini(msg);
    return false;
  }
  // success
  return true;
}

void
arjuna_camera__srv__ListObjects_Response__fini(arjuna_camera__srv__ListObjects_Response * msg)
{
  if (!msg) {
    return;
  }
  // labels
  rosidl_runtime_c__String__Sequence__fini(&msg->labels);
  // poses
  geometry_msgs__msg__PoseStamped__Sequence__fini(&msg->poses);
  // success
}

bool
arjuna_camera__srv__ListObjects_Response__are_equal(const arjuna_camera__srv__ListObjects_Response * lhs, const arjuna_camera__srv__ListObjects_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // labels
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->labels), &(rhs->labels)))
  {
    return false;
  }
  // poses
  if (!geometry_msgs__msg__PoseStamped__Sequence__are_equal(
      &(lhs->poses), &(rhs->poses)))
  {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  return true;
}

bool
arjuna_camera__srv__ListObjects_Response__copy(
  const arjuna_camera__srv__ListObjects_Response * input,
  arjuna_camera__srv__ListObjects_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // labels
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->labels), &(output->labels)))
  {
    return false;
  }
  // poses
  if (!geometry_msgs__msg__PoseStamped__Sequence__copy(
      &(input->poses), &(output->poses)))
  {
    return false;
  }
  // success
  output->success = input->success;
  return true;
}

arjuna_camera__srv__ListObjects_Response *
arjuna_camera__srv__ListObjects_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  arjuna_camera__srv__ListObjects_Response * msg = (arjuna_camera__srv__ListObjects_Response *)allocator.allocate(sizeof(arjuna_camera__srv__ListObjects_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(arjuna_camera__srv__ListObjects_Response));
  bool success = arjuna_camera__srv__ListObjects_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
arjuna_camera__srv__ListObjects_Response__destroy(arjuna_camera__srv__ListObjects_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    arjuna_camera__srv__ListObjects_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
arjuna_camera__srv__ListObjects_Response__Sequence__init(arjuna_camera__srv__ListObjects_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  arjuna_camera__srv__ListObjects_Response * data = NULL;

  if (size) {
    data = (arjuna_camera__srv__ListObjects_Response *)allocator.zero_allocate(size, sizeof(arjuna_camera__srv__ListObjects_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = arjuna_camera__srv__ListObjects_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        arjuna_camera__srv__ListObjects_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
arjuna_camera__srv__ListObjects_Response__Sequence__fini(arjuna_camera__srv__ListObjects_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      arjuna_camera__srv__ListObjects_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

arjuna_camera__srv__ListObjects_Response__Sequence *
arjuna_camera__srv__ListObjects_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  arjuna_camera__srv__ListObjects_Response__Sequence * array = (arjuna_camera__srv__ListObjects_Response__Sequence *)allocator.allocate(sizeof(arjuna_camera__srv__ListObjects_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = arjuna_camera__srv__ListObjects_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
arjuna_camera__srv__ListObjects_Response__Sequence__destroy(arjuna_camera__srv__ListObjects_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    arjuna_camera__srv__ListObjects_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
arjuna_camera__srv__ListObjects_Response__Sequence__are_equal(const arjuna_camera__srv__ListObjects_Response__Sequence * lhs, const arjuna_camera__srv__ListObjects_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!arjuna_camera__srv__ListObjects_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
arjuna_camera__srv__ListObjects_Response__Sequence__copy(
  const arjuna_camera__srv__ListObjects_Response__Sequence * input,
  arjuna_camera__srv__ListObjects_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(arjuna_camera__srv__ListObjects_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    arjuna_camera__srv__ListObjects_Response * data =
      (arjuna_camera__srv__ListObjects_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!arjuna_camera__srv__ListObjects_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          arjuna_camera__srv__ListObjects_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!arjuna_camera__srv__ListObjects_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
