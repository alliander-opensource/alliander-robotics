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

#include "rcdt_interfaces/srv/express_pose_in_other_frame.hpp"
#include "rcdt_utilities/manipulate_pose.hpp"

/**
 * Class to test the package.
 */
class PackageTester : public rclcpp::Node {
 public:
  PackageTester() : Node("manipulate_pose_tester") {
    express_pose_in_other_frame_client_ =
        this->create_client<rcdt_interfaces::srv::ExpressPoseInOtherFrame>(
            "pose_manipulator/express_pose_in_other_frame");
  }

  /**
   * @brief Waits for the services to be available.
   * @param timeout The duration to wait for the services.
   * @return True if all services are available, false otherwise.
   */
  bool waitForServices(std::chrono::seconds timeout) {
    bool express_pose_in_other_frame_available =
        express_pose_in_other_frame_client_->wait_for_service(timeout);
    if (!express_pose_in_other_frame_available) {
      RCLCPP_ERROR(this->get_logger(),
                   "Service 'express_pose_in_other_frame' "
                   "not available within timeout.");
      return false;
    }

    return true;
  }

  /**
   * @brief Sends an ExpressPoseInOtherFrame service request.
   * @param req The ExpressPoseInOtherFrame request message.
   * @return A future and request ID for the service call.
   */
  rclcpp::Client<
      rcdt_interfaces::srv::ExpressPoseInOtherFrame>::FutureAndRequestId
  sendExpressPoseInOtherFrameRequest(
      std::shared_ptr<rcdt_interfaces::srv::ExpressPoseInOtherFrame::Request>
          req) {
    return express_pose_in_other_frame_client_->async_send_request(req);
  }

 private:
  rclcpp::Client<rcdt_interfaces::srv::ExpressPoseInOtherFrame>::SharedPtr
      express_pose_in_other_frame_client_; /**< Client to express pose in
                                             another coordinate frame */
};
