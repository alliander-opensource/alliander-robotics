// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

#ifndef KEEPOUT_ZONE_MANAGER_HPP_
#define KEEPOUT_ZONE_MANAGER_HPP_

#include <alliander_interfaces/msg/utm_datum.hpp>
#include <alliander_interfaces/srv/add_keepout_zone.hpp>
#include <cstdint>
#include <geographic_msgs/msg/geo_path.hpp>
#include <memory>
#include <nav_msgs/msg/occupancy_grid.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <utility>
#include <vector>

using alliander_interfaces::msg::UTMDatum;
using alliander_interfaces::srv::AddKeepoutZone;
using geographic_msgs::msg::GeoPath;
using nav_msgs::msg::OccupancyGrid;
using sensor_msgs::msg::NavSatFix;

/// Class to manage keepout zones in the navigation costmap.
class KeepoutZoneManager : public rclcpp::Node {
 public:
  /**
   * @brief Constructor for the KeepoutZoneManager class.
   *
   * Initializes the ROS2 node and its communication interfaces for managing
   * keepout zones.
   */
  KeepoutZoneManager();

 private:
  // Other variables:
  /// A point represented by its x and y coordinates.
  using Point = std::pair<double, double>;
  /// A polygon represented by a sequence of points.
  using Polygon = std::vector<Point>;

  /**
   * @brief Stores a keepout polygon in GPS and local coordinates.
   *
   * The GPS polygon contains geographic coordinates, while the local polygon
   * contains coordinates transformed into the local UTM reference frame.
   */
  struct StoredPolygon {
    /// Polygon represented by GPS latitude and longitude coordinates.
    Polygon gps;
    /// Polygon represented by local x and y coordinates.
    Polygon local;
  };

  // ROS2 communication variables:
  /// Subscriber that receives the UTM configuration.
  rclcpp::Subscription<UTMDatum>::SharedPtr utm_sub_;
  /// Subscriber that receives GPS position updates.
  rclcpp::Subscription<NavSatFix>::SharedPtr gps_sub_;
  /// Publisher that publishes the keepout zone occupancy grid.
  rclcpp::Publisher<OccupancyGrid>::SharedPtr keepout_zone_pub_;
  /// Service that handles requests to add a keepout zone.
  rclcpp::Service<AddKeepoutZone>::SharedPtr add_zone_srv_;

  // UTM configuration variables:
  /// UTM zone and hemisphere information used for coordinate conversions.
  UTMDatum utm_datum_;

  // Costmap configuration variables:
  /// Resolution of the keepout zone occupancy grid in metres per cell.
  double resolution_;
  /// Width of the keepout zone occupancy grid in cells.
  int width_;
  /// Height of the keepout zone occupancy grid in cells.
  int height_;

  /// X-coordinate of the occupancy grid origin in the local reference frame.
  double origin_x_;
  /// Y-coordinate of the occupancy grid origin in the local reference frame.
  double origin_y_;

  // Reference position variables:
  /// Latitude of the reference GPS position used for local coordinates.
  double utm_reference_lat_;
  /// Longitude of the reference GPS position used for local coordinates.
  double utm_reference_lon_;
  /// Indicates whether the reference GPS position has been initialized.
  bool reference_initialized_;

  /// Number of keepout zones added by the manager.
  int zone_count_;

  // Keepout zone data:
  /// Occupancy grid data representing the keepout zone mask.
  std::vector<int8_t> mask_data_;
  /// Polygons defining the stored keepout zones in GPS and local coordinates.
  std::vector<StoredPolygon> polygons_;

  /**
   * @brief Callback that processes incoming UTM configuration messages.
   * @param msg UTM datum message containing the zone and hemisphere
   * information.
   */
  void utmCallback(const UTMDatum::SharedPtr msg);

  /**
   * @brief Callback that processes the reference lat-lon coordinates based on
   * the incoming GPS position updates.
   * @param msg GPS message containing the current latitude and longitude.
   */
  void gpsCallback(const NavSatFix::SharedPtr msg);

  /**
   * @brief Callback that handles requests to add a keepout zone.
   * @param request Service request containing the keepout zone definition.
   * @param response Service response indicating the outcome of the request.
   */
  void addZoneCallback(const std::shared_ptr<AddKeepoutZone::Request> request,
                       std::shared_ptr<AddKeepoutZone::Response> response);

  /**
   * @brief Converts GPS coordinates into local x and y coordinates.
   * @param latitude GPS latitude in degrees.
   * @param longitude GPS longitude in degrees.
   * @return Point containing the local x and y coordinates in metres.
   */
  Point gpsToLocalXY(double latitude, double longitude) const;

  /**
   * @brief Converts a geographic path into a polygon in local coordinates.
   * @param path Geographic path containing the polygon's GPS coordinates.
   * @return Polygon containing the path points in local x and y coordinates.
   */
  Polygon gpsPathToPolygon(const GeoPath& path) const;

  /**
   * @brief Converts local coordinates into occupancy grid pixel coordinates for
   * the mask.
   * @param x Local x-coordinate in metres.
   * @param y Local y-coordinate in metres.
   * @return Point containing the corresponding occupancy grid pixel
   * coordinates.
   */
  Point localToPixel(double x, double y) const;

  /**
   * @brief Checks whether a point lies inside a polygon, such that these points
   * can be marked as occupied in the keepout zone mask.
   * @param x X-coordinate of the point.
   * @param y Y-coordinate of the point.
   * @param polygon Polygon against which the point is checked.
   * @return True if the point is inside the polygon, false otherwise.
   */
  bool pointInPolygon(double x, double y, const Polygon& polygon) const;

  /**
   * @brief Adds a polygon to the keepout zone occupancy grid.
   * @param polygon Polygon defining the keepout zone in local coordinates.
   * @return True if the polygon was added successfully, false otherwise.
   */
  bool addPolygonToMask(const Polygon& polygon);

  /**
   * @brief Rebuilds the occupancy grid to fit all stored keepout polygons
   * (within a reasonable size limit, otherwise the polygon will be rejected).
   *
   * @return True if the grid was rebuilt successfully, false otherwise.
   */
  bool rebuildMask();

  /**
   * @brief Publishes the current keepout zone occupancy grid.
   */
  void publishMask();
};

#endif  // KEEPOUT_ZONE_MANAGER_HPP_
