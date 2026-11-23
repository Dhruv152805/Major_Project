#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "arjuna_camera__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__GetObjectPose_Request() -> *const std::ffi::c_void;
}

#[link(name = "arjuna_camera__rosidl_generator_c")]
extern "C" {
    fn arjuna_camera__srv__GetObjectPose_Request__init(msg: *mut GetObjectPose_Request) -> bool;
    fn arjuna_camera__srv__GetObjectPose_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetObjectPose_Request>, size: usize) -> bool;
    fn arjuna_camera__srv__GetObjectPose_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetObjectPose_Request>);
    fn arjuna_camera__srv__GetObjectPose_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetObjectPose_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<GetObjectPose_Request>) -> bool;
}

// Corresponds to arjuna_camera__srv__GetObjectPose_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetObjectPose_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub label: rosidl_runtime_rs::String,

}



impl Default for GetObjectPose_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arjuna_camera__srv__GetObjectPose_Request__init(&mut msg as *mut _) {
        panic!("Call to arjuna_camera__srv__GetObjectPose_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetObjectPose_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__GetObjectPose_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__GetObjectPose_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__GetObjectPose_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetObjectPose_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetObjectPose_Request where Self: Sized {
  const TYPE_NAME: &'static str = "arjuna_camera/srv/GetObjectPose_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__GetObjectPose_Request() }
  }
}


#[link(name = "arjuna_camera__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__GetObjectPose_Response() -> *const std::ffi::c_void;
}

#[link(name = "arjuna_camera__rosidl_generator_c")]
extern "C" {
    fn arjuna_camera__srv__GetObjectPose_Response__init(msg: *mut GetObjectPose_Response) -> bool;
    fn arjuna_camera__srv__GetObjectPose_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<GetObjectPose_Response>, size: usize) -> bool;
    fn arjuna_camera__srv__GetObjectPose_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<GetObjectPose_Response>);
    fn arjuna_camera__srv__GetObjectPose_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<GetObjectPose_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<GetObjectPose_Response>) -> bool;
}

// Corresponds to arjuna_camera__srv__GetObjectPose_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetObjectPose_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pose: geometry_msgs::msg::rmw::PoseStamped,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for GetObjectPose_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arjuna_camera__srv__GetObjectPose_Response__init(&mut msg as *mut _) {
        panic!("Call to arjuna_camera__srv__GetObjectPose_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for GetObjectPose_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__GetObjectPose_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__GetObjectPose_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__GetObjectPose_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for GetObjectPose_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for GetObjectPose_Response where Self: Sized {
  const TYPE_NAME: &'static str = "arjuna_camera/srv/GetObjectPose_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__GetObjectPose_Response() }
  }
}


#[link(name = "arjuna_camera__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__ListObjects_Request() -> *const std::ffi::c_void;
}

#[link(name = "arjuna_camera__rosidl_generator_c")]
extern "C" {
    fn arjuna_camera__srv__ListObjects_Request__init(msg: *mut ListObjects_Request) -> bool;
    fn arjuna_camera__srv__ListObjects_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ListObjects_Request>, size: usize) -> bool;
    fn arjuna_camera__srv__ListObjects_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ListObjects_Request>);
    fn arjuna_camera__srv__ListObjects_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ListObjects_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<ListObjects_Request>) -> bool;
}

// Corresponds to arjuna_camera__srv__ListObjects_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListObjects_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for ListObjects_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arjuna_camera__srv__ListObjects_Request__init(&mut msg as *mut _) {
        panic!("Call to arjuna_camera__srv__ListObjects_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ListObjects_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__ListObjects_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__ListObjects_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__ListObjects_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ListObjects_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ListObjects_Request where Self: Sized {
  const TYPE_NAME: &'static str = "arjuna_camera/srv/ListObjects_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__ListObjects_Request() }
  }
}


#[link(name = "arjuna_camera__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__ListObjects_Response() -> *const std::ffi::c_void;
}

#[link(name = "arjuna_camera__rosidl_generator_c")]
extern "C" {
    fn arjuna_camera__srv__ListObjects_Response__init(msg: *mut ListObjects_Response) -> bool;
    fn arjuna_camera__srv__ListObjects_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ListObjects_Response>, size: usize) -> bool;
    fn arjuna_camera__srv__ListObjects_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ListObjects_Response>);
    fn arjuna_camera__srv__ListObjects_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ListObjects_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<ListObjects_Response>) -> bool;
}

// Corresponds to arjuna_camera__srv__ListObjects_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListObjects_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub labels: rosidl_runtime_rs::Sequence<rosidl_runtime_rs::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub poses: rosidl_runtime_rs::Sequence<geometry_msgs::msg::rmw::PoseStamped>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,

}



impl Default for ListObjects_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !arjuna_camera__srv__ListObjects_Response__init(&mut msg as *mut _) {
        panic!("Call to arjuna_camera__srv__ListObjects_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ListObjects_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__ListObjects_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__ListObjects_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { arjuna_camera__srv__ListObjects_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ListObjects_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ListObjects_Response where Self: Sized {
  const TYPE_NAME: &'static str = "arjuna_camera/srv/ListObjects_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__arjuna_camera__srv__ListObjects_Response() }
  }
}






#[link(name = "arjuna_camera__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__arjuna_camera__srv__GetObjectPose() -> *const std::ffi::c_void;
}

// Corresponds to arjuna_camera__srv__GetObjectPose
#[allow(missing_docs, non_camel_case_types)]
pub struct GetObjectPose;

impl rosidl_runtime_rs::Service for GetObjectPose {
    type Request = GetObjectPose_Request;
    type Response = GetObjectPose_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__arjuna_camera__srv__GetObjectPose() }
    }
}




#[link(name = "arjuna_camera__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__arjuna_camera__srv__ListObjects() -> *const std::ffi::c_void;
}

// Corresponds to arjuna_camera__srv__ListObjects
#[allow(missing_docs, non_camel_case_types)]
pub struct ListObjects;

impl rosidl_runtime_rs::Service for ListObjects {
    type Request = ListObjects_Request;
    type Response = ListObjects_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__arjuna_camera__srv__ListObjects() }
    }
}


