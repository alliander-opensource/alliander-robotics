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

TEST_F(PackageTesterFixture, TestTransformPoseTranslation) {
  geometry_msgs::msg::PoseStamped pose_in;
  pose_in.pose.position.y = 1;
  pose_in.pose.position.z = 2;

  geometry_msgs::msg::Transform tf;
  tf.translation.x = 5;
  tf.translation.y = 5;
  tf.translation.z = 5;

  auto req = std::make_shared<rcdt_messages::srv::TransformPose::Request>();
  req->pose = pose_in;
  req->transform = tf;

  auto future_and_id = tester_node_->sendTransformPoseRequest(req);
  auto result_code = executor_->spin_until_future_complete(
      future_and_id.future, std::chrono::milliseconds(500));

  ASSERT_EQ(result_code, rclcpp::FutureReturnCode::SUCCESS);
  auto response = future_and_id.future.get();
  ASSERT_NE(response, nullptr);

  ASSERT_EQ(response->pose.pose.position.x, 5);
  ASSERT_EQ(response->pose.pose.position.y, 6);
  ASSERT_EQ(response->pose.pose.position.z, 7);
}

TEST_F(PackageTesterFixture, TestTransformPoseRotation) {
  geometry_msgs::msg::PoseStamped pose_in;
  pose_in.pose.position.x = 5;

  // apply rotation of +PI/2 around Z-axis, which shifts pose to Y-axis
  geometry_msgs::msg::Transform tf;
  tf.rotation.w = 0.7071068;
  tf.rotation.z = 0.7071068;

  auto req = std::make_shared<rcdt_messages::srv::TransformPose::Request>();
  req->pose = pose_in;
  req->transform = tf;

  auto future_and_id = tester_node_->sendTransformPoseRequest(req);
  auto result_code = executor_->spin_until_future_complete(
      future_and_id.future, std::chrono::milliseconds(500));

  ASSERT_EQ(result_code, rclcpp::FutureReturnCode::SUCCESS);
  auto response = future_and_id.future.get();
  ASSERT_NE(response, nullptr);

  ASSERT_EQ(response->pose.pose.position.x, 0);
  ASSERT_NEAR(response->pose.pose.position.y, 5, 1e-4);
}

// MAIN
int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);

  int _argc = 0;
  const char** _argv = nullptr;

  rclcpp::init(_argc, _argv);

  return RUN_ALL_TESTS();
}
