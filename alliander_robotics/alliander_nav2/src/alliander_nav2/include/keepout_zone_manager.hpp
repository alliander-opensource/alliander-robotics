// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

#ifndef KEEPOUT_ZONE_MANAGER_HPP_
#define KEEPOUT_ZONE_MANAGER_HPP_

#include <tf2/time.h>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

#include <alliander_interfaces/msg/utm_datum.hpp>
#include <alliander_interfaces/srv/manage_keepout_zones.hpp>
#include <cstdint>
#include <geographic_msgs/msg/geo_path.hpp>
#include <memory>
#include <nav_msgs/msg/occupancy_grid.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <utility>
#include <vector>

using alliander_interfaces::msg::UTMDatum;
using alliander_interfaces::srv::ManageKeepoutZones;
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
   * @brief Stores a keepout zone in GPS and local coordinates.
   *
   * The GPS zone contains geographic coordinates, while the local zone contains
   * coordinates transformed into the local UTM reference frame.
   */
  struct StoredZones {
    /// Unique ID of the zone.
    std::uint64_t id;
    /// Zone's polygon represented by GPS latitude and longitude coordinates.
    Polygon gps;
    /// Zone's polygon represented by local x and y coordinates.
    Polygon local;
  };

  // ROS2 communication variables:
  /// Subscriber that receives the UTM configuration.
  rclcpp::Subscription<UTMDatum>::SharedPtr utm_sub_;
  /// Publisher that publishes the keepout zone occupancy grid.
  rclcpp::Publisher<OccupancyGrid>::SharedPtr keepout_zone_pub_;
  /// Service that adds or removes keepout zones.
  rclcpp::Service<ManageKeepoutZones>::SharedPtr manage_zones_srv_;

  // UTM configuration variables:
  /// UTM zone and hemisphere information used for coordinate conversions.
  UTMDatum utm_datum_;
  /// Indicates whether the UTM datum has been initialized.
  bool utm_datum_initialized_;

  // Costmap configuration variables:
  /// Resolution of the keepout zone occupancy grid in metres per cell.
  double resolution_;
  /// Width of the keepout zone occupancy grid in cells.
  int width_;
  /// Height of the keepout zone occupancy grid in cells.
  int height_;

  /// X-coordinate of the occupancy grid origin in the local reference frame.
  double grid_origin_x_;
  /// Y-coordinate of the occupancy grid origin in the local reference frame.
  double grid_origin_y_;

  /// ID to assign to the next newly created zone.
  std::uint64_t next_zone_id_;

  // Keepout zone data:
  /// Occupancy grid data representing the keepout zone mask.
  std::vector<int8_t> mask_data_;
  /// Polygons defining the stored keepout zones in GPS and local coordinates.
  std::vector<StoredZones> zones_;

  // Wait for TF
  /// TF buffer and listener.
  std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;

  /// Timer that waits for the required TF transforms.
  rclcpp::TimerBase::SharedPtr initial_mask_timer_;

  /// Prevent publishing the initial mask before TF is ready.
  bool initial_mask_published_{false};

  /**
   * @brief Checks whether the TF UTM transform is available.
   */
  void waitForUtmTransform();

  /**
   * @brief Callback that processes incoming UTM configuration messages.
   * @param msg UTM datum message containing the zone and hemisphere
   * information.
   */
  void utmCallback(const UTMDatum::SharedPtr msg);

  /**
   * @brief Handles requests to add or remove all remove keepout zones.
   * @param request Request describing the operation and its arguments.
   * @param response Response containing the operation result and affected IDs.
   */
  void manageZonesCallback(
      const std::shared_ptr<ManageKeepoutZones::Request> request,
      std::shared_ptr<ManageKeepoutZones::Response> response);

  /**
   * @brief Handles requests to add keepout zones.
   * @param request Request describing the operation and its arguments.
   * @param response Response containing the operation result and affected IDs.
   */
  void addZones(const std::shared_ptr<ManageKeepoutZones::Request> request,
                std::shared_ptr<ManageKeepoutZones::Response> response);

  /**
   * @brief Handles requests to remove a specific keepout zone.
   * @param request Request describing the operation and its arguments.
   * @param response Response containing the operation result and affected IDs.
   */
  void removeSingleZone(
      const std::shared_ptr<ManageKeepoutZones::Request> request,
      std::shared_ptr<ManageKeepoutZones::Response> response);

  /**
   * @brief Handles requests to remove all keepout zones.
   * @param response Response containing the operation result and affected IDs.
   */
  void removeAllZones(std::shared_ptr<ManageKeepoutZones::Response> response);

  /**
   * @brief Converts GPS coordinates into local x and y coordinates.
   * @param latitude GPS latitude in degrees.
   * @param longitude GPS longitude in degrees.
   * @return Point containing the local x and y coordinates in metres.
   */
  Point gpsToLocalXY(double latitude, double longitude)
      const;  // TODO: since the gps topic is now removed, look into renaming
              // the functions with gps in the name

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
   * @brief Rebuilds the occupancy grid to fit all stored zones (within a
   * reasonable size limit, otherwise the zone will be rejected).
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
