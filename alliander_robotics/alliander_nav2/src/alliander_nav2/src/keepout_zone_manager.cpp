// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

#include "keepout_zone_manager.hpp"

#include <GeographicLib/UTMUPS.hpp>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <functional>
#include <new>
#include <opencv2/imgproc.hpp>
#include <string>
#include <utility>

using std::placeholders::_1;
using std::placeholders::_2;

KeepoutZoneManager::KeepoutZoneManager() : Node("keepout_zone_manager") {
  // Initialize TF buffer and listener.
  tf_buffer_ = std::make_shared<tf2_ros::Buffer>(get_clock());
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

  // Subscribe to the UTM datum.
  rclcpp::QoS qos(1);
  qos.transient_local();

  utm_sub_ = create_subscription<UTMDatum>(
      "/utm_datum", qos, std::bind(&KeepoutZoneManager::utmCallback, this, _1));

  const auto mask_qos =
      rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local();

  keepout_zone_pub_ =
      create_publisher<OccupancyGrid>("/keepout_filter_mask", mask_qos);

  manage_zones_srv_ = create_service<ManageKeepoutZones>(
      "/manage_nogozones",
      std::bind(&KeepoutZoneManager::manageZonesCallback, this, _1, _2));

  // Start with a minimal, empty grid. With each newly added zone, its
  // dimensions will grow accordingly.
  mask_data_.assign(1, 0);

  initial_mask_timer_ = create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&KeepoutZoneManager::waitForUtmTransform, this));

  RCLCPP_INFO(get_logger(),
              "Keepout Zone Manager initialized. Waiting for TF transforms.");
}

void KeepoutZoneManager::waitForUtmTransform() {
  if (initial_mask_published_) {
    initial_mask_timer_->cancel();
    return;
  }

  const bool map_transform_available =
      tf_buffer_->canTransform("utm", "map", this->now());

  if (!map_transform_available) {
    RCLCPP_INFO_THROTTLE(
        get_logger(), *get_clock(), 5000,
        "Waiting for TF transforms: utm->map not yet available");

    return;
  }

  // Both transforms are available. Publish the initial mask.
  initial_mask_published_ = true;

  publishMask();

  RCLCPP_INFO(get_logger(),
              "Required TF transforms are available. "
              "Initial keepout mask published.");

  // No need to keep checking after successful publication.
  initial_mask_timer_->cancel();
}

void KeepoutZoneManager::utmCallback(const UTMDatum::SharedPtr msg) {
  utm_datum_ = *msg;
  utm_datum_initialized_ = true;
}

KeepoutZoneManager::Point KeepoutZoneManager::gpsToUTMCoordinates(
    double latitude, double longitude) const {
  bool northp = utm_datum_.northp;
  int zone = utm_datum_.zone;
  double x;
  double y;
  GeographicLib::UTMUPS::Forward(latitude, longitude, zone, northp, x, y);

  return {x, y};
}

cv::Mat KeepoutZoneManager::geoPathToContour(const GeoPath& path) const {
  cv::Mat contour;

  for (const auto& pose : path.poses) {
    auto point = gpsToUTMCoordinates(pose.pose.position.latitude,
                                     pose.pose.position.longitude);

    if (!std::isfinite(point.first) || !std::isfinite(point.second)) {
      return {};
    }

    cv::Point cv_point(
        static_cast<int>(std::floor(point.first / resolution_)),
        static_cast<int>(std::floor(point.second / resolution_)));

    contour.push_back(cv_point);
  }

  return contour;
}

bool KeepoutZoneManager::rebuildMask() {
  if (zones_.empty()) {
    width_ = 1;
    height_ = 1;
    grid_origin_x_ = 0.0;
    grid_origin_y_ = 0.0;
    mask_data_.assign(1, 0);
    return true;
  }

  std::vector<cv::Mat> contours;

  if (!collectLocalContours(contours)) {
    return false;
  }

  std::vector<int8_t> new_mask;
  int new_width;
  int new_height;
  double new_origin_x;
  double new_origin_y;

  if (!createMask(contours, new_mask, new_width, new_height, new_origin_x,
                  new_origin_y)) {
    return false;
  }

  // Commit the new grid.
  width_ = new_width;
  height_ = new_height;
  grid_origin_x_ = new_origin_x;
  grid_origin_y_ = new_origin_y;
  mask_data_.swap(new_mask);

  RCLCPP_INFO(get_logger(),
              "Rebuilt keepout mask: width=%d, height=%d, "
              "resolution=%.3f m, origin=(%.3f, %.3f).",
              width_, height_, resolution_, grid_origin_x_, grid_origin_y_);

  return true;
}

bool KeepoutZoneManager::collectLocalContours(std::vector<cv::Mat>& contours) const {
  contours.reserve(zones_.size());

  for (const auto& zone : zones_) {
    if (zone.local.empty() || zone.local.rows < 3 ||
        zone.local.type() != CV_32SC2) {
      RCLCPP_ERROR(get_logger(), "Cannot rebuild mask: invalid zone contour.");
      return false;
    }

    contours.push_back(zone.local.clone());
  }

  return true;
}

bool KeepoutZoneManager::createMask(std::vector<cv::Mat>& contours,
                                    std::vector<int8_t>& new_mask,
                                    int& new_width, int& new_height,
                                    double& new_origin_x,
                                    double& new_origin_y) const {
  // Calculate the combined bounding box of all contours.
  cv::Mat combined_contour;
  cv::vconcat(contours, combined_contour);
  const cv::Rect bounding_box = cv::boundingRect(combined_contour);

  // Calculate the required grid dimensions.
  constexpr std::size_t max_nr_grid_cells = 10'000'000;

  if (bounding_box.width < 1 || bounding_box.height < 1) {
    RCLCPP_ERROR(get_logger(), "Keepout grid dimensions are invalid.");
    return false;
  }

  const std::size_t cell_count =
      static_cast<std::size_t>(bounding_box.width) * bounding_box.height;

  if (cell_count > max_nr_grid_cells) {
    RCLCPP_ERROR(get_logger(), "Keepout grid dimensions are too large.");
    return false;
  }

  // Calculate the grid origin in metres.
  new_origin_x = bounding_box.x * resolution_;
  new_origin_y = bounding_box.y * resolution_;

  // Allocate the new grid.
  try {
    new_mask.assign(cell_count, 0);
  } catch (const std::bad_alloc&) {
    RCLCPP_ERROR(get_logger(), "Unable to allocate the new keepout grid.");
    return false;
  }

  cv::Mat mask(bounding_box.height, bounding_box.width, CV_8SC1,
               new_mask.data());

  // Shift all contours relative to the new grid origin.
  for (auto& contour : contours) {
    contour -= cv::Scalar(bounding_box.x, bounding_box.y);
  }

  // Fill the mask with all keepout contours.
  cv::fillPoly(mask, contours, cv::Scalar(100));

  new_width = bounding_box.width;
  new_height = bounding_box.height;

  return true;
}

void KeepoutZoneManager::manageZonesCallback(
    const std::shared_ptr<ManageKeepoutZones::Request> request,
    std::shared_ptr<ManageKeepoutZones::Response> response) {
  switch (request->operation) {
    case ManageKeepoutZones::Request::ADD:
      if (!utm_datum_initialized_) {
        response->success = false;
        response->message = "No UTM datum is available.";
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
  response->zone_ids.reserve(zones_.size());

  for (const auto& zone : zones_) {
    response->zone_ids.push_back(zone.id);
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
          "Skipping zone: invalid path, at least three points are required.");
      ++skipped_count;
      continue;
    }

    // Convert GPS coordinates to local coordinates.
    const cv::Mat local_zone = geoPathToContour(path);

    // Reject zones containing invalid local coordinates.
    if (local_zone.empty()) {
      RCLCPP_WARN(get_logger(), "Skipping zone: invalid local coordinates.");
      ++skipped_count;
      continue;
    }

    // Preserve the original GPS coordinates.
    cv::Mat gps_zone;
    for (const auto& pose : path.poses) {
      gps_zone.push_back(cv::Point2d(pose.pose.position.latitude,
                                     pose.pose.position.longitude));
    }

    zones_.push_back({next_zone_id_, std::move(gps_zone), local_zone});

    // Attempt to rebuild the occupancy grid with the new zone.
    if (!rebuildMask()) {
      // rebuildMask() preserves the previous grid on failure.
      zones_.pop_back();

      RCLCPP_WARN(
          get_logger(),
          "Skipping keepout zone #%s: failed to rebuild occupancy grid.",
          std::to_string(next_zone_id_).c_str());

      ++skipped_count;
      continue;
    }

    RCLCPP_INFO(get_logger(), "Keepout zone #%s created with %d points.",
                std::to_string(next_zone_id_).c_str(), local_zone.rows);

    ++next_zone_id_;
    ++added_count;
  }

  // Publish once after processing all requested zones.
  if (added_count > 0) {
    publishMask();
  }

  response->success = added_count > 0;

  if (added_count == 0 && skipped_count == 0) {
    response->message = "No keepout zones were provided.";
  } else {
    response->message =
        "Added " + std::to_string(added_count) + " keepout zone(s); skipped " +
        std::to_string(skipped_count) +
        ". Total active zones: " + std::to_string(zones_.size()) + ".";
  }
}

void KeepoutZoneManager::removeSingleZone(
    const std::shared_ptr<ManageKeepoutZones::Request> request,
    std::shared_ptr<ManageKeepoutZones::Response> response) {
  // Find the zone using its stable ID.
  const auto zone_it = std::find_if(zones_.begin(), zones_.end(),
                                    [request](const StoredZones& zone) {
                                      return zone.id == request->zone_id;
                                    });

  if (zone_it == zones_.end()) {
    response->success = false;
    response->message = "Keepout zone #" + std::to_string(request->zone_id) +
                        " does not exist.";
    return;
  }

  // Save the zone and its position so it can be restored if rebuilding fails.
  const auto original_position = std::distance(zones_.begin(), zone_it);
  StoredZones removed_zone = *zone_it;

  zones_.erase(zone_it);

  // Rebuild the grid without the removed zone.
  if (!rebuildMask()) {
    // Restore the zone to its original position.
    zones_.insert(zones_.begin() + original_position, std::move(removed_zone));

    response->success = false;
    response->message = "Failed to remove keepout zone #" +
                        std::to_string(request->zone_id) +
                        ": the occupancy grid could not be rebuilt. "
                        "The existing zones remain unchanged.";
    return;
  }

  publishMask();

  RCLCPP_INFO(get_logger(), "Keepout zone #%lu removed successfully.",
              request->zone_id);

  response->success = true;
  response->message = "Keepout zone #" + std::to_string(request->zone_id) +
                      " removed. Total number of keepout zones active: " +
                      std::to_string(zones_.size());
}

void KeepoutZoneManager::removeAllZones(
    std::shared_ptr<ManageKeepoutZones::Response> response) {
  if (zones_.empty()) {
    response->success = true;
    response->message = "No keepout zones are currently active.";
    return;
  }

  // Preserve the current zones in case rebuilding fails.
  auto previous_zones = std::move(zones_);
  const std::size_t removed_count = previous_zones.size();

  zones_.clear();

  // Rebuild the occupancy grid without any keepout zones.
  if (!rebuildMask()) {
    // Restore the existing zones.
    zones_ = std::move(previous_zones);

    response->success = false;
    response->message =
        "Failed to remove all keepout zones because the occupancy "
        "grid could not be rebuilt. Existing zones have been restored.";
    return;
  }

  publishMask();

  RCLCPP_INFO(get_logger(), "Removed all %zu keepout zone(s).", removed_count);

  response->success = true;
  response->message = "Successfully removed all " +
                      std::to_string(removed_count) + " keepout zone(s).";
}

void KeepoutZoneManager::publishMask() {
  if (!initial_mask_published_) {
    RCLCPP_DEBUG(get_logger(),
                 "Skipping keepout mask publication until TF is ready.");
    return;
  }

  OccupancyGrid msg;

  msg.header.stamp = get_clock()->now();
  msg.header.frame_id = "utm";

  msg.info.resolution = static_cast<float>(resolution_);
  msg.info.width = static_cast<std::uint32_t>(width_);
  msg.info.height = static_cast<std::uint32_t>(height_);

  msg.info.origin.position.x = grid_origin_x_;
  msg.info.origin.position.y = grid_origin_y_;
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
