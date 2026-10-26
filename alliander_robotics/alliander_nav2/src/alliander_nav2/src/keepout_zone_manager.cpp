// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <functional>
#include <memory>
#include <string>

#include "keepout_zone_manager.hpp"
#include "rclcpp/qos.hpp"

KeepoutZoneManager::KeepoutZoneManager()
    : Node("keepout_zone_manager"),
      resolution_(0.1),
      width_(400),
      height_(400),
      origin_x_(-10.0),
      origin_y_(-10.0),
      reference_lat_(0.0),
      reference_lon_(0.0),
      reference_initialized_(false),
      zone_count_(0) {
  gps_subscriber_ = create_subscription<sensor_msgs::msg::NavSatFix>(
      "/ublox/gps/fix", 10,
      std::bind(&KeepoutZoneManager::gps_callback, this,
                std::placeholders::_1)); // TODO: hard-coded topic!

  const auto mask_qos =
      rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local();

  publisher_ = create_publisher<nav_msgs::msg::OccupancyGrid>(
      "/panther/keepout_filter_mask", mask_qos); // TODO: hard-coded topic!

  srv_ = create_service<alliander_interfaces::srv::AddKeepoutZone>(
      "/add_ui_nogozone",
      std::bind(&KeepoutZoneManager::add_zone_callback, this,
                std::placeholders::_1, std::placeholders::_2));

  mask_data_.assign(static_cast<std::size_t>(width_) * height_, 0);

  publish_mask();

  RCLCPP_INFO(get_logger(), "Dynamic GPS Keepout Publisher initialized.");
  RCLCPP_INFO(get_logger(), "Waiting for the first valid GPS fix.");
}

void KeepoutZoneManager::gps_callback(
    const sensor_msgs::msg::NavSatFix::SharedPtr msg) {
  if (msg->status.status < 0) {
    RCLCPP_WARN(get_logger(), "Invalid GPS fix received.");
    return;
  }

  if (!reference_initialized_) {
    reference_lat_ = msg->latitude;
    reference_lon_ = msg->longitude;
    reference_initialized_ = true;

    RCLCPP_INFO(get_logger(),
                "GPS reference set: latitude=%.8f, longitude=%.8f",
                reference_lat_, reference_lon_);
  }
}

double KeepoutZoneManager::degrees_to_radians(double degrees) {
  constexpr double pi = 3.14159265358979323846;
  return degrees * pi / 180.0;
}

KeepoutZoneManager::Point KeepoutZoneManager::gps_to_local_xy(
    double latitude, double longitude) const {
  constexpr double earth_radius = 6378137.0;

  const double delta_lat = degrees_to_radians(latitude - reference_lat_);
  const double delta_lon = degrees_to_radians(longitude - reference_lon_);
  const double reference_lat_rad = degrees_to_radians(reference_lat_);

  const double north = earth_radius * delta_lat;
  const double east = earth_radius * std::cos(reference_lat_rad) * delta_lon;

  return {east, north};
}

KeepoutZoneManager::Polygon KeepoutZoneManager::gps_path_to_polygon(
    const geographic_msgs::msg::GeoPath& path) const {
  Polygon polygon;
  polygon.reserve(path.poses.size());

  for (const auto& pose : path.poses) {
    polygon.push_back(gps_to_local_xy(pose.pose.position.latitude,
                                      pose.pose.position.longitude));
  }

  return polygon;
}

KeepoutZoneManager::Point KeepoutZoneManager::local_to_pixel(double x,
                                                             double y) const {
  return {std::trunc((x - origin_x_) / resolution_),
          std::trunc((y - origin_y_) / resolution_)};
}

bool KeepoutZoneManager::point_in_polygon(double x, double y,
                                          const Polygon& polygon) const {
  if (polygon.size() < 3) {
    return false;
  }

  bool inside = false;

  auto previous = polygon.back();

  for (const auto& current : polygon) {
    const auto [current_x, current_y] = current;
    const auto [previous_x, previous_y] = previous;

    if ((current_y > y) != (previous_y > y)) {
      const double intersection_x = (previous_x - current_x) * (y - current_y) /
                                        (previous_y - current_y) +
                                    current_x;

      if (x < intersection_x) {
        inside = !inside;
      }
    }

    previous = current;
  }

  return inside;
}

bool KeepoutZoneManager::add_polygon_to_mask(const Polygon& polygon) {
  if (polygon.size() < 3) {
    return false;
  }

  double min_x = polygon.front().first;
  double max_x = min_x;
  double min_y = polygon.front().second;
  double max_y = min_y;

  for (const auto& [x, y] : polygon) {
    min_x = std::min(min_x, x);
    max_x = std::max(max_x, x);
    min_y = std::min(min_y, y);
    max_y = std::max(max_y, y);
  }

  const auto [min_px_value, min_py_value] = local_to_pixel(min_x, min_y);
  const auto [max_px_value, max_py_value] = local_to_pixel(max_x, max_y);

  const int min_px = std::max(0, static_cast<int>(min_px_value));
  const int min_py = std::max(0, static_cast<int>(min_py_value));
  const int max_px = std::min(width_ - 1, static_cast<int>(max_px_value));
  const int max_py = std::min(height_ - 1, static_cast<int>(max_py_value));

  if (min_px > max_px || min_py > max_py) {
    return false;
  }

  for (int pixel_y = min_py; pixel_y <= max_py; ++pixel_y) {
    for (int pixel_x = min_px; pixel_x <= max_px; ++pixel_x) {
      const double world_x = origin_x_ + (pixel_x + 0.5) * resolution_;
      const double world_y = origin_y_ + (pixel_y + 0.5) * resolution_;

      if (point_in_polygon(world_x, world_y, polygon)) {
        const auto index = static_cast<std::size_t>(pixel_y) * width_ + pixel_x;

        mask_data_[index] = 100;
      }
    }
  }

  return true;
}

void KeepoutZoneManager::add_zone_callback(
    const std::shared_ptr<alliander_interfaces::srv::AddKeepoutZone::Request>
        request,
    std::shared_ptr<alliander_interfaces::srv::AddKeepoutZone::Response>
        response) {
  if (!reference_initialized_) {
    response->success = false;
    response->message = "No GPS reference is available.";
    return;
  }

  if (request->path.poses.size() < 3) {
    response->success = false;
    response->message = "The polygon must contain at least three points.";
    return;
  }

  const Polygon local_polygon = gps_path_to_polygon(request->path);

  for (const auto& [x, y] : local_polygon) {
    if (!std::isfinite(x) || !std::isfinite(y)) {
      response->success = false;
      response->message = "The polygon contains invalid GPS coordinates.";
      return;
    }
  }

  if (!add_polygon_to_mask(local_polygon)) {
    response->success = false;
    response->message = "The polygon is invalid or entirely outside the map.";
    return;
  }

  Polygon gps_polygon;
  gps_polygon.reserve(request->path.poses.size());

  for (const auto& pose : request->path.poses) {
    gps_polygon.emplace_back(pose.pose.position.latitude,
                             pose.pose.position.longitude);
  }

  polygons_.push_back({gps_polygon, local_polygon});

  ++zone_count_;

  publish_mask();

  RCLCPP_INFO(get_logger(), "Keepout polygon #%d created with %zu points.",
              zone_count_, local_polygon.size());

  response->success = true;
  response->message =
      "Keepout polygon #" + std::to_string(zone_count_) + " added.";
}

void KeepoutZoneManager::publish_mask() {
  nav_msgs::msg::OccupancyGrid msg;

  msg.header.stamp = get_clock()->now();
  msg.header.frame_id = "map";

  msg.info.resolution = static_cast<float>(resolution_);
  msg.info.width = static_cast<std::uint32_t>(width_);
  msg.info.height = static_cast<std::uint32_t>(height_);

  msg.info.origin.position.x = origin_x_;
  msg.info.origin.position.y = origin_y_;
  msg.info.origin.orientation.w = 1.0;

  msg.data = mask_data_;

  publisher_->publish(msg);
}

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);

  rclcpp::spin(std::make_shared<KeepoutZoneManager>());

  rclcpp::shutdown();

  return 0;
}
