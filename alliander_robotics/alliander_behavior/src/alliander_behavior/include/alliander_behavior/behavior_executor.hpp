// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <alliander_behavior/status_logger.hpp>
#include <atomic>
#include <behaviortree_ros2/tree_execution_server.hpp>
#include <chrono>
#include <memory>
#include <mutex>
#include <optional>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <string>

namespace alliander_behavior {

/// Generic, re-usable BT executor class that inherits from BehaviorTree.ROS2's
/// TreeExecutionServer.
class BehaviorExecutor : public BT::TreeExecutionServer {
 public:
  /**
   * @brief initializes the BehaviorExecutor.
   * @param node shared pointer to ROS2 node instance.
   */
  explicit BehaviorExecutor(const rclcpp::Node::SharedPtr& node);

  /**
   * @brief halts the running tree, stops if timeout is reached.
   * @param timeout amount of milliseconds to wait before forcing a stop.
   * @return whether the tree was halted before the deadline.
   */
  bool haltAndWait(std::chrono::milliseconds timeout);

 protected:
  /**
   * @brief callback for when a tree is received to execute. Returning false
   * will reject the goal.
   * @param tree_name string containing tree name (TreeID, not file name).
   * @return whether the goal is accepted or rejected.
   */
  bool onGoalReceived(const std::string& tree_name,
                      const std::string&) override;
  /**
   * @brief callback for when the tree is created. Used to initialize values.
   * @param tree the tree that was created.
   */
  void onTreeCreated(BT::Tree& tree) override;
  /**
   * @brief run each loop after tree.tickOnce(). Return a valid NodeStatus to
   * stop the tree.
   * @return optional failure if the tree is halted.
   */
  std::optional<BT::NodeStatus> onLoopAfterTick(BT::NodeStatus) override;
  /**
   * @brief callback after tree execution is completed, to handle shutdown.
   * @param status status of tree after last tick.
   * @param was_cancelled true is action was cancelled by Action Client.
   * @return optional status message indicating tree is halted.
   */
  std::optional<std::string> onTreeExecutionCompleted(
      BT::NodeStatus status, bool was_cancelled) override;

 private:
  /**
   * @brief initializes a global blackboard, including ROS param overrides.
   * Uses strings to seed blackboard, as those are handled better.
   */
  void initializeBlackboard();
  /**
   * @brief autostarts a given tree. An action client is created, which connects
   * to an internal action server. This is in line with ExecuteTree's functions.
   * @param tree_name the BTree (TreeID) to start.
   * @param discovery_timeout time in seconds to wait for server to come online.
   */
  void scheduleAutostart(const std::string& tree_name,
                         std::chrono::seconds discovery_timeout);

  /// Allows logging BT state transitions in ROS.
  std::unique_ptr<RosStatusLogger> status_logger_;

  /// Boolean indicating whether a tree is currently running.
  std::atomic<bool> tree_active_{false};
  /// Boolean indicating whether the user or another process requested a halt.
  std::atomic<bool> halt_requested_{false};
  /// Monotonically increasing time representation of when the tree was ticked
  /// last.
  std::atomic<std::chrono::steady_clock::rep> last_tick_{0};

  /// Action Client for loading a BTree.
  rclcpp_action::Client<ExecuteTree>::SharedPtr autostart_client_;
  /// Timer for loading a BTree.
  rclcpp::TimerBase::SharedPtr autostart_timer_;
};

}  // namespace alliander_behavior
