// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <tf2/convert.hpp>
#include <tf2/exceptions.hpp>
#include <tf2/time.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <tf2_ros/transform_listener.hpp>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/transform.hpp"
#include "rcdt_messages/srv/express_pose_in_other_frame.hpp"
#include "rcdt_messages/srv/transform_pose.hpp"
#include "tf2_ros/buffer.hpp"

/**
 * Class to manipulate poses using TF2.
 */
class PoseManipulator : public rclcpp::Node {
 public:
  PoseManipulator();

 private:
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_{
      nullptr};                                /**< TF2 Transform Listener */
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_; /**< TF2 Transform Buffer */

  // Services
  rclcpp::Service<rcdt_messages::srv::ExpressPoseInOtherFrame>::SharedPtr
      express_pose_in_other_frame_service_; /**< Service for
                                               ExpressPoseInOtherFrame */
  /** @brief Callback for the ExpressPoseInOtherFrame service
   * @param req The request message
   * @param resp The response message
   */
  void expressPoseInOtherFrame(
      const std::shared_ptr<
          rcdt_messages::srv::ExpressPoseInOtherFrame::Request>
          req,
      std::shared_ptr<rcdt_messages::srv::ExpressPoseInOtherFrame::Response>
          resp);

  rclcpp::Service<rcdt_messages::srv::TransformPose>::SharedPtr
      transform_pose_service_; /**< Service for TransformPose */
  /** @brief Callback for the TransformPose service
   * @param req The request message
   * @param resp The response message
   */
  void transformPose(
      const std::shared_ptr<rcdt_messages::srv::TransformPose::Request> req,
      std::shared_ptr<rcdt_messages::srv::TransformPose::Response> resp);

  rclcpp::Service<rcdt_messages::srv::TransformPose>::SharedPtr
      transform_pose_relative_service_; /**< Service for TransformPoseRelative
                                         */
  /** @brief Callback for the TransformPoseRelative service
   * @param req The request message
   * @param resp The response message
   */
  void transformPoseRelative(
      const std::shared_ptr<rcdt_messages::srv::TransformPose::Request> req,
      std::shared_ptr<rcdt_messages::srv::TransformPose::Response> resp);

  /** @brief Transforms a pose using a given transform
   * @param pose_in The input pose
   * @param tf The transform to apply
   * @return The transformed pose
   */
  geometry_msgs::msg::PoseStamped doTransform(
      const geometry_msgs::msg::PoseStamped pose_in,
      const geometry_msgs::msg::Transform tf);
};
