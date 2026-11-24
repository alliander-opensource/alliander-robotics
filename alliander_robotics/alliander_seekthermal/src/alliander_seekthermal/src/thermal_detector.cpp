#include "thermal_detector.hpp"

#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/core.hpp>
#include <opencv2/core/base.hpp>
#include <opencv2/core/mat.hpp>
#include <opencv2/opencv.hpp>
#include <rclcpp/create_subscription.hpp>
#include <rclcpp/create_timer.hpp>
#include <sensor_msgs/image_encodings.hpp>

#include "std_msgs/msg/float32_multi_array.hpp"
#include "std_msgs/msg/header.hpp"

constexpr float MINIMUM_DETECTION_TEMPERATURE = 20.0;

ThermalDetector::ThermalDetector() : rclcpp::Node("thermal_detector") {
  sub_data_ = create_subscription<std_msgs::msg::Float32MultiArray>(
      "/topic_in_data", 1,
      [this](const std_msgs::msg::Float32MultiArray::SharedPtr msg) {
        dataCallback(msg);
      });
  timer_ = create_wall_timer(std::chrono::milliseconds(250),
                             [this]() { onTimer(); });

  pub_hotspots_image_ =
      create_publisher<sensor_msgs::msg::Image>("/topic_out_hotspots", 1);
}

void ThermalDetector::dataCallback(
    const std_msgs::msg::Float32MultiArray::SharedPtr msg) {
  if (msg->data.size() != IMAGE_WIDTH * IMAGE_HEIGHT) {
    RCLCPP_ERROR(get_logger(), "Unexpected image size %zu (expected %zux%zu)",
                 msg->data.size(), IMAGE_WIDTH, IMAGE_HEIGHT);
    return;
  }

  temperature_ =
      cv::Mat(IMAGE_HEIGHT, IMAGE_WIDTH, CV_32FC1, msg->data.data()).clone();
}

void ThermalDetector::onTimer() {
  if (temperature_.empty()) {
    return;
  }

  // all spots over X degrees Celsius
  auto mask = threshold(temperature_);

  // remove small spots of heat
  removeNoise(mask);

  // create Hotspots with centroid, temperature, etc
  auto hotspots = createHotspots(mask);

  // overlay the hotspots and publish
  overlayHotspots(mask, hotspots);
}

cv::Mat ThermalDetector::threshold(const cv::Mat data) {
  cv::Mat mask;
  cv::compare(data, MINIMUM_DETECTION_TEMPERATURE, mask, cv::CMP_GT);

  return mask;
}

void ThermalDetector::removeNoise(const cv::Mat mask) {
  // use morphological opening (erosion + dilation) to remove noise
  const auto kernel =
      cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(3, 3));
  cv::morphologyEx(mask, mask, cv::MORPH_OPEN, kernel);
}

std::vector<Hotspot> ThermalDetector::createHotspots(const cv::Mat mask) {
  cv::Mat labels, stats, centroids;
  const int count =
      cv::connectedComponentsWithStats(mask, labels, stats, centroids);
  RCLCPP_DEBUG(get_logger(), "Found %d hotspots", count);

  std::vector<Hotspot> hotspots;

  for (int label = 1; label < count; ++label) {
    const int area = stats.at<int>(label, cv::CC_STAT_AREA);

    if (area < 10) continue;

    cv::Mat component_mask = labels == label;

    const double mean_temperature = cv::mean(temperature_, component_mask)[0];

    double min_temperature, max_temperature;

    cv::minMaxLoc(temperature_, &min_temperature, &max_temperature, nullptr,
                  nullptr, component_mask);

    Hotspot hotspot;
    hotspot.max_temperature = max_temperature;
    hotspot.mean_temperature = mean_temperature;
    hotspot.area = area;
    hotspot.centroid = centroids.at<cv::Point2d>(label);
    hotspot.label = label;
    hotspot.stats = stats.at<int>(label);

    RCLCPP_INFO(
        get_logger(),
        "Created hotspot %d: (%.1f, %.1f), temp: mean %.1f / max %.1f, area: "
        "%d",
        label, hotspot.centroid.x, hotspot.centroid.y, hotspot.mean_temperature,
        hotspot.max_temperature, hotspot.area);

    hotspots.emplace_back(hotspot);
  }

  return hotspots;
}

void ThermalDetector::overlayHotspots(const cv::Mat& mask,
                                      const std::vector<Hotspot>& hotspots) {
  // convert temperature to 8-bit values ( 0 - 100 C)
  cv::Mat clipped;
  cv::max(temperature_, 0., clipped);
  cv::min(clipped, 100., clipped);
  cv::Mat temperature_8u;
  clipped.convertTo(temperature_8u, CV_8UC1, 255.0 / 100.0, 0.0);

  // colorized thermal image
  cv::Mat overlay;
  cv::applyColorMap(temperature_8u, overlay, cv::COLORMAP_INFERNO);

  // hotspot contours
  std::vector<std::vector<cv::Point>> contours;
  cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
  cv::drawContours(overlay, contours, -1, cv::Scalar(0, 255, 0), 2);

  for (const auto& hotspot : hotspots) {
    const cv::Point center{static_cast<int>(std::round(hotspot.centroid.x)),
                           static_cast<int>(std::round(hotspot.centroid.y))};
    // circle at centroid
    cv::circle(overlay, center, 3, cv::Scalar(255, 255, 255), cv::FILLED,
               cv::LINE_AA);

    // text display
    const std::string text = cv::format(
        "%.1f / %.1f C", hotspot.mean_temperature, hotspot.max_temperature);
    cv::putText(overlay, text, center + cv::Point(5, -5),
                cv::FONT_HERSHEY_SIMPLEX, 0.4, cv::Scalar(255, 255, 255), 1,
                cv::LINE_AA);
  }

  auto msg = cv_bridge::CvImage(std_msgs::msg::Header{},
                                sensor_msgs::image_encodings::BGR8, overlay)
                 .toImageMsg();

  msg->header.stamp = get_clock()->now();
  msg->header.frame_id = "seekthermal/base_link";

  pub_hotspots_image_->publish(*msg);
}
