// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from arjuna_camera:srv/GetObjectPose.idl
// generated code does not contain a copyright notice

#ifndef ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__FUNCTIONS_H_
#define ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "arjuna_camera/msg/rosidl_generator_c__visibility_control.h"

#include "arjuna_camera/srv/detail/get_object_pose__struct.h"

/// Initialize srv/GetObjectPose message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * arjuna_camera__srv__GetObjectPose_Request
 * )) before or use
 * arjuna_camera__srv__GetObjectPose_Request__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Request__init(arjuna_camera__srv__GetObjectPose_Request * msg);

/// Finalize srv/GetObjectPose message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Request__fini(arjuna_camera__srv__GetObjectPose_Request * msg);

/// Create srv/GetObjectPose message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * arjuna_camera__srv__GetObjectPose_Request__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
arjuna_camera__srv__GetObjectPose_Request *
arjuna_camera__srv__GetObjectPose_Request__create();

/// Destroy srv/GetObjectPose message.
/**
 * It calls
 * arjuna_camera__srv__GetObjectPose_Request__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Request__destroy(arjuna_camera__srv__GetObjectPose_Request * msg);

/// Check for srv/GetObjectPose message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Request__are_equal(const arjuna_camera__srv__GetObjectPose_Request * lhs, const arjuna_camera__srv__GetObjectPose_Request * rhs);

/// Copy a srv/GetObjectPose message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Request__copy(
  const arjuna_camera__srv__GetObjectPose_Request * input,
  arjuna_camera__srv__GetObjectPose_Request * output);

/// Initialize array of srv/GetObjectPose messages.
/**
 * It allocates the memory for the number of elements and calls
 * arjuna_camera__srv__GetObjectPose_Request__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Request__Sequence__init(arjuna_camera__srv__GetObjectPose_Request__Sequence * array, size_t size);

/// Finalize array of srv/GetObjectPose messages.
/**
 * It calls
 * arjuna_camera__srv__GetObjectPose_Request__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Request__Sequence__fini(arjuna_camera__srv__GetObjectPose_Request__Sequence * array);

/// Create array of srv/GetObjectPose messages.
/**
 * It allocates the memory for the array and calls
 * arjuna_camera__srv__GetObjectPose_Request__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
arjuna_camera__srv__GetObjectPose_Request__Sequence *
arjuna_camera__srv__GetObjectPose_Request__Sequence__create(size_t size);

/// Destroy array of srv/GetObjectPose messages.
/**
 * It calls
 * arjuna_camera__srv__GetObjectPose_Request__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Request__Sequence__destroy(arjuna_camera__srv__GetObjectPose_Request__Sequence * array);

/// Check for srv/GetObjectPose message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Request__Sequence__are_equal(const arjuna_camera__srv__GetObjectPose_Request__Sequence * lhs, const arjuna_camera__srv__GetObjectPose_Request__Sequence * rhs);

/// Copy an array of srv/GetObjectPose messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Request__Sequence__copy(
  const arjuna_camera__srv__GetObjectPose_Request__Sequence * input,
  arjuna_camera__srv__GetObjectPose_Request__Sequence * output);

/// Initialize srv/GetObjectPose message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * arjuna_camera__srv__GetObjectPose_Response
 * )) before or use
 * arjuna_camera__srv__GetObjectPose_Response__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Response__init(arjuna_camera__srv__GetObjectPose_Response * msg);

/// Finalize srv/GetObjectPose message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Response__fini(arjuna_camera__srv__GetObjectPose_Response * msg);

/// Create srv/GetObjectPose message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * arjuna_camera__srv__GetObjectPose_Response__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
arjuna_camera__srv__GetObjectPose_Response *
arjuna_camera__srv__GetObjectPose_Response__create();

/// Destroy srv/GetObjectPose message.
/**
 * It calls
 * arjuna_camera__srv__GetObjectPose_Response__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Response__destroy(arjuna_camera__srv__GetObjectPose_Response * msg);

/// Check for srv/GetObjectPose message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Response__are_equal(const arjuna_camera__srv__GetObjectPose_Response * lhs, const arjuna_camera__srv__GetObjectPose_Response * rhs);

/// Copy a srv/GetObjectPose message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Response__copy(
  const arjuna_camera__srv__GetObjectPose_Response * input,
  arjuna_camera__srv__GetObjectPose_Response * output);

/// Initialize array of srv/GetObjectPose messages.
/**
 * It allocates the memory for the number of elements and calls
 * arjuna_camera__srv__GetObjectPose_Response__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Response__Sequence__init(arjuna_camera__srv__GetObjectPose_Response__Sequence * array, size_t size);

/// Finalize array of srv/GetObjectPose messages.
/**
 * It calls
 * arjuna_camera__srv__GetObjectPose_Response__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Response__Sequence__fini(arjuna_camera__srv__GetObjectPose_Response__Sequence * array);

/// Create array of srv/GetObjectPose messages.
/**
 * It allocates the memory for the array and calls
 * arjuna_camera__srv__GetObjectPose_Response__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
arjuna_camera__srv__GetObjectPose_Response__Sequence *
arjuna_camera__srv__GetObjectPose_Response__Sequence__create(size_t size);

/// Destroy array of srv/GetObjectPose messages.
/**
 * It calls
 * arjuna_camera__srv__GetObjectPose_Response__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
void
arjuna_camera__srv__GetObjectPose_Response__Sequence__destroy(arjuna_camera__srv__GetObjectPose_Response__Sequence * array);

/// Check for srv/GetObjectPose message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Response__Sequence__are_equal(const arjuna_camera__srv__GetObjectPose_Response__Sequence * lhs, const arjuna_camera__srv__GetObjectPose_Response__Sequence * rhs);

/// Copy an array of srv/GetObjectPose messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_arjuna_camera
bool
arjuna_camera__srv__GetObjectPose_Response__Sequence__copy(
  const arjuna_camera__srv__GetObjectPose_Response__Sequence * input,
  arjuna_camera__srv__GetObjectPose_Response__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // ARJUNA_CAMERA__SRV__DETAIL__GET_OBJECT_POSE__FUNCTIONS_H_
