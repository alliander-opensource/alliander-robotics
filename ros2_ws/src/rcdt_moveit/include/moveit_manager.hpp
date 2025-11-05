// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <moveit_visual_tools/moveit_visual_tools.h>
#include <tf2_ros/transform_broadcaster.h>

#include <boost/process.hpp>
#include <boost/process/group.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.hpp>
#include <moveit/robot_model/joint_model_group.hpp>
#include <moveit/robot_state/robot_state.hpp>
#include <moveit_msgs/srv/servo_command_type.hpp>
#include <rcdt_messages/srv/add_marker.hpp>
#include <rcdt_messages/srv/add_object.hpp>
#include <rcdt_messages/srv/define_goal_pose.hpp>
#include <rcdt_messages/srv/express_pose_in_other_frame.hpp>
#include <rcdt_messages/srv/move_hand_to_pose.hpp>
#include <rcdt_messages/srv/move_to_configuration.hpp>
#include <rcdt_messages/srv/pose_stamped_srv.hpp>
#include <rcdt_messages/srv/transform_goal_pose.hpp>
#include <rclcpp/executors/multi_threaded_executor.hpp>
#include <rclcpp/logging.hpp>
#include <rclcpp/node.hpp>
#include <rclcpp/node_options.hpp>
#include <rclcpp/parameter_value.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rviz_visual_tools/rviz_visual_tools.hpp>
#include <std_srvs/srv/set_bool.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <string>
#include <vector>

#include "geometry_msgs/msg/transform_stamped.hpp"

using std::placeholders::_1;
using std::placeholders::_2;

typedef rcdt_messages::srv::AddObject AddObject;
typedef rcdt_messages::srv::AddMarker AddMarker;
typedef rcdt_messages::srv::DefineGoalPose DefineGoalPose;
typedef rcdt_messages::srv::ExpressPoseInOtherFrame ExpressPoseInOtherFrame;
typedef rcdt_messages::srv::TransformGoalPose TransformGoalPose;
typedef rcdt_messages::srv::MoveToConfiguration MoveToConf;
typedef rcdt_messages::srv::MoveHandToPose MoveHandToPose;
typedef rcdt_messages::srv::PoseStampedSrv PoseStampedSrv;
typedef moveit_msgs::srv::ServoCommandType ServoCommandType;
typedef std_srvs::srv::Trigger Trigger;
typedef std_srvs::srv::SetBool SetBool;
typedef geometry_msgs::msg::PoseStamped PoseStamped;
typedef geometry_msgs::msg::TransformStamped TransformStamped;

/// Class to interact with the Moveit framework.
class MoveitManager {
 public:
  /**
   * @brief constructor for the MoveitManager class.
   * @param node The ROS2 node to attach to.
   */
  MoveitManager(rclcpp::Node::SharedPtr node);

 private:
  /// The main node
  rclcpp::Node::SharedPtr node;
  /// A separate node used to spin clients
  rclcpp::Node::SharedPtr client_node;
  /// Transform broadcaster
  tf2_ros::TransformBroadcaster tf_broadcaster;
  /// MoveGroup interface for motion planning and execution
  moveit::planning_interface::MoveGroupInterface move_group;
  /// Interface to control the planning scene
  moveit::planning_interface::PlanningSceneInterface planning_scene_interface;
  /// Joint model group for the arm
  const moveit::core::JointModelGroup* jmg_arm;
  /// Joint model group for the hand
  const moveit::core::JointModelGroup* jmg_hand;
  /// Joint model group for the TCP (tool center point)
  const moveit::core::JointModelGroup* jmg_tcp;
  /// Namespace of the arm
  std::string namespace_arm;
  /// Namespace of the camera
  std::string namespace_camera;
  /// The base frame of the robot
  std::string base_frame = "map";
  /// The marker topic for RViz visualization
  std::string marker_topic = "/rviz_markers";
  /// The current motion plan
  moveit::planning_interface::MoveGroupInterface::Plan plan;
  /// Tools for RViz visualization
  rviz_visual_tools::RvizVisualTools rviz_visual_tools;
  /// Tools for MoveIt visualization (in  RViz)
  moveit_visual_tools::MoveItVisualTools moveit_visual_tools;
  /// The goal pose for the end effector
  PoseStamped goal_pose;
  /// The arm-end pose in the TCP frame, used to publish EE markers.
  PoseStamped arm_end_in_tcp_frame;
  /// A handle to run a subprocess
  boost::process::child process;
  /// A group to manage multiple subprocesses
  boost::process::group process_group;
  /// A map to store basic shape types for MoveIt
  std::map<std::string, int> shapes = {
      {"BOX", 1}, {"SPHERE", 2}, {"CYLINDER", 3}, {"CONE", 4}};
  /// Motion planning types (point-to-point, linear, circular)
  std::set<std::string> pilz_types = {"PTP", "LIN", "CIRC"};

  /// Client to transform a Pose in another coordinate frame
  rclcpp::Client<ExpressPoseInOtherFrame>::SharedPtr
      express_pose_in_other_frame_client;

  /// Service to add collision object
  rclcpp::Service<AddObject>::SharedPtr add_object_service;
  /// Service to remove all collision objects
  rclcpp::Service<Trigger>::SharedPtr clear_objects_service;
  /// Service to toggle octomap scan
  rclcpp::Service<SetBool>::SharedPtr toggle_octomap_scan_service;
  /// Service to offset the goal_pose by a specified translation
  rclcpp::Service<TransformGoalPose>::SharedPtr transform_goal_pose_service;
  /// Service to define the goal_pose
  rclcpp::Service<DefineGoalPose>::SharedPtr define_goal_pose_service;
  /// Service to move to a specified configuration
  rclcpp::Service<MoveToConf>::SharedPtr move_to_configuration_service;
  /// Service to move hand to a specified goal Pose
  rclcpp::Service<MoveHandToPose>::SharedPtr move_hand_to_pose_service;
  /// Service to add a visual marker at a specified Pose
  rclcpp::Service<AddMarker>::SharedPtr add_marker_service;
  /// Service to clear visual markers
  rclcpp::Service<Trigger>::SharedPtr clear_markers_service;
  /// Service to visualize a specified grasp Pose
  rclcpp::Service<PoseStampedSrv>::SharedPtr visualize_grasp_pose_service;
  /// Service to create a motion plan
  rclcpp::Service<PoseStampedSrv>::SharedPtr create_plan_service;
  /// Service to visualize the current motion plan
  rclcpp::Service<Trigger>::SharedPtr visualize_plan_service;
  /// Service to execute the current motion plan
  rclcpp::Service<Trigger>::SharedPtr execute_plan_service;

  /**
   * @brief Callback to add a collision object.
   * @param request The AddObject request indicating object pose and shape.
   * @param response Response indicating whether the service call succeeded.
   */
  void add_object(const std::shared_ptr<AddObject::Request> request,
                  std::shared_ptr<AddObject::Response> response);
  /**
   * @brief Callback to clear collision objects.
   * @param request The Trigger request.
   * @param response Response indicating whether the service call succeeded.
   */
  void clear_objects(const std::shared_ptr<Trigger::Request> request,
                     std::shared_ptr<Trigger::Response> response);
  /**
   * @brief Callback to toggle the octomap scan.
   * @param request The request to enable or disable the scan.
   * @param response Response indicating whether the service call succeeded.
   */
  void toggle_octomap_scan(const std::shared_ptr<SetBool::Request> request,
                           std::shared_ptr<SetBool::Response> response);
  /**
   * @brief Callback to define the goal_pose in the base frame.
   * @param request The DefineGoalPose request containing the desired pose.
   * @param response Response indicating whether the service call succeeded.
   */
  void define_goal_pose(const std::shared_ptr<DefineGoalPose::Request> request,
                        std::shared_ptr<DefineGoalPose::Response> response);
  /**
   * @brief Callback to offset goal_pose by a specified translation around a
   * specified axis.
   * @param request The TransformGoalPose request containing relevant axis and
   * translation.
   * @param response Response indicating whether the service call succeeded.
   */
  void transform_goal_pose(
      const std::shared_ptr<TransformGoalPose::Request> request,
      std::shared_ptr<TransformGoalPose::Response> response);
  /**
   * @brief Callback to move arm to a specified configuration (e.g. home).
   * @param request The MoveToConf request containing the configuration.
   * @param response Response indicating whether the service call succeeded.
   */
  void move_to_configuration(const std::shared_ptr<MoveToConf::Request> request,
                             std::shared_ptr<MoveToConf::Response> response);
  /**
   * @brief Callback to move arm to a specified goal Pose.
   * @param request The MoveHandToPose request containing the goal Pose and Pilz
   * planning type.
   * @param response Response indicating whether the service call succeeded.
   */
  void move_hand_to_pose(const std::shared_ptr<MoveHandToPose::Request> request,
                         std::shared_ptr<MoveHandToPose::Response> response);
  /**
   * @brief Callback to add a visual marker at a specified location.
   * @param request The AddMarker request containing the Pose to add the visual
   * marker.
   * @param response Response indicating whether the service call succeeded.
   */
  void add_marker(const std::shared_ptr<AddMarker::Request> request,
                  std::shared_ptr<AddMarker::Response> response);
  /**
   * @brief Callback to clear visual markers.
   * @param request The Trigger request.
   * @param response Response indicating whether the service call succeeded.
   */
  void clear_markers(const std::shared_ptr<Trigger::Request> request,
                     std::shared_ptr<Trigger::Response> response);
  /**
   * @brief Callback to visualize the desired grasp pose in RViz.
   * @param request The request containing the desired grasp pose.
   * @param response Response indicating whether the service call succeeded.
   */
  void visualize_grasp_pose(
      const std::shared_ptr<PoseStampedSrv::Request> request,
      std::shared_ptr<PoseStampedSrv::Response> response);
  /**
   * @brief Callback to create a motion plan to the desired goal pose.
   * @param request The request containing the desired goal pose.
   * @param response Response indicating whether the service call succeeded.
   */
  void create_plan(const std::shared_ptr<PoseStampedSrv::Request> request,
                   std::shared_ptr<PoseStampedSrv::Response> response);
  /**
   * @brief Callback to visualize the planned motion in RViz.
   * @param request The request containing the planned motion.
   * @param response Response indicating whether the service call succeeded.
   */
  void visualize_plan(const std::shared_ptr<Trigger::Request> request,
                      std::shared_ptr<Trigger::Response> response);
  /**
   * @brief Callback to execute the planned motion.
   * @param request The request containing the planned motion.
   * @param response Response indicating whether the service call succeeded.
   */
  void execute_plan(const std::shared_ptr<Trigger::Request> request,
                    std::shared_ptr<Trigger::Response> response);

  /**
   * @brief Initialize clients.
   */
  void initialize_clients();
  /**
   * @brief Initialize services.
   */
  void initialize_services();
  /**
   * @brief Change the frame of a pose.
   * @param pose The pose to transform.
   * @param target_frame The target frame to transform to.
   * @return The transformed pose.
   */
  PoseStamped change_frame(PoseStamped pose, std::string target_frame = "");
  /**
   * @brief Plan and execute a motion to the goal_pose.
   * @param planning_type The type of planning to use.
   * @return bool indicating success or failure.
   */
  bool plan_and_execute(std::string planning_type = "");
};
