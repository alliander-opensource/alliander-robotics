// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "meta_manager.hpp"

#include <tf2/exceptions.h>
#include <tf2/time.h>

MetaManager::MetaManager()
    : Node(
          "meta_manager",
          rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(
              true)) {
  // Declare parameters:
  try {
    namespace_arm = this->get_parameter("namespace_arm").as_string();
  } catch (const rclcpp::exceptions::ParameterNotDeclaredException& e) {
    RCLCPP_ERROR(this->get_logger(), "Parameter 'namespace_arm' is not set.");
  }
  namespace_meta = std::string(this->get_namespace()).erase(0, 1);

  // Initialize TF2:
  tf_buffer = std::make_shared<tf2_ros::Buffer>(this->get_clock());
  tf_listener = std::make_shared<tf2_ros::TransformListener>(*tf_buffer);
  tf_broadcaster = std::make_shared<tf2_ros::TransformBroadcaster>(this);

  // Subscriptions:
  sub_meta_tf = this->create_subscription<tf2_msgs::msg::TFMessage>(
      "/" + namespace_meta + "/tf", 10,
      std::bind(&MetaManager::callback_tf, this, std::placeholders::_1));
  sub_joystick = this->create_subscription<sensor_msgs::msg::Joy>(
      "/" + namespace_meta + "/joystick", 10,
      std::bind(&MetaManager::callback_joystick, this, std::placeholders::_1));

  // Publishers:
  pub_tf = this->create_publisher<tf2_msgs::msg::TFMessage>("/tf", 10);
  pub_servo_target = this->create_publisher<geometry_msgs::msg::PoseStamped>(
      "/franka/servo_node/pose_target_cmds", 10);

  // Clients:
  srv_client_arm_home =
      this->create_client<alliander_interfaces::srv::StringSrv>(
          "/" + namespace_arm + "/moveit_manager/move_to_configuration");
}

// Add timestamps to transforms, change "world" frame to "map" frame and prepend
// the namespace before republishing them on the global /tf topic:
void MetaManager::callback_tf(const tf2_msgs::msg::TFMessage::SharedPtr msg) {
  auto updated_msg = *msg;
  for (auto& transform : updated_msg.transforms) {
    transform.header.stamp = this->get_clock()->now();
    if (transform.header.frame_id == "world") {
      transform.header.frame_id = "map";
    } else {
      transform.header.frame_id =
          namespace_meta + "/" + transform.header.frame_id;
    }
    transform.child_frame_id = namespace_meta + "/" + transform.child_frame_id;
  }
  pub_tf->publish(updated_msg);
}

// Set the hand frame to the current pose of the end-effector when the
// joystick trigger is pressed, and publish the target frame as long as the
// trigger is held down.
void MetaManager::callback_joystick(
    const sensor_msgs::msg::Joy::SharedPtr msg) {
  // Return if the arm is busy:
  if (BUSY) {
    return;
  }

  // Move arm to home position when button A is pressed:
  auto BUTTON_A = bool(msg->buttons[1]);
  auto TRIGGER_PRESSED = bool(msg->axes[5] == 1.0f);
  if (!BUTTON_A) {
    BUTTON_A_PRESSED = false;
  }
  if (BUTTON_A && !BUTTON_A_PRESSED && !TRIGGER_PRESSED) {
    move_arm_to_home();
    BUTTON_A_PRESSED = true;
  }

  // Return if the trigger is not pressed:
  if (!TRIGGER_PRESSED) {
    OUTDATED = true;
    return;
  }

  // Update the end-effector frame if outdated:
  if (OUTDATED) {
    set_end_effector_target_to_current_pose();
    OUTDATED = false;
  }

  // Publish start positions of hand and end-effector:
  hand_start.header.stamp = this->get_clock()->now();
  tf_broadcaster->sendTransform(hand_start);
  end_effector_start.header.stamp = this->get_clock()->now();
  tf_broadcaster->sendTransform(end_effector_start);

  // Publish the target:
  publish_servo_target();
}

// Set the end-effector target to the current pose of the end-effector:
void MetaManager::set_end_effector_target_to_current_pose() {
  try {
    hand_start = tf_buffer->lookupTransform("map", "quest/hand_right",
                                            tf2::TimePointZero);
    hand_start.child_frame_id = "quest/hand_right_start";
    end_effector_start = tf_buffer->lookupTransform(
        "map", namespace_arm + "/fr3_hand_tcp", tf2::TimePointZero);
    end_effector_start.child_frame_id = "end_effector_start";
  } catch (const tf2::TransformException& e) {
    RCLCPP_ERROR(this->get_logger(), "Could not get transform: %s", e.what());
  }
}

// Publish the target frame on the tf and as pose for MoveIt Servo.
void MetaManager::publish_servo_target() {
  try {
    auto transform = tf_buffer->lookupTransform(
        "quest/hand_right_start", "quest/hand_right", tf2::TimePointZero);
    transform.header.frame_id = "end_effector_start";
    transform.child_frame_id = "end_effector_target";
    tf_broadcaster->sendTransform(transform);

    PoseStamped servo_target;
    servo_target.header.frame_id = "end_effector_start";
    servo_target.pose.position.x = transform.transform.translation.x;
    servo_target.pose.position.y = transform.transform.translation.y;
    servo_target.pose.position.z = transform.transform.translation.z;
    servo_target.pose.orientation = transform.transform.rotation;
    servo_target.header.stamp = this->get_clock()->now();
    pub_servo_target->publish(servo_target);
  } catch (const tf2::TransformException&) {
  }
}

// Move the arm to the home position and mark it as busy until completed:
void MetaManager::move_arm_to_home() {
  if (BUSY) {
    RCLCPP_INFO(this->get_logger(), "Arm already moving.");
    return;
  }
  BUSY = true;

  auto request = std::make_shared<StringSrv::Request>();
  request->text = "home";

  if (!srv_client_arm_home->service_is_ready()) {
    RCLCPP_WARN(this->get_logger(), "'Move arm' service not available.");
    BUSY = false;
    return;
  }

  srv_client_arm_home->async_send_request(
      request, [this](rclcpp::Client<StringSrv>::SharedFuture future) {
        try {
          auto response = future.get();

          if (response->success) {
            RCLCPP_DEBUG(this->get_logger(), "Arm moved home successfully.");
          } else {
            RCLCPP_WARN(this->get_logger(), "Move home failed.");
          }
        } catch (const std::exception& e) {
          RCLCPP_ERROR(this->get_logger(), "'Move arm' service call failed: %s",
                       e.what());
        }
        BUSY = false;
      });
}

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<MetaManager>();
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
}
