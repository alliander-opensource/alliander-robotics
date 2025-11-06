// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "tests/test_package.hpp"

#include <chrono>

/**
 * @brief Test fixture class for the PackageTester Node.
 * * This fixture ensures a clean setup and teardown for each test,
 * making sure the PackageTester has access to all the right data.
 */
class PackageTesterFixture : public testing::Test {
 public:
  /**
   * @brief Sets up the test suite.
   */
  static void SetUpTestSuite() {
    if (!rclcpp::ok()) {
      rclcpp::init(0, nullptr);
    }

    executor_ = std::make_shared<rclcpp::executors::MultiThreadedExecutor>();
  }

  /**
   * @brief Tears down the test suite.
   */
  static void TearDownTestSuite() {
    executor_.reset();
    rclcpp::shutdown();
  }

 protected:
  /**
   * @brief Sets up each test.
   */
  void SetUp() override {
    joy_topic_manager_node_ = std::make_shared<JoyTopicManager>();
    tester_node_ = std::make_shared<PackageTester>();

    executor_->add_node(joy_topic_manager_node_);
    executor_->add_node(tester_node_);
  }

  /**
   * @brief Tears down each test.
   */
  void TearDown() override {
    executor_->remove_node(joy_topic_manager_node_);
    executor_->remove_node(tester_node_);

    joy_topic_manager_node_.reset();
    tester_node_.reset();
  }

  /// JoyTopicManager class to run tests on.
  std::shared_ptr<JoyTopicManager> joy_topic_manager_node_;
  /// PackageTester class that provides mock data.
  std::shared_ptr<PackageTester> tester_node_;
  /// Executor to spin both nodes.
  static std::shared_ptr<rclcpp::executors::MultiThreadedExecutor> executor_;
};

std::shared_ptr<rclcpp::executors::MultiThreadedExecutor>
    PackageTesterFixture::executor_ = nullptr;

// TESTS
TEST_F(PackageTesterFixture, TestNodeInitialization) {
  ASSERT_EQ(std::string(tester_node_->get_name()), "joy_topic_manager_tester");
}

TEST_F(PackageTesterFixture, TestSwitchToArm) {
  sensor_msgs::msg::Joy msg;
  msg.buttons = {1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  tester_node_->publish_joy_message(msg);

  executor_->spin_some(std::chrono::milliseconds(200));

  std::map<int, Button> joy_state =
      joy_topic_manager_node_->get_button_states();

  for (auto& [index, button] : joy_state) {
    ASSERT_EQ(button.state, msg.buttons[index]);
  }
}

TEST_F(PackageTesterFixture, TestSwitchToBase) {
  sensor_msgs::msg::Joy msg;
  msg.buttons = {0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  tester_node_->publish_joy_message(msg);

  executor_->spin_some(std::chrono::milliseconds(200));

  std::map<int, Button> joy_state =
      joy_topic_manager_node_->get_button_states();

  for (auto& [index, button] : joy_state) {
    ASSERT_EQ(button.state, msg.buttons[index]);
  }
}

// MAIN
int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);

  int _argc = 0;
  const char** _argv = nullptr;

  rclcpp::init(_argc, _argv);

  return RUN_ALL_TESTS();
}
