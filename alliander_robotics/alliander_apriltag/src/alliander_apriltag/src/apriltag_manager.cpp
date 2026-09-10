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

/// Manager for handling AprilTag detections and publishing corresponding poses.
class ApriltagManager : public rclcpp::Node {
 public:
  ApriltagManager() : Node("apriltag_manager") {
    this->declare_parameter("tag_ids", std::vector<int>{});
    this->declare_parameter("publish_topics", std::vector<std::string>{});

    auto tag_ids = this->get_parameter("tag_ids").as_integer_array();
    auto publish_topics =
        this->get_parameter("publish_topics").as_string_array();
    if (tag_ids.size() != publish_topics.size()) {
      RCLCPP_ERROR(
          this->get_logger(),
          "The number of tag IDs must match the number of pose topics.");
      return;
    }

    for (int i = 0; i < publish_topics.size(); i++) {
      auto tag_id = tag_ids[i];
      auto publish_topic = publish_topics[i];
      if (publish_topic.empty()) {
        RCLCPP_WARN(this->get_logger(),
                    "Publish topic is empty for tag ID %ld. No publisher will "
                    "be created for this tag.",
                    tag_id);
        continue;
      }
      if (publishers.count(tag_id)) {
        RCLCPP_WARN(this->get_logger(),
                    "Publisher already exists for tag ID %ld. No new publisher "
                    "will be created.",
                    tag_id);
        continue;
      }
      auto publisher = this->create_publisher<PoseStamped>(publish_topic, 10);
      publishers.insert({tag_id, publisher});
    }

    subscription = this->create_subscription<AprilTagDetectionArray>(
        "/tag_detections", 10,
        std::bind(&ApriltagManager::detection_callback, this, _1));
  }

 private:
  /**
   * @brief Callback function for handling AprilTag detections.
   * @param msg_sub The AprilTagDetectionArray message containing detected tags.
   */
  void detection_callback(
      const AprilTagDetectionArray::SharedPtr msg_sub) const {
    for (auto detection : msg_sub->detections) {
      if (detection.family != "tag36h11") continue;
      if (publishers.count(detection.id)) {
        PoseStamped msg_pub;
        msg_pub.header = msg_sub->header;
        msg_pub.pose = detection.pose.pose.pose;
        publishers.at(detection.id)->publish(msg_pub);
      }
    }
  }

  /// Map of tag IDs to their corresponding publishers.
  std::map<int, rclcpp::Publisher<PoseStamped>::SharedPtr> publishers;
  /// Subscription to the AprilTag detection topic.
  rclcpp::Subscription<AprilTagDetectionArray>::SharedPtr subscription;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ApriltagManager>());
  rclcpp::shutdown();
  return 0;
}
