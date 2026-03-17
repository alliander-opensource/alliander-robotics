// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef BASE_DIAGNOSTICS_HPP_
#define BASE_DIAGNOSTICS_HPP_

#include <diagnostic_msgs/msg/diagnostic_status.hpp>
#include <mutex>
#include <rclcpp/rclcpp.hpp>

/**
 * @brief Base class for diagnostic modules.
 *
 * This class provides a common interface for evaluating and reporting
 * diagnostic status of a component. Derived classes implement the
 * evaluate() function to update the diagnostic status based on
 * monitored data.
 */
class BaseDiagnostics {
 public:
  /**
   * @brief Construct a BaseDiagnostics instance.
   * @param name Name of the diagnostic component.
   * @param hardware_id Identifier of the associated hardware.
   */
  BaseDiagnostics(const std::string& name, const std::string& hardware_id) {
    status_.name = name;
    status_.hardware_id = hardware_id;
  }

  virtual ~BaseDiagnostics() = default;

  /**
   * @brief Evaluate the monitored data and update the diagnostic status.
   * @param now current time.
   */
  virtual void evaluate(rclcpp::Time now) = 0;

  /**
   * @brief Get the current diagnostic status.
   * @return Copy of the diagnostic status message.
   */
  diagnostic_msgs::msg::DiagnosticStatus get_status() {
    std::lock_guard<std::mutex> lock(mutex_);
    return status_;
  }

 protected:
  /// Current diagnostic status message.
  diagnostic_msgs::msg::DiagnosticStatus status_;

  /// Mutex protecting access to the status message.
  std::mutex mutex_;

  /// Escalation timeout until status level should become a warning
  rclcpp::Duration warning_timeout_ = std::chrono::seconds(3);

  /// Escalation timeout until status level should become an error
  rclcpp::Duration error_timeout_ = std::chrono::seconds(5);

  /// Escalation timeout until status level should become stale
  rclcpp::Duration stale_timeout_ = std::chrono::seconds(10);
};

#endif  // BASE_DIAGNOSTICS_HPP_
