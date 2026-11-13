// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#include "alliander_behavior/behavior_executor.hpp"

namespace alliander_behavior {

const uint16_t HALT_SLEEP_PERIOD_MS = 50;

/**
 * @brief returns a monotonically increasing amount of ticks since epoch.
 * @return ticks since epoch.
 */
std::chrono::steady_clock::rep steadyNow() {
  return std::chrono::steady_clock::now().time_since_epoch().count();
}

BehaviorExecutor::BehaviorExecutor(const rclcpp::Node::SharedPtr& node)
    : BT::TreeExecutionServer(node) {
  node->declare_parameter<std::string>("tree_name", "");

  initializeBlackboard();
  executeRegistration();

  const auto tree_name = node->get_parameter("tree_name").as_string();
  if (!tree_name.empty()) {
    scheduleAutostart(tree_name, std::chrono::seconds(10));
  }
}

void BehaviorExecutor::initializeBlackboard() {
  const std::string prefix = "blackboard.";
  auto blackboard = globalBlackboard();

  // find param overrides
  const auto& overrides =
      node()->get_node_parameters_interface()->get_parameter_overrides();

  for (const auto& [name, value] : overrides) {
    if (name.rfind(prefix, 0) != 0) continue;
    if (!node()->has_parameter(name)) {
      node()->declare_parameter(name, value);
    }

    // convert params to strings, as this will resolve conflicts.
    // e.g. dock_retry_delay_ms: 5000 will get a int64_t type, but in the XML's
    // BT.CPP Sleep behavior, it is interpreted as unsigned int. To combat this,
    // just cast everything to strings.
    const auto key = name.substr(prefix.size());
    switch (value.get_type()) {
      case rclcpp::ParameterType::PARAMETER_BOOL:
        blackboard->set(key, value.get<bool>() ? "true" : "false");
        continue;
      case rclcpp::ParameterType::PARAMETER_DOUBLE:
        blackboard->set(key, std::to_string(value.get<double>()));
        continue;
      case rclcpp::ParameterType::PARAMETER_INTEGER:
        blackboard->set(key, std::to_string(value.get<int64_t>()));
        continue;
      case rclcpp::ParameterType::PARAMETER_STRING:
        blackboard->set(key, value.get<std::string>());
        continue;
      default:
        RCLCPP_ERROR(node()->get_logger(),
                     "Error converting param %s: type %s is not implemented.",
                     key.c_str(), rclcpp::to_string(value.get_type()).c_str());
        continue;
    }
  }
}

/// Calls a BehaviorTree.ROS2 ExecuteTree action
void BehaviorExecutor::scheduleAutostart(
    const std::string& tree_name, std::chrono::seconds discovery_timeout) {
  const auto action_name = node()->get_parameter("action_name").as_string();
  autostart_client_ =
      rclcpp_action::create_client<ExecuteTree>(node(), action_name);

  const auto discovery_timeout_ticks =
      std::chrono::duration_cast<std::chrono::steady_clock::duration>(
          discovery_timeout)
          .count();
  const auto deadline = steadyNow() + discovery_timeout_ticks;

  // retried on a timer, because the client needs to discover our own server
  autostart_timer_ = node()->create_wall_timer(
      std::chrono::milliseconds(250), [this, tree_name, deadline]() {
        // don't start a new tree if a halt is requested
        if (halt_requested_) {
          autostart_timer_->cancel();
          return;
        }

        // stop execution if deadline has passed
        if (!autostart_client_->action_server_is_ready()) {
          if (steadyNow() >= deadline) {
            RCLCPP_ERROR(node()->get_logger(),
                         "Could not autostart tree %s: ExecuteTree action "
                         "server was not available before timeout",
                         tree_name.c_str());
            autostart_timer_->cancel();
          }
          return;
        }
        autostart_timer_->cancel();

        // start tree
        ExecuteTree::Goal goal;
        goal.target_tree = tree_name;

        rclcpp_action::Client<ExecuteTree>::SendGoalOptions options;
        options.goal_response_callback =
            [this,
             tree_name](rclcpp_action::ClientGoalHandle<ExecuteTree>::SharedPtr
                            handle) {
              if (!handle) {
                RCLCPP_ERROR(node()->get_logger(),
                             "Autostart of tree '%s' was rejected",
                             tree_name.c_str());
              }
            };
        RCLCPP_INFO(node()->get_logger(), "Autostarting tree '%s'",
                    tree_name.c_str());
        autostart_client_->async_send_goal(goal, options);
      });
}

/// Executes a given BTree with tree_name
bool BehaviorExecutor::onGoalReceived(const std::string& tree_name,
                                      const std::string&) {
  if (halt_requested_) {
    RCLCPP_WARN(node()->get_logger(),
                "Rejecting tree '%s': executor is shutting down",
                tree_name.c_str());
    return false;
  }
  if (tree_active_) {
    RCLCPP_WARN(node()->get_logger(),
                "Rejecting tree '%s': tree '%s' is still running. Cancel it "
                "first.",
                tree_name.c_str(), treeName().c_str());
    return false;
  }
  return true;
}

/// Sets flags and initializes logger
void BehaviorExecutor::onTreeCreated(BT::Tree& tree) {
  last_tick_ = steadyNow();
  tree_active_ = true;
  status_logger_ =
      std::make_unique<RosStatusLogger>(tree, node()->get_logger());
}

/// Invoked each loop after tree.tickOnce().
/// Used to update tick time and handle halt
std::optional<BT::NodeStatus> BehaviorExecutor::onLoopAfterTick(
    BT::NodeStatus) {
  last_tick_ = steadyNow();
  if (halt_requested_) {
    // makes the base class halt the tree and abort the goal
    return BT::NodeStatus::FAILURE;
  }
  return std::nullopt;
}

/// Callback if entire tree completes. Used to inform user
std::optional<std::string> BehaviorExecutor::onTreeExecutionCompleted(
    BT::NodeStatus status, bool was_cancelled) {
  status_logger_.reset();
  tree_active_ = false;

  if (halt_requested_) {
    return "Tree halted: executor is shutting down";
  }
  if (!was_cancelled) {
    RCLCPP_WARN(node()->get_logger(),
                "Tree '%s' completed on its own with status %s; waiting for "
                "a new ExecuteTree goal",
                treeName().c_str(), BT::toStr(status, false).c_str());
  }
  return std::nullopt;
}

/// Graceful shutdown of running tree
bool BehaviorExecutor::haltAndWait(std::chrono::milliseconds timeout) {
  halt_requested_ = true;
  const auto deadline = std::chrono::steady_clock::now() + timeout;
  while (tree_active_) {
    if (std::chrono::steady_clock::now() > deadline) return false;
    // cede execution to other parts of software
    std::this_thread::sleep_for(
        std::chrono::milliseconds(HALT_SLEEP_PERIOD_MS));
  }
  return true;
}

}  // namespace alliander_behavior
