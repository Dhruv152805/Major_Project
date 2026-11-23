#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to arjuna_camera__srv__GetObjectPose_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetObjectPose_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub label: std::string::String,

}



impl Default for GetObjectPose_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetObjectPose_Request::default())
  }
}

impl rosidl_runtime_rs::Message for GetObjectPose_Request {
  type RmwMsg = super::srv::rmw::GetObjectPose_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        label: msg.label.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        label: msg.label.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      label: msg.label.to_string(),
    }
  }
}


// Corresponds to arjuna_camera__srv__GetObjectPose_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetObjectPose_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pose: geometry_msgs::msg::PoseStamped,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for GetObjectPose_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetObjectPose_Response::default())
  }
}

impl rosidl_runtime_rs::Message for GetObjectPose_Response {
  type RmwMsg = super::srv::rmw::GetObjectPose_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        pose: geometry_msgs::msg::PoseStamped::into_rmw_message(std::borrow::Cow::Owned(msg.pose)).into_owned(),
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        pose: geometry_msgs::msg::PoseStamped::into_rmw_message(std::borrow::Cow::Borrowed(&msg.pose)).into_owned(),
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      pose: geometry_msgs::msg::PoseStamped::from_rmw_message(msg.pose),
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to arjuna_camera__srv__ListObjects_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListObjects_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for ListObjects_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ListObjects_Request::default())
  }
}

impl rosidl_runtime_rs::Message for ListObjects_Request {
  type RmwMsg = super::srv::rmw::ListObjects_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
    }
  }
}


// Corresponds to arjuna_camera__srv__ListObjects_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ListObjects_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub labels: Vec<std::string::String>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub poses: Vec<geometry_msgs::msg::PoseStamped>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,

}



impl Default for ListObjects_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::ListObjects_Response::default())
  }
}

impl rosidl_runtime_rs::Message for ListObjects_Response {
  type RmwMsg = super::srv::rmw::ListObjects_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        labels: msg.labels
          .into_iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        poses: msg.poses
          .into_iter()
          .map(|elem| geometry_msgs::msg::PoseStamped::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
        success: msg.success,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        labels: msg.labels
          .iter()
          .map(|elem| elem.as_str().into())
          .collect(),
        poses: msg.poses
          .iter()
          .map(|elem| geometry_msgs::msg::PoseStamped::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      success: msg.success,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      labels: msg.labels
          .into_iter()
          .map(|elem| elem.to_string())
          .collect(),
      poses: msg.poses
          .into_iter()
          .map(geometry_msgs::msg::PoseStamped::from_rmw_message)
          .collect(),
      success: msg.success,
    }
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


