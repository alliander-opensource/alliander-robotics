// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "tests/test_package.hpp"
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/static_transform_broadcaster.h>

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

    tf_broadcaster_ = std::make_shared<tf2_ros::StaticTransformBroadcaster>(tester_node_);
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
  std::shared_ptr<tf2_ros::StaticTransformBroadcaster> tf_broadcaster_;
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

TEST_F(PackageTesterFixture, TestTransformPoseToFrameTranslation) {
  // Create input pose in source frame
  geometry_msgs::msg::PoseStamped pose_in;
  pose_in.header.frame_id = "source_frame";
  pose_in.pose.position.x = 1.0;
  pose_in.pose.position.y = 2.0;
  pose_in.pose.position.z = 3.0;

  // Publish a transform: target_frame <- source_frame
  geometry_msgs::msg::TransformStamped tf;
  tf.header.frame_id = "target_frame";
  tf.child_frame_id = "source_frame";
  tf.transform.translation.x = 5.0;
  tf.transform.translation.y = 6.0;
  tf.transform.translation.z = 7.0;
  tf.transform.rotation.w = 1.0;

  tf_broadcaster_->sendTransform(tf);

  // Build request
  auto req = std::make_shared<rcdt_interfaces::srv::TransformPoseToFrame::Request>();
  req->pose = pose_in;
  req->target_frame = "target_frame";

  // Send request
  auto future_and_id = tester_node_->sendTransformPoseToFrameRequest(req);

  auto result_code = executor_->spin_until_future_complete(
      future_and_id.future, std::chrono::milliseconds(500));

  // Validate response
  ASSERT_EQ(result_code, rclcpp::FutureReturnCode::SUCCESS);
  auto response = future_and_id.future.get();
  ASSERT_NE(response, nullptr);

  EXPECT_TRUE(response->success);

  EXPECT_DOUBLE_EQ(response->pose.pose.position.x, 6.0);
  EXPECT_DOUBLE_EQ(response->pose.pose.position.y, 8.0);
  EXPECT_DOUBLE_EQ(response->pose.pose.position.z, 10.0);

  EXPECT_EQ(response->pose.header.frame_id, "target_frame");
}

TEST_F(PackageTesterFixture, TestTransformPoseToFrameRotation) {
  // Create input pose in source frame
  geometry_msgs::msg::PoseStamped pose_in;
  pose_in.header.frame_id = "source_frame";
  pose_in.pose.position.x = 5.0;

  // apply rotation of +PI/2 around Z-axis, which shifts pose to Y-axis
  geometry_msgs::msg::TransformStamped tf;
  tf.header.frame_id = "target_frame";
  tf.child_frame_id = "source_frame";
  tf.transform.rotation.w = 0.7071068;
  tf.transform.rotation.z = 0.7071068;

  tf_broadcaster_->sendTransform(tf);

  // Build request
  auto req = std::make_shared<rcdt_interfaces::srv::TransformPoseToFrame::Request>();
  req->pose = pose_in;
  req->target_frame = "target_frame";

  // Send request
  auto future_and_id = tester_node_->sendTransformPoseToFrameRequest(req);

  auto result_code = executor_->spin_until_future_complete(
      future_and_id.future, std::chrono::milliseconds(500));

  // Validate response
  ASSERT_EQ(result_code, rclcpp::FutureReturnCode::SUCCESS);
  auto response = future_and_id.future.get();
  ASSERT_NE(response, nullptr);

  EXPECT_TRUE(response->success);

  ASSERT_NEAR(response->pose.pose.position.x, 0, 1e-4);
  ASSERT_NEAR(response->pose.pose.position.y, 5, 1e-4);

  EXPECT_EQ(response->pose.header.frame_id, "target_frame");
}

// MAIN
int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);

  int _argc = 0;
  const char** _argv = nullptr;

  rclcpp::init(_argc, _argv);

  return RUN_ALL_TESTS();
}
