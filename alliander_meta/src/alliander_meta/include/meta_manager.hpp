// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/transform_listener.h>

#include <alliander_interfaces/srv/string_srv.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <moveit_msgs/srv/servo_command_type.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>

typedef geometry_msgs::msg::PoseStamped PoseStamped;
typedef geometry_msgs::msg::TransformStamped TransformStamped;
typedef sensor_msgs::msg::Joy Joy;
typedef alliander_interfaces::srv::StringSrv StringSrv;
typedef moveit_msgs::srv::ServoCommandType ServoCommandType;

/// Class to interact with a Meta Quest 3.
class MetaManager : public rclcpp::Node {
 public:
  MetaManager();

 private:
  /// Namespace meta:
  std::string namespace_meta;
  /// Namespace arm:
  std::string namespace_arm;

  // TF2
  /// Buffer storing incoming transforms
  std::shared_ptr<tf2_ros::Buffer> tf_buffer;
  /// Listener that populates tf_buffer_
  std::shared_ptr<tf2_ros::TransformListener> tf_listener;
  /// Broadcaster used to publish the end-effector target frame
  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster;

  // Subscriptions
  /// Subscriber for joystick input from the Meta Quest controller
  rclcpp::Subscription<Joy>::SharedPtr sub_joystick;

  // Publishers
  /// Publisher for republishing Meta Quest TF frames onto the global /tf topic:
  rclcpp::Publisher<PoseStamped>::SharedPtr pub_servo_target;

  // Clients
  /// Client to move the arm back to home position
  rclcpp::Client<StringSrv>::SharedPtr srv_client_arm_home;
  /// Client to change the command type of the servo node
  rclcpp::Client<ServoCommandType>::SharedPtr
      srv_client_switch_servo_command_type;

  // State
  /// True when the end-effector target must be reset
  bool OUTDATED = true;
  /// True when the arm is currently moving using a service call
  bool BUSY = false;
  /// Start of the hand frame when the trigger is pressed
  TransformStamped hand_start;
  /// Start of the end-effector target frame when the trigger is pressed
  TransformStamped end_effector_start;

  /**
   * @brief Callback for incoming joystick messages from the Meta Quest.
   * @param msg the incoming joystick message
   */
  void callback_joystick(const Joy::SharedPtr msg);
  /// Initialise the end-effector target to the robot's current link pose
  void set_end_effector_target_to_current_pose();
  /// Look up the end-effector target in the map frame and publish it
  void publish_servo_target();
  /// Call the service to move the robot arm to its home position
  void move_arm_to_home();
  /// Call the service to switch the command type of the servo node
  void switch_servo_command_type();
};
