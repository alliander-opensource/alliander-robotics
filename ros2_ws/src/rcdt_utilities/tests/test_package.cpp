// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "tests/test_package.hpp"

#define PI 3.14159265

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
    pose_manipulator_node_ = std::make_shared<PoseManipulator>();
    tester_node_ = std::make_shared<PackageTester>();

    executor_->add_node(pose_manipulator_node_);
    executor_->add_node(tester_node_);
  }

  /**
   * @brief Tears down each test.
   */
  void TearDown() override {
    executor_->remove_node(pose_manipulator_node_);
    executor_->remove_node(tester_node_);

    pose_manipulator_node_.reset();
    tester_node_.reset();
  }

  std::shared_ptr<PoseManipulator>
      pose_manipulator_node_;                  /**< Node to manipulate poses */
  std::shared_ptr<PackageTester> tester_node_; /**< Node to test the package */
  static std::shared_ptr<rclcpp::executors::MultiThreadedExecutor>
      executor_; /**< Executor to spin nodes */
};

std::shared_ptr<rclcpp::executors::MultiThreadedExecutor>
    PackageTesterFixture::executor_ = nullptr;

// TESTS
TEST_F(PackageTesterFixture, TestNodeInitialization) {
  ASSERT_EQ(std::string(tester_node_->get_name()), "manipulate_pose_tester");
}

TEST_F(PackageTesterFixture, TestServiceInitialization) {
  ASSERT_TRUE(tester_node_->waitForServices(std::chrono::seconds(1)));
}

// MAIN
int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);

  int _argc = 0;
  const char** _argv = nullptr;

  rclcpp::init(_argc, _argv);

  return RUN_ALL_TESTS();
}
