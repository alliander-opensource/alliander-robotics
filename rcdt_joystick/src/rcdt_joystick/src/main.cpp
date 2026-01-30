#include <sys/resource.h>

#include "rcdt_joystick/joystick_manager.hpp"


int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  rclcpp::Node::SharedPtr node = std::make_shared<rclcpp::Node>("rcdt_joystick");
  
  JoystickManager joystick_manager(node);

  rclcpp::spin(node);

  rclcpp::shutdown();
  return 0;
}