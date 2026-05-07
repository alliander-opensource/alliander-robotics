// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <gtest/gtest.h>

#include <chrono>
#include <rclcpp/duration.hpp>
#include <rclcpp/executors.hpp>
#include <rclcpp/executors/multi_threaded_executor.hpp>
#include <rclcpp/executors/single_threaded_executor.hpp>
#include <rclcpp/future_return_code.hpp>
#include <rclcpp/rclcpp.hpp>

#include "alliander_interfaces/srv/transform_pose_to_frame.hpp"
#include "alliander_utilities/manipulate_pose.hpp"

/**
 * Class to test the package.
 */
class PackageTester : public rclcpp::Node {
 public:
  PackageTester() : Node("manipulate_pose_tester") {
    transform_pose_to_frame_client_ =
        this->create_client<alliander_interfaces::srv::TransformPoseToFrame>(
            "pose_manipulator/transform_pose_to_frame");
  }

  /**
   * @brief Waits for the services to be available.
   * @param timeout The duration to wait for the services.
   * @return True if all services are available, false otherwise.
   */
  bool waitForServices(std::chrono::seconds timeout) {
    bool transform_pose_to_frame_available =
        transform_pose_to_frame_client_->wait_for_service(timeout);
    if (!transform_pose_to_frame_available) {
      RCLCPP_ERROR(this->get_logger(),
                   "Service 'transform_pose_to_frame' "
                   "not available within timeout.");
      return false;
    }

    return true;
  }

  /**
   * @brief Sends an TransformPoseToFrame service request.
   * @param req The TransformPoseToFrame request message.
   * @return A future and request ID for the service call.
   */
  rclcpp::Client<
      alliander_interfaces::srv::TransformPoseToFrame>::FutureAndRequestId
  sendTransformPoseToFrameRequest(
      std::shared_ptr<alliander_interfaces::srv::TransformPoseToFrame::Request>
          req) {
    return transform_pose_to_frame_client_->async_send_request(req);
  }

 private:
  rclcpp::Client<alliander_interfaces::srv::TransformPoseToFrame>::SharedPtr
      transform_pose_to_frame_client_; /**< Client to express pose in
                                             another coordinate frame */
};
