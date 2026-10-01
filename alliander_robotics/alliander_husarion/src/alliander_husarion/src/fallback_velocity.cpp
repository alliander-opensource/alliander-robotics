// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <chrono>
#include <rclcpp/executors.hpp>
#include <rclcpp/node.hpp>

#include "geometry_msgs/msg/twist_stamped.hpp"

using std::chrono_literals;

typedef geometry_msgs::msg::TwistStamped TwistStamped;

/// Publishes a zero velocity command as a fallback for twist_mux.
class CmdVelFallback : public rclcpp::Node {
 public:
  CmdVelFallback() : Node("cmd_vel_fallback") {
    publisher = this->create_publisher<TwistStamped>("cmd_vel_fallback", 10);

    timer = this->create_wall_timer(
        50ms, std::bind(&CmdVelFallback::publish_zero_velocity, this));

    RCLCPP_INFO(this->get_logger(),
                "Publishing zero velocity fallback at 20 Hz");
  }

 private:
  /**
   * @brief Publish a zero velocity command.
   */
  void publish_zero_velocity() {
    TwistStamped msg;

    msg.header.stamp = this->now();

    msg.twist.linear.x = 0.0;
    msg.twist.linear.y = 0.0;
    msg.twist.linear.z = 0.0;

    msg.twist.angular.x = 0.0;
    msg.twist.angular.y = 0.0;
    msg.twist.angular.z = 0.0;

    publisher->publish(msg);
  }

  /// Publisher for the fallback velocity command.
  rclcpp::Publisher<TwistStamped>::SharedPtr publisher;

  /// Timer used to periodically publish the zero velocity command.
  rclcpp::TimerBase::SharedPtr timer;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CmdVelFallback>());
  rclcpp::shutdown();
  return 0;
}
