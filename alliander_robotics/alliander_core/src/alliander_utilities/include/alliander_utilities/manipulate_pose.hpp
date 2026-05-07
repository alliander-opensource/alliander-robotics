// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <tf2/convert.hpp>
#include <tf2/exceptions.hpp>
#include <tf2/time.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <tf2_ros/transform_listener.hpp>

#include "alliander_interfaces/srv/transform_pose_to_frame.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/transform.hpp"
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
  rclcpp::Service<alliander_interfaces::srv::TransformPoseToFrame>::SharedPtr
      transform_pose_to_frame_service_; /**< Service for
                                               TransformPoseToFrame */
  /** @brief Callback for the TransformPoseToFrame service
   * @param req The request message
   * @param resp The response message
   */
  void TransformPoseToFrame(
      const std::shared_ptr<
          alliander_interfaces::srv::TransformPoseToFrame::Request>
          req,
      std::shared_ptr<alliander_interfaces::srv::TransformPoseToFrame::Response>
          resp);
};
