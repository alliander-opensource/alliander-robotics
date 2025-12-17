// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "rcdt_utilities/manipulate_pose.hpp"

PoseManipulator::PoseManipulator() : rclcpp::Node("pose_manipulator") {
  tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

  transform_pose_to_frame_service_ = this->create_service<
      rcdt_interfaces::srv::TransformPoseToFrame>(
      "~/transform_pose_to_frame",
      [this](
          std::shared_ptr<rcdt_interfaces::srv::TransformPoseToFrame::Request>
              req,
          std::shared_ptr<rcdt_interfaces::srv::TransformPoseToFrame::Response>
              resp) { this->TransformPoseToFrame(req, resp); });
}

void PoseManipulator::TransformPoseToFrame(
    const std::shared_ptr<rcdt_interfaces::srv::TransformPoseToFrame::Request>
        req,
    std::shared_ptr<rcdt_interfaces::srv::TransformPoseToFrame::Response>
        resp) {
  std::string source_frame = req->pose.header.frame_id;
  std::string target_frame = req->target_frame;

  geometry_msgs::msg::TransformStamped tf;
  try {
    tf = tf_buffer_->lookupTransform(target_frame, source_frame,
                                     rclcpp::Time(0));
  } catch (const tf2::TransformException& e) {
    RCLCPP_WARN(this->get_logger(),
                "Could not transform from frame %s to frame %s: %s",
                source_frame.c_str(), target_frame.c_str(), e.what());
    resp->success = false;
    return;
  }

  if (req->pose.header.frame_id != tf.child_frame_id) {
    RCLCPP_ERROR(this->get_logger(),
                 "Pose frame ID (%s) and Transform child frame ID (%s) are not "
                 "the same.",
                 req->pose.header.frame_id.c_str(), tf.child_frame_id.c_str());
  }

  try {
    tf2::doTransform(req->pose, resp->pose, tf);
  } catch (const tf2::TransformException& e) {
    RCLCPP_ERROR(this->get_logger(),
                 "Could not transform pose to frame %s: %s.",
                 target_frame.c_str(), e.what());
  }
  resp->success = true;
}
