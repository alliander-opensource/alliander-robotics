// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

#include "keepout_zone_manager.hpp"

#include <GeographicLib/UTMUPS.hpp>
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <limits>
#include <memory>
#include <new>
#include <string>

#include "rclcpp/qos.hpp"

using std::placeholders::_1;
using std::placeholders::_2;

KeepoutZoneManager::KeepoutZoneManager()
    : Node("keepout_zone_manager"),
      resolution_(0.1),
      width_(1),
      height_(1),
      origin_x_(0.0),
      origin_y_(0.0),
      utm_reference_lat_(0.0),
      utm_reference_lon_(0.0),
      reference_initialized_(false),
      zone_count_(0),
      next_zone_id_(1) {
  rclcpp::QoS qos(1);
  qos.transient_local();

  utm_sub_ = create_subscription<UTMDatum>(
      "/utm_datum", qos, std::bind(&KeepoutZoneManager::utmCallback, this, _1));
  gps_sub_ = create_subscription<NavSatFix>(
      "/gps/fix", 10, std::bind(&KeepoutZoneManager::gpsCallback, this, _1));

  const auto mask_qos =
      rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local();

  keepout_zone_pub_ =
      create_publisher<OccupancyGrid>("/keepout_filter_mask", mask_qos);

  manage_zones_srv_ = create_service<ManageKeepoutZones>(
      "/manage_nogozones",
      std::bind(&KeepoutZoneManager::manageZonesCallback, this, _1, _2));

  // Start with a minimal, empty grid. Its dimensions will grow to fit the
  // stored polygons when keepout zones are added.
  mask_data_.assign(1, 0);

  publishMask();

  RCLCPP_INFO(get_logger(), "Dynamic GPS Keepout Publisher initialized.");
}

void KeepoutZoneManager::utmCallback(const UTMDatum::SharedPtr msg) {
  utm_datum_ = *msg;
}

void KeepoutZoneManager::gpsCallback(const NavSatFix::SharedPtr msg) {
  if (msg->status.status < 0) {
    RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 5000,
                         "Invalid GPS fix received.");
    return;
  }

  // Check if a valid UTM datum has been set.
  if (utm_datum_.zone < 1 || utm_datum_.zone > 60) {
    RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 5000,
                         "No valid UTM zone set. Cannot convert plan to GPS.");
    return;
  }

  if (!reference_initialized_) {
    bool northp = utm_datum_.northp;
    int zone = static_cast<int>(utm_datum_.zone);
    double x = 0.0;
    double y = 0.0;
    GeographicLib::UTMUPS::Forward(msg->latitude, msg->longitude, zone, northp,
                                   x, y);

    utm_reference_lat_ = x;
    utm_reference_lon_ = y;

    reference_initialized_ = true;

    RCLCPP_INFO(get_logger(),
                "GPS UTM reference set: latitude=%.8f, longitude=%.8f",
                utm_reference_lat_, utm_reference_lon_);
  }
}

KeepoutZoneManager::Point KeepoutZoneManager::gpsToLocalXY(
    double latitude, double longitude) const {
  bool northp = utm_datum_.northp;
  int zone = static_cast<int>(utm_datum_.zone);
  double x = 0.0;
  double y = 0.0;
  GeographicLib::UTMUPS::Forward(latitude, longitude, zone, northp, x, y);

  const double local_x = x - utm_reference_lat_;
  const double local_y = y - utm_reference_lon_;

  return {local_x, local_y};
}

KeepoutZoneManager::Polygon KeepoutZoneManager::gpsPathToPolygon(
    const GeoPath& path) const {
  Polygon polygon;
  polygon.reserve(path.poses.size());

  for (const auto& pose : path.poses) {
    polygon.push_back(gpsToLocalXY(pose.pose.position.latitude,
                                   pose.pose.position.longitude));
  }

  return polygon;
}

KeepoutZoneManager::Point KeepoutZoneManager::localToPixel(double x,
                                                           double y) const {
  return {std::floor((x - origin_x_) / resolution_),
          std::floor((y - origin_y_) / resolution_)};
}

bool KeepoutZoneManager::pointInPolygon(double x, double y,
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

bool KeepoutZoneManager::addPolygonToMask(const Polygon& polygon) {
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

  const auto [min_px_value, min_py_value] = localToPixel(min_x, min_y);
  const auto [max_px_value, max_py_value] = localToPixel(max_x, max_y);

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

      if (pointInPolygon(world_x, world_y, polygon)) {
        const auto index = static_cast<std::size_t>(pixel_y) *
                               static_cast<std::size_t>(width_) +
                           static_cast<std::size_t>(pixel_x);

        mask_data_[index] = 100;
      }
    }
  }

  return true;
}

bool KeepoutZoneManager::rebuildMask() {
  // Keep a valid, minimal grid when no polygons have been added.
  if (polygons_.empty()) {
    width_ = 1;
    height_ = 1;
    origin_x_ = 0.0;
    origin_y_ = 0.0;
    mask_data_.assign(1, 0);
    return true;
  }

  // Calculate the combined bounding box of all stored polygons.
  double min_x = polygons_.front().local.front().first;
  double max_x = min_x;
  double min_y = polygons_.front().local.front().second;
  double max_y = min_y;

  for (const auto& stored_polygon : polygons_) {
    for (const auto& [x, y] : stored_polygon.local) {
      min_x = std::min(min_x, x);
      max_x = std::max(max_x, x);
      min_y = std::min(min_y, y);
      max_y = std::max(max_y, y);
    }
  }

  // Calculate the new origin without changing the current grid.
  const double new_origin_x = std::floor(min_x / resolution_) * resolution_;
  const double new_origin_y = std::floor(min_y / resolution_) * resolution_;

  // Calculate the required grid dimensions.
  const double width_cells =
      std::ceil((max_x - new_origin_x) / resolution_) + 1.0;
  const double height_cells =
      std::ceil((max_y - new_origin_y) / resolution_) + 1.0;

  // Reject invalid or excessively large grids before allocating memory (~10MB).
  constexpr std::size_t max_nr_grid_cells = 10'000'000;

  if (!std::isfinite(width_cells) || !std::isfinite(height_cells) ||
      width_cells < 1.0 || height_cells < 1.0 ||
      width_cells > static_cast<double>(std::numeric_limits<int>::max()) ||
      height_cells > static_cast<double>(std::numeric_limits<int>::max()) ||
      width_cells * height_cells > static_cast<double>(max_nr_grid_cells)) {
    RCLCPP_ERROR(get_logger(),
                 "Keepout grid dimensions are invalid or too large "
                 "(width=%.0f, height=%.0f). Rejecting grid rebuild.",
                 width_cells, height_cells);
    return false;
  }

  const int new_width = static_cast<int>(width_cells);
  const int new_height = static_cast<int>(height_cells);

  const auto cell_count = static_cast<std::size_t>(new_width) *
                          static_cast<std::size_t>(new_height);

  // Allocate the new grid before changing the current grid.
  std::vector<int8_t> new_mask;

  try {
    new_mask.assign(cell_count, 0);
  } catch (const std::bad_alloc&) {
    RCLCPP_ERROR(get_logger(),
                 "Unable to allocate the new keepout grid. "
                 "Keeping the previously published grid.");
    return false;
  }

  // Commit the new grid only after its dimensions are valid and its memory
  // has been allocated successfully.
  const int old_width = width_;
  const int old_height = height_;
  const double old_origin_x = origin_x_;
  const double old_origin_y = origin_y_;

  width_ = new_width;
  height_ = new_height;
  origin_x_ = new_origin_x;
  origin_y_ = new_origin_y;
  mask_data_.swap(new_mask);

  // Rebuild the mask using all stored polygons.
  for (const auto& stored_polygon : polygons_) {
    if (!addPolygonToMask(stored_polygon.local)) {
      // Restore the previous grid if rasterization unexpectedly fails.
      mask_data_.swap(new_mask);
      width_ = old_width;
      height_ = old_height;
      origin_x_ = old_origin_x;
      origin_y_ = old_origin_y;

      RCLCPP_ERROR(get_logger(),
                   "Failed to rasterize a keepout polygon. "
                   "Keeping the previously published grid.");
      return false;
    }
  }

  RCLCPP_INFO(get_logger(),
              "Rebuilt keepout mask: width=%d, height=%d, "
              "resolution=%.3f m, origin=(%.3f, %.3f).",
              width_, height_, resolution_, origin_x_, origin_y_);

  return true;
}

void KeepoutZoneManager::manageZonesCallback(
    const std::shared_ptr<ManageKeepoutZones::Request> request,
    std::shared_ptr<ManageKeepoutZones::Response> response) {
  switch (request->operation) {
    case ManageKeepoutZones::Request::ADD:
      if (!reference_initialized_) {
        response->success = false;
        response->message = "No GPS reference is available.";
        return;
      }

      addZones(request, response);
      break;

    case ManageKeepoutZones::Request::REMOVE:
      removeSingleZone(request, response);
      break;

    case ManageKeepoutZones::Request::REMOVE_ALL:
      removeAllZones(response);
      break;

    default:
      response->success = false;
      response->message = "Unknown keepout zone operation.";
      break;
  }

  response->zone_ids.clear();
  response->zone_ids.reserve(polygons_.size());

  for (const auto& polygon : polygons_) {
    response->zone_ids.push_back(polygon.id);
  }
}

void KeepoutZoneManager::addZones(
    const std::shared_ptr<ManageKeepoutZones::Request> request,
    std::shared_ptr<ManageKeepoutZones::Response> response) {
  std::size_t added_count = 0;
  std::size_t skipped_count = 0;

  for (const auto& path : request->paths) {
    if (path.poses.size() < 3) {
      RCLCPP_WARN(
          get_logger(),
          "Skipping keepout polygon: at least three points are required.");
      ++skipped_count;
      continue;
    }

    // Convert GPS coordinates to local coordinates.
    const Polygon local_polygon = gpsPathToPolygon(path);

    // Reject polygons containing invalid local coordinates.
    const bool valid_coordinates = std::all_of(
        local_polygon.begin(), local_polygon.end(), [](const auto& point) {
          return std::isfinite(point.first) && std::isfinite(point.second);
        });

    if (!valid_coordinates) {
      RCLCPP_WARN(get_logger(),
                  "Skipping keepout polygon: invalid local coordinates.");
      ++skipped_count;
      continue;
    }

    // Preserve the original GPS coordinates.
    Polygon gps_polygon;
    gps_polygon.reserve(path.poses.size());

    for (const auto& pose : path.poses) {
      gps_polygon.emplace_back(pose.pose.position.latitude,
                               pose.pose.position.longitude);
    }

    polygons_.push_back({next_zone_id_, std::move(gps_polygon), local_polygon});

    // Attempt to rebuild the occupancy grid with the new zone.
    if (!rebuildMask()) {
      // rebuildMask() preserves the previous grid on failure.
      polygons_.pop_back();

      RCLCPP_WARN(
          get_logger(),
          "Skipping keepout polygon #%s: failed to rebuild occupancy grid.",
          std::to_string(next_zone_id_).c_str());

      ++skipped_count;
      continue;
    }

    RCLCPP_INFO(get_logger(), "Keepout polygon #%s created with %zu points.",
                std::to_string(next_zone_id_).c_str(), local_polygon.size());

    ++zone_count_;
    ++next_zone_id_;
    ++added_count;
  }

  // Publish once after processing all requested polygons.
  if (added_count > 0) {
    publishMask();
  }

  // Report whether the request added any zones.
  response->success = added_count > 0;

  if (added_count == 0 && skipped_count == 0) {
    response->message = "No keepout polygons were provided.";
  } else {
    response->message =
        "Added " + std::to_string(added_count) + " keepout zone(s); skipped " +
        std::to_string(skipped_count) +
        ". Total active zones: " + std::to_string(zone_count_) + ".";
  }
}

void KeepoutZoneManager::removeSingleZone(
    const std::shared_ptr<ManageKeepoutZones::Request> request,
    std::shared_ptr<ManageKeepoutZones::Response> response) {
  // Find the zone using its stable ID.
  const auto zone_it = std::find_if(polygons_.begin(), polygons_.end(),
                                    [request](const StoredPolygon& polygon) {
                                      return polygon.id == request->zone_id;
                                    });

  if (zone_it == polygons_.end()) {
    response->success = false;
    response->message = "Keepout zone #" + std::to_string(request->zone_id) +
                        " does not exist.";
    return;
  }

  // Save the zone and its position so it can be restored if rebuilding fails.
  const auto original_position =
      static_cast<std::size_t>(std::distance(polygons_.begin(), zone_it));
  StoredPolygon removed_zone = *zone_it;

  polygons_.erase(zone_it);

  // Rebuild the grid without the removed zone.
  if (!rebuildMask()) {
    // Restore the zone to its original position.
    polygons_.insert(polygons_.begin() + original_position,
                     std::move(removed_zone));

    response->success = false;
    response->message = "Failed to remove keepout zone #" +
                        std::to_string(request->zone_id) +
                        ": the occupancy grid could not be rebuilt. "
                        "The existing zones remain unchanged.";
    return;
  }

  --zone_count_;

  publishMask();

  RCLCPP_INFO(get_logger(), "Keepout zone #%lu removed successfully.",
              request->zone_id);

  response->success = true;
  response->message = "Keepout zone #" + std::to_string(request->zone_id) +
                      " removed. Total number of keepout zones active: " +
                      std::to_string(zone_count_);
}

void KeepoutZoneManager::removeAllZones(
    std::shared_ptr<ManageKeepoutZones::Response> response) {
  if (polygons_.empty()) {
    response->success = true;
    response->message = "No keepout zones are currently active.";
    return;
  }

  // Preserve the current zones in case rebuilding fails.
  auto previous_polygons = std::move(polygons_);
  const std::size_t removed_count = previous_polygons.size();

  polygons_.clear();

  // Rebuild the occupancy grid without any keepout zones.
  if (!rebuildMask()) {
    // Restore the existing zones.
    polygons_ = std::move(previous_polygons);

    response->success = false;
    response->message =
        "Failed to remove all keepout zones because the occupancy "
        "grid could not be rebuilt. Existing zones have been restored.";
    return;
  }

  zone_count_ = 0;
  publishMask();

  RCLCPP_INFO(get_logger(), "Removed all %zu keepout zone(s).", removed_count);

  response->success = true;
  response->message = "Successfully removed all " +
                      std::to_string(removed_count) + " keepout zone(s).";
}

void KeepoutZoneManager::publishMask() {
  OccupancyGrid msg;

  msg.header.stamp = get_clock()->now();
  msg.header.frame_id = "map";

  msg.info.resolution = static_cast<float>(resolution_);
  msg.info.width = static_cast<std::uint32_t>(width_);
  msg.info.height = static_cast<std::uint32_t>(height_);

  msg.info.origin.position.x = origin_x_;
  msg.info.origin.position.y = origin_y_;
  msg.info.origin.orientation.w = 1.0;

  msg.data = mask_data_;

  keepout_zone_pub_->publish(msg);
}

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<KeepoutZoneManager>());
  rclcpp::shutdown();
  return 0;
}
