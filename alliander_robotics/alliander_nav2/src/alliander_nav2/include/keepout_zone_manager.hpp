// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef KEEPOUT_ZONE_MANAGER_HPP_
#define KEEPOUT_ZONE_MANAGER_HPP_

#include <alliander_interfaces/srv/add_keepout_zone.hpp>
#include <cstdint>
#include <memory>
#include <utility>
#include <vector>

#include "geographic_msgs/msg/geo_path.hpp"
#include "nav_msgs/msg/occupancy_grid.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/nav_sat_fix.hpp"

class KeepoutZoneManager : public rclcpp::Node {
 public:
  KeepoutZoneManager();

 private:
  using Point = std::pair<double, double>;
  using Polygon = std::vector<Point>;

  struct StoredPolygon {
    Polygon gps;
    Polygon local;
  };

  rclcpp::Subscription<sensor_msgs::msg::NavSatFix>::SharedPtr gps_subscriber_;
  rclcpp::Publisher<nav_msgs::msg::OccupancyGrid>::SharedPtr publisher_;
  rclcpp::Service<alliander_interfaces::srv::AddKeepoutZone>::SharedPtr srv_;

  double resolution_;
  int width_;
  int height_;

  double origin_x_;
  double origin_y_;

  double reference_lat_;
  double reference_lon_;
  bool reference_initialized_;

  int zone_count_;

  std::vector<int8_t> mask_data_;
  std::vector<StoredPolygon> polygons_;

  void gps_callback(const sensor_msgs::msg::NavSatFix::SharedPtr msg);
  void add_zone_callback(
      const std::shared_ptr<alliander_interfaces::srv::AddKeepoutZone::Request>
          request,
      std::shared_ptr<alliander_interfaces::srv::AddKeepoutZone::Response>
          response);
  Point gps_to_local_xy(double latitude, double longitude) const;
  Polygon gps_path_to_polygon(const geographic_msgs::msg::GeoPath& path) const;
  static double degrees_to_radians(double degrees);
  Point local_to_pixel(double x, double y) const;
  bool point_in_polygon(double x, double y, const Polygon& polygon) const;
  bool add_polygon_to_mask(const Polygon& polygon);
  void publish_mask();
};

#endif  // KEEPOUT_ZONE_MANAGER_HPP_
