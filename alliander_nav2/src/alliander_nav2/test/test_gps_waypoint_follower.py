# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import math
from dataclasses import dataclass
from enum import Enum, auto

import rclpy
from geographic_msgs.msg import GeoPose
from geometry_msgs.msg import Quaternion
from nav2_msgs.action import FollowGPSWaypoints
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.task import Future


@dataclass(frozen=True)
class GPSWaypoint:
    """Dataclass containing lat/lon and optional yaw orientation.

    Attributes:
        latitude (float): latitude of GPS waypoint.
        longitude (float): longitude of GPS waypoint.
        yaw (float): yaw of GPS waypoint.
    """

    latitude: float
    longitude: float
    yaw: float = 0.0


class Route(Enum):
    """Enum containing predefined routes for GPS Waypoint Follower.

    Attributes:
        KB_TRUCK_PARKING_LOT: Route nearby Roboticalab entrance.
        SIM_TIGHT_ALLEYS: Simulation route in Arnhem, with buildings close together.
    """

    KB_TRUCK_PARKING_LOT = auto()
    SIM_TIGHT_ALLEYS = auto()


ROUTES: dict[Route, list[GPSWaypoint]] = {
    Route.KB_TRUCK_PARKING_LOT: [
        GPSWaypoint(51.966663, 5.940867),
        GPSWaypoint(51.966511, 5.940912),
        GPSWaypoint(51.966512, 5.940945),
        GPSWaypoint(51.966661, 5.940892, yaw=math.pi / 4),
    ],
    Route.SIM_TIGHT_ALLEYS: [
        GPSWaypoint(51.977291, 5.954022, yaw=-math.pi),
        GPSWaypoint(51.977251, 5.954025, yaw=-math.pi / 4),
        GPSWaypoint(51.977213, 5.954037, yaw=-3 * math.pi / 4),
        GPSWaypoint(51.977203, 5.954130, yaw=math.pi / 6),
        GPSWaypoint(51.977226, 5.954096, yaw=-5 * math.pi / 6),
        GPSWaypoint(51.977172, 5.954103, yaw=-3 * math.pi / 4),
        GPSWaypoint(51.977172, 5.954198, yaw=3 * math.pi / 4),
        GPSWaypoint(51.977209, 5.954075, yaw=7 * math.pi / 4),
        GPSWaypoint(51.977229, 5.953975, yaw=math.pi / 2),
    ],
}


class GPSWaypointFollower(Node):
    """Class that sends predefined routes to nav2's GPS waypoint follower action server."""

    def __init__(self):
        """Sets up the action client."""
        super().__init__("test_gps_waypoints")
        self.ac = ActionClient(
            self, FollowGPSWaypoints, "/panther/follow_gps_waypoints"
        )

    def send_goal(self, route: Route) -> Future:
        """Sends a Route to the nav2 action server.

        Args:
            route (Route): predefined set of waypoints to send.

        Returns:
            Future: future that can be awaited by rclpy.
        """
        self.ac.wait_for_server()

        waypoints = ROUTES[route]
        goal_msg = FollowGPSWaypoints.Goal()
        goal_msg.gps_poses = [self._to_gps_pose(wp) for wp in waypoints]
        print(f"goal: {goal_msg}")

        future = self.ac.send_goal_async(goal_msg, feedback_callback=self.cb_feedback)
        future.add_done_callback(self.cb_result)
        return future

    def cb_feedback(self, feedback_msg: FollowGPSWaypoints.Feedback) -> None:
        """Callback for feedback from the action server.

        Args:
            feedback_msg (FollowGPSWaypoints.Feedback): feedback indicating current waypoint being followed.
        """
        self.get_logger().info(
            f"Now navigating to waypoint {feedback_msg.current_waypoint}."
        )

    def cb_result(self, result_msg: FollowGPSWaypoints.Result) -> None:
        """Callback for result from the action server.

        Args:
            result_msg (FollowGPSWaypoints.Result): message indicating statistics of operation.
        """
        self.get_logger().info(
            f"Completed waypoints.\nMissed waypoints: {result_msg.missed_waypoints}\nError msg: {result_msg.error_msg}"
        )

    @staticmethod
    def _to_gps_pose(wp: GPSWaypoint) -> GeoPose:
        pose = GeoPose()
        pose.position.latitude = wp.latitude
        pose.position.longitude = wp.longitude
        pose.orientation = GPSWaypointFollower._yaw_to_quaternion(wp.yaw)
        return pose

    @staticmethod
    def _yaw_to_quaternion(yaw: float) -> Quaternion:
        q = Quaternion()
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q


if __name__ == "__main__":
    route_input = input(
        f"\nGPS Waypoint Follower test script.\nChoose one of the following routes:\n{ROUTES}\n\nInput: "
    )
    match route_input:
        case "KB_TRUCK_PARKING_LOT" | 1:
            route = Route.KB_TRUCK_PARKING_LOT
        case "SIM_TIGHT_ALLEYS" | 2:
            route = Route.SIM_TIGHT_ALLEYS
        case _:
            print("No valid route given. Defaulting to SIM_TIGHT_ALLEYS.")
            route = Route.SIM_TIGHT_ALLEYS

    rclpy.init()
    gps_waypoint_follower = GPSWaypointFollower()

    future = gps_waypoint_follower.send_goal(route)
    rclpy.spin_until_future_complete(gps_waypoint_follower, future)

    gps_waypoint_follower.destroy_node()
    rclpy.shutdown()
