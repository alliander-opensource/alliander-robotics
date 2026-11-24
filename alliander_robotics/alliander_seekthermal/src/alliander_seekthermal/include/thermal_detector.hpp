#include <opencv2/opencv.hpp>
#include <rclcpp/publisher.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>

constexpr size_t IMAGE_WIDTH = 320;
constexpr size_t IMAGE_HEIGHT = 240;

struct Hotspot {
  cv::Point2d centroid;
  float mean_temperature;
  float max_temperature;
  int area;
  cv::Mat label;
  cv::Mat stats;
};

class ThermalDetector : public rclcpp::Node {
 public:
  ThermalDetector();

 private:
  void dataCallback(const std_msgs::msg::Float32MultiArray::SharedPtr msg);
  void onTimer();

  cv::Mat threshold(const cv::Mat data);
  void removeNoise(const cv::Mat mask);
  std::vector<Hotspot> createHotspots(const cv::Mat mask);
  void overlayHotspots(const cv::Mat& mask,
                       const std::vector<Hotspot>& hotspots);

  cv::Mat temperature_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr sub_data_;
  rclcpp::TimerBase::SharedPtr timer_;

  // for debugging, remove later
  sensor_msgs::msg::Image image_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_intermediate_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_image_;
  void publishDebugImage(cv::Mat mat);
};
