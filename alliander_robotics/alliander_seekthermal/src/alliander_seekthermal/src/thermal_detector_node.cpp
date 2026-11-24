#include <thermal_detector.hpp>

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);

  rclcpp::executors::SingleThreadedExecutor executor;
  auto node = std::make_shared<ThermalDetector>();
  executor.add_node(node);

  executor.spin();

  rclcpp::shutdown();
  return 0;
}
