// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "moveit_manager.hpp"

MoveitManager::MoveitManager(rclcpp::Node::SharedPtr node_)
    : node(node_), tf_broadcaster(node),
      move_group(
          node,
          moveit::planning_interface::MoveGroupInterface::Options(
              "arm",
              moveit::planning_interface::MoveGroupInterface::ROBOT_DESCRIPTION,
              node->get_namespace())),
      rviz_visual_tools(base_frame, marker_topic, node),
      moveit_visual_tools(node, base_frame, marker_topic) {
  initialize_clients();

  namespace_arm = std::string(node->get_namespace()).erase(0, 1);
  namespace_camera = node->get_parameter("namespace_camera").as_string();

  jmg_arm = move_group.getRobotModel()->getJointModelGroup("arm");
  jmg_hand = move_group.getRobotModel()->getJointModelGroup("hand");
  jmg_tcp = move_group.getRobotModel()->getJointModelGroup("tcp");

  moveit_visual_tools.loadMarkerPub(false);
  moveit_visual_tools.loadRobotStatePub("display_robot_state");
  moveit_visual_tools.loadTrajectoryPub("display_planned_path_custom");

  auto link_tcp = jmg_tcp->getLinkModelNames().back();
  move_group.setEndEffectorLink(link_tcp);

  auto link_arm_end = jmg_arm->getLinkModelNames().back();
  PoseStamped arm_end_in_arm_frame;
  arm_end_in_arm_frame.header.frame_id = link_arm_end;
  arm_end_in_tcp_frame = change_frame(arm_end_in_arm_frame, link_tcp);

  initialize_services();
  RCLCPP_INFO(node->get_logger(), "Moveit Manager initialized.");
};

void MoveitManager::initialize_clients() {
  client_node = std::make_shared<rclcpp::Node>("moveit_manager_client");
  express_pose_in_other_frame_client =
      client_node->create_client<ExpressPoseInOtherFrame>(
          "/pose_manipulator/express_pose_in_other_frame");
};

void MoveitManager::initialize_services() {
  add_object_service = node->create_service<AddObject>(
      "~/add_object", std::bind(&MoveitManager::add_object, this, _1, _2));

  clear_objects_service = node->create_service<Trigger>(
      "~/clear_objects",
      std::bind(&MoveitManager::clear_objects, this, _1, _2));

  toggle_octomap_scan_service = node->create_service<SetBool>(
      "~/toggle_octomap_scan",
      std::bind(&MoveitManager::toggle_octomap_scan, this, _1, _2));

  define_goal_pose_service = node->create_service<DefineGoalPose>(
      "~/define_goal_pose",
      std::bind(&MoveitManager::define_goal_pose, this, _1, _2));

  transform_goal_pose_service = node->create_service<TransformGoalPose>(
      "~/transform_goal_pose",
      std::bind(&MoveitManager::transform_goal_pose, this, _1, _2));

  move_to_configuration_service = node->create_service<MoveToConf>(
      "~/move_to_configuration",
      std::bind(&MoveitManager::move_to_configuration, this, _1, _2));

  move_hand_to_pose_service = node->create_service<MoveHandToPose>(
      "~/move_hand_to_pose",
      std::bind(&MoveitManager::move_hand_to_pose, this, _1, _2));

  add_marker_service = node->create_service<AddMarker>(
      "~/add_marker", std::bind(&MoveitManager::add_marker, this, _1, _2));

  visualize_grasp_pose_service = node->create_service<PoseStampedSrv>(
      "~/visualize_grasp_pose",
      std::bind(&MoveitManager::visualize_grasp_pose, this, _1, _2));

  create_plan_service = node->create_service<PoseStampedSrv>(
      "~/create_plan", std::bind(&MoveitManager::create_plan, this, _1, _2));

  visualize_plan_service = node->create_service<Trigger>(
      "~/visualize_plan",
      std::bind(&MoveitManager::visualize_plan, this, _1, _2));

  execute_plan_service = node->create_service<Trigger>(
      "~/execute_plan", std::bind(&MoveitManager::execute_plan, this, _1, _2));

  clear_markers_service = node->create_service<Trigger>(
      "~/clear_markers",
      std::bind(&MoveitManager::clear_markers, this, _1, _2));
};

void MoveitManager::add_object(
    const std::shared_ptr<AddObject::Request> request,
    std::shared_ptr<AddObject::Response> response) {
  moveit_msgs::msg::CollisionObject collision_object;
  collision_object.header = request->pose.header;

  shape_msgs::msg::SolidPrimitive solid_primitive;
  try {
    solid_primitive.type = shapes.at(request->shape);
  } catch (std::out_of_range) {
    RCLCPP_ERROR(node->get_logger(), "Shape %s is not a valid option.}. Exit.",
                 request->shape.c_str());
    return;
  }

  std::vector<moveit_msgs::msg::CollisionObject> collision_objects;
  solid_primitive.dimensions = {request->d1, request->d2, request->d3};
  collision_object.primitives.push_back(solid_primitive);
  collision_object.primitive_poses.push_back(request->pose.pose);
  collision_object.operation = collision_object.ADD;
  collision_object.id = "object";
  collision_objects.push_back(collision_object);
  planning_scene_interface.addCollisionObjects(collision_objects);
  response->success = true;
};

void MoveitManager::clear_objects(
    const std::shared_ptr<Trigger::Request> request,
    std::shared_ptr<Trigger::Response> response) {
  planning_scene_interface.removeCollisionObjects({"object"});
  response->success = true;
};

/**
 * Toggle the octomap scan by running a launch file with topic_tools relay nodes
 * as a boost process. These relay nodes pass the depth_image and
 * camera_info to the topic where MoveIt octomap is subscribed. We use
 * topic_tools relay for performance, since this does not perform serialization
 * on the messages. We create a process group and terminate the whole group
 * instead of the process, since terminating a single process may leave child
 * processes running.
 */
void MoveitManager::toggle_octomap_scan(
    const std::shared_ptr<SetBool::Request> request,
    std::shared_ptr<SetBool::Response> response) {
  if (namespace_camera.empty()) {
    RCLCPP_ERROR(node->get_logger(),
                 "Namespace of camera is not set. Cannot toggle octomap scan.");
    return;
  }
  auto cmd = fmt::format("ros2 launch rcdt_moveit relay_octomap.launch.py "
                         "namespace_arm:={} namespace_camera:={}",
                         namespace_arm, namespace_camera);
  if (request->data) {
    if (process.running()) {
      RCLCPP_WARN(node->get_logger(),
                  "Cannot enable octomap scan: already active.");
      return;
    }
    process = boost::process::child(cmd, process_group);
    RCLCPP_INFO(node->get_logger(), "Octomap scan enabled.");
  } else {
    if (!process.running()) {
      RCLCPP_WARN(node->get_logger(),
                  "Cannot disable octomap scan: not active.");
      return;
    }
    process_group.terminate();
    RCLCPP_INFO(node->get_logger(), "Octomap scan disabled.");
  }
};

void MoveitManager::define_goal_pose(
    const std::shared_ptr<DefineGoalPose::Request> request,
    std::shared_ptr<DefineGoalPose::Response> response) {
  auto pose = change_frame(request->pose);
  goal_pose = pose;
  response->success = true;
};

void MoveitManager::transform_goal_pose(
    const std::shared_ptr<TransformGoalPose::Request> request,
    std::shared_ptr<TransformGoalPose::Response> response) {
  if (request->axis == "x") {
    goal_pose.pose.position.x += request->value;
  } else if (request->axis == "y") {
    goal_pose.pose.position.y += request->value;
  } else if (request->axis == "z") {
    goal_pose.pose.position.z += request->value;
  } else {
    RCLCPP_ERROR(node->get_logger(), "Axis must be one of 'x', 'y', 'z'.");
    response->success = false;
    return;
  }
  response->success = true;
};

void MoveitManager::move_to_configuration(
    const std::shared_ptr<MoveToConf::Request> request,
    std::shared_ptr<MoveToConf::Response> response) {
  move_group.setNamedTarget(request->configuration);
  response->success = plan_and_execute();
};

void MoveitManager::move_hand_to_pose(
    const std::shared_ptr<MoveHandToPose::Request> request,
    std::shared_ptr<MoveHandToPose::Response> response) {
  move_group.setPoseTarget(goal_pose);
  response->success = plan_and_execute(request->planning_type);
};

bool MoveitManager::plan_and_execute(std::string planning_type) {
  if (pilz_types.count(planning_type)) {
    move_group.setPlanningPipelineId("pilz_industrial_motion_planner");
    move_group.setPlannerId(planning_type);
  } else {
    move_group.setPlanningPipelineId("ompl");
  }
  moveit::planning_interface::MoveGroupInterface::Plan plan;
  auto error_code = move_group.plan(plan);
  if (error_code != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(node->get_logger(), "Failed to generate plan.");
    return false;
  }

  moveit_visual_tools.deleteAllMarkers("Path");
  moveit_visual_tools.deleteAllMarkers("Sphere");
  moveit_visual_tools.publishTrajectoryLine(plan.trajectory, jmg_arm);
  moveit_visual_tools.trigger();

  error_code = move_group.execute(plan);
  if (error_code != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(node->get_logger(), "Failed to execute plan.");
    return false;
  }
  return true;
};

PoseStamped MoveitManager::change_frame(PoseStamped pose,
                                        std::string target_frame) {
  if (target_frame == "") {
    target_frame = base_frame;
  }
  auto request = std::make_shared<ExpressPoseInOtherFrame::Request>();
  request->pose = pose;
  request->target_frame = target_frame;
  while (!express_pose_in_other_frame_client->service_is_ready()) {
    RCLCPP_WARN(
        node->get_logger(),
        "Waiting for express_pose_in_other_frame service to be available...");
    rclcpp::sleep_for(std::chrono::seconds(1));
  }
  auto future = express_pose_in_other_frame_client->async_send_request(request);
  rclcpp::spin_until_future_complete(client_node, future);
  auto response = future.get();
  return response->pose;
};

void MoveitManager::add_marker(
    const std::shared_ptr<AddMarker::Request> request,
    std::shared_ptr<AddMarker::Response> response) {
  auto pose = change_frame(request->marker_pose);
  moveit_visual_tools.publishAxis(pose.pose);
  moveit_visual_tools.trigger();
  response->success = true;
};

void MoveitManager::visualize_grasp_pose(
    const std::shared_ptr<PoseStampedSrv::Request> request,
    std::shared_ptr<PoseStampedSrv::Response> response) {
  // Broadcast a tf frame at the desired Tool Center Point location:
  TransformStamped tf;
  tf.header = request->pose.header;
  tf.header.stamp = node->now();
  tf.transform.translation.x = request->pose.pose.position.x;
  tf.transform.translation.y = request->pose.pose.position.y;
  tf.transform.translation.z = request->pose.pose.position.z;
  tf.transform.rotation = request->pose.pose.orientation;
  tf.child_frame_id = "desired_tcp";
  tf_broadcaster.sendTransform(tf);

  // Define the arm_end_link in the desired_tcp_frame and convert to base:
  PoseStamped arm_end_in_desired_tcp_frame;
  arm_end_in_desired_tcp_frame.header.frame_id = "desired_tcp";
  arm_end_in_desired_tcp_frame.pose = arm_end_in_tcp_frame.pose;
  auto arm_end_in_base_frame = change_frame(arm_end_in_desired_tcp_frame);

  // Publish the End Effector marker:
  std::vector<double> positions = {0.04};
  moveit_visual_tools.publishEEMarkers(arm_end_in_base_frame.pose, jmg_hand,
                                       positions, rviz_visual_tools::BLUE);
  response->success = true;
}

void MoveitManager::create_plan(
    const std::shared_ptr<PoseStampedSrv::Request> request,
    std::shared_ptr<PoseStampedSrv::Response> response) {
  move_group.setPoseTarget(request->pose);
  auto error_code = move_group.plan(plan);
  if (error_code != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(node->get_logger(), "Failed to generate plan.");
  }

  // Visualize the goal state in RViz:
  auto goal_positions =
      plan.trajectory.joint_trajectory.points.back().positions;
  moveit::core::RobotState goal_state(move_group.getRobotModel());
  goal_state.setJointGroupPositions(jmg_arm, goal_positions);
  moveit_visual_tools.publishRobotState(goal_state, rviz_visual_tools::ORANGE);
  response->success = true;
}

void MoveitManager::visualize_plan(
    const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
  moveit::core::RobotState state(move_group.getRobotModel());
  moveit_visual_tools.publishTrajectoryPath(plan.trajectory, state);
  response->success = true;
}

void MoveitManager::execute_plan(
    const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
  auto error_code = move_group.execute(plan);
  response->success = (error_code == moveit::core::MoveItErrorCode::SUCCESS);
  if (!response->success) {
    RCLCPP_ERROR(node->get_logger(), "Failed to execute plan.");
  }
}

void MoveitManager::clear_markers(
    const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
  moveit_visual_tools.deleteAllMarkers("Axis");
  moveit_visual_tools.trigger();
  response->success = true;
}

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions node_options;
  node_options.automatically_declare_parameters_from_overrides(true);
  auto node = std::make_shared<rclcpp::Node>("moveit_manager", node_options);
  auto moveit_manager = MoveitManager(node);
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
}
