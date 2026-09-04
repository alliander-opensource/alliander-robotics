// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <rclcpp/executors.hpp>
#include <rclcpp/node.hpp>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "isaac_ros_apriltag_interfaces/msg/april_tag_detection_array.hpp"
using std::placeholders::_1;

typedef geometry_msgs::msg::PoseStamped PoseStamped;
typedef isaac_ros_apriltag_interfaces::msg::AprilTagDetectionArray
    AprilTagDetectionArray;

class ApriltagManager : public rclcpp::Node {
 public:
  ApriltagManager() : Node("apriltag_manager") {
    subscription_ = this->create_subscription<AprilTagDetectionArray>(
        "/tag_detections", 10,
        std::bind(&ApriltagManager::topic_callback, this, _1));
    publisher_ =
        this->create_publisher<PoseStamped>("/panther/detected_dock_pose", 10);
  }

 private:
  void topic_callback(const AprilTagDetectionArray::SharedPtr msg_sub) const {
    if (msg_sub->detections.empty()) {
      return;
    }
    PoseStamped msg_pub;
    msg_pub.header = msg_sub->header;
    msg_pub.pose = msg_sub->detections[0].pose.pose.pose;
    publisher_->publish(msg_pub);
  }

  rclcpp::Subscription<AprilTagDetectionArray>::SharedPtr subscription_;
  rclcpp::Publisher<PoseStamped>::SharedPtr publisher_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ApriltagManager>());
  rclcpp::shutdown();
  return 0;
}
