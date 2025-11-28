# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from math import atan2

import cv2
import numpy as np
from geometry_msgs.msg import Point as ros_Point
from geometry_msgs.msg import Pose as ros_Pose
from geometry_msgs.msg import Quaternion as ros_Quaternion
from tf_transformations import quaternion_from_euler


@dataclass
class Point2D:
    """A 2D point in space.

    Attributes:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
    """

    x: float
    y: float

    @property
    def as_tuple(self) -> tuple:
        """Return point as tuple.

        Returns:
            tuple: A tuple containing the x and y coordinates of the point.
        """
        return self.x, self.y

    @property
    def as_int_tuple(self) -> tuple:
        """Return point as tuple of integers.

        Returns:
            tuple: A tuple containing the x and y coordinates of the point as integers.
        """
        return int(self.x), int(self.y)

    @property
    def as_array(self) -> np.ndarray:
        """Return point as numpy array.

        Returns:
            np.ndarray: A numpy array containing the x and y coordinates of the point.
        """
        return np.array([self.x, self.y])

    def surrounding_points(self, grid_size: int = 5) -> "Point2DList":
        """       Calculate surrounding points in a grid around the point. 
        Args:
            grid_size (int): The size of the grid around the point. Defaults to 5.
        Returns:
            Point2DList: A Point2DList containing the surrounding points in a grid around the point.
        """
        surrounding_points = []
        for x_pos in range(self.x - grid_size, self.x + grid_size):
            for y_pos in range(self.y - grid_size, self.y + grid_size):
                surrounding_points.append(Point2D(x_pos, y_pos))
        return Point2DList(surrounding_points)


@dataclass
class Point3D:
    """A 3D point in space.

    Attributes:
        x (float): The x-coordinate of the point.
        y (float): The y-coordinate of the point.
        z (float): The z-coordinate of the point.
    """

    x: float
    y: float
    z: float

    @property
    def as_ros_point(self) -> ros_Point:
        """Return point as ROS Point message.

        Returns:
            ros_Point: A ROS Point message containing the x, y, and z coordinates of the point.
        """
        return ros_Point(x=self.x, y=self.y, z=self.z)


@dataclass
class Quaternion:
    """A quaternion representing orientation in 3D space.

    Attributes:
        x (float): The x component of the quaternion.
        y (float): The y component of the quaternion.
        z (float): The z component of the quaternion.
        w (float): The w component of the quaternion.
    """

    x: float
    y: float
    z: float
    w: float

    @property
    def as_tuple(self) -> tuple:
        """Return quaternion as tuple.

        Returns:
            tuple: A tuple containing the x, y, z, and w components of the quaternion.
        """
        return self.x, self.y, self.z, self.w

    @staticmethod
    def from_eulerangles(x: float, y: float, z: float) -> "Quaternion":
        """Create a quaternion from Euler angles in radians.
        Args:
            x (float): The roll angle in radians.
            y (float): The pitch angle in radians.
            z (float): The yaw angle in radians.
        Returns:
            Quaternion: A Quaternion object representing the orientation defined by the Euler angles.
        """
        x, y, z, w = quaternion_from_euler(x, y, z)
        return Quaternion(x, y, z, w)

    @staticmethod
    def from_eulerangles_deg(x: float, y: float, z: float) -> "Quaternion":
        """Create a quaternion from Euler angles in degrees.
        Args:
            x (float): The roll angle in degrees.
            y (float): The pitch angle in degrees.
            z (float): The yaw angle in degrees.
        Returns:  
            Quaternion: A Quaternion object representing the orientation defined by the Euler angles.
        """
        x, y, z, w = quaternion_from_euler(np.deg2rad(x), np.deg2rad(y), np.deg2rad(z))
        return Quaternion(x, y, z, w)

    @property
    def as_ros_quaternion(self) -> ros_Quaternion:
        """Return quaternion as ROS Quaternion message.

        Returns:
            ros_Quaternion: A ROS Quaternion message containing the x, y, z, and w components of the quaternion.
        """
        return ros_Quaternion(x=self.x, y=self.y, z=self.z, w=self.w)


@dataclass
class Pose:
    """A pose in 3D space defined by a position and orientation.

    Attributes:
        position (Point3D): The position of the pose in 3D space.
        orientation (Quaternion): The orientation of the pose in 3D space.
    """

    position: Point3D
    orientation: Quaternion

    @property
    def as_ros_pose(self) -> ros_Pose:
        """Return pose as ROS Pose message.

        Returns:
            ros_Pose: A ROS Pose message containing the position and orientation of the pose.
        """
        return ros_Pose(
            position=self.position.as_ros_point,
            orientation=self.orientation.as_ros_quaternion,
        )


@dataclass
class Point2DList:
    """A list of 2D points.

    Attributes:
        points (list[Point2D]): A list of Point2D objects.
    """

    points: list[Point2D]

    @property
    def mean(self) -> Point2D:
        """Calculate the mean point of the list of points. 
        Returns:
            Point2D: A Point2D object representing the mean point of the list.
        """
        x, y = np.mean([point.as_array for point in self.points], axis=0)
        return Point2D(x, y)


@dataclass
class Line:
    """A line segment defined by two 2D points.

    Attributes:
        p1 (Point2D): The first point of the line segment.
        p2 (Point2D): The second point of the line segment.
    """

    p1: Point2D
    p2: Point2D

    @property
    def length(self) -> float:
        """Calculate the length of the line segment.
        Returns:
            float: The length of the line segment, calculated as the Euclidean distance between p1 and p2.
        """
        return float(np.linalg.norm(self.p1.as_array - self.p2.as_array))

    @property
    def flipped(self) -> "Line":
        """Return a new Line with the points flipped.

        Returns:
            Line: A new Line object with the points p1 and p2 swapped.
        """
        return Line(self.p2, self.p1)

    def points_along(self, n: int) -> list[Point2D]:
        """Calculate n points along the line segment, excluding the endpoints.

        Args:
            n (int): The number of points to calculate along the line segment.

        Returns:
            list[Point2D]: A list of Point2D objects representing the points along the line segment.
        """
        points = np.linspace(self.p1.as_array, self.p2.as_array, n + 2, dtype=int)
        points = points[1:-1]  # remove edges
        return [Point2D(point[0], point[1]) for point in points]

    def angle(self) -> float:
        """Calculate the angle of the line segment in radians.

        Returns:
            float: The angle of the line segment in radians, measured from the positive x-axis.
        """
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        return atan2(dy, dx)


@dataclass
class SidePair:
    """A pair of line segments representing the long sides of a bounding box.

    Attributes:
        side1 (Line): The first line segment of the pair.
        side2 (Line): The second line segment of the pair.
    """

    side1: Line
    side2: Line

    def point_pairs(self, n: int = 5) -> list[Point2DList]:
        """Calculate n pairs of points along the long sides of the bounding box.

        Args:
            n (int): The number of pairs of points to calculate along the long sides.

        Returns:
            list[Point2DList]: A list of Point2DList objects, each containing a pair of points from the two sides.
        """
        points1 = self.side1.points_along(n)
        points2 = self.side2.points_along(n)
        return [Point2DList([points1[i], points2[i]]) for i in range(n)]


@dataclass
class BoundingBox:
    """A bounding box defined by its center, width, height, and rotation angle.

    Attributes:
        x (float): The x-coordinate of the center of the bounding box.
        y (float): The y-coordinate of the center of the bounding box.
        w (float): The width of the bounding box.
        h (float): The height of the bounding box.
        angle_deg (float): The rotation angle of the bounding box in degrees.
    """

    x: float
    y: float
    w: float
    h: float
    angle_deg: float

    @property
    def ordered_values(self) -> tuple[float]:
        """Return the bounding box values in a specific order.

        Returns:
            tuple[float]: A tuple containing the x, y, w, h, and angle_deg values of the bounding box.
        """
        return (self.x, self.y, self.w, self.h, self.angle_deg)

    @property
    def center(self) -> Point2D:
        """Return the center point of the bounding box.

        Returns:
            Point2D: A Point2D object representing the center of the bounding box.
        """
        return Point2D(self.x, self.y)

    @property
    def corners(self) -> list[Point2D]:
        """Calculate the corners of the bounding box.

        Returns:
            list[Point2D]: A list of Point2D objects representing the corners of the bounding box.
        """
        x, y, w, h, angle_deg = self.ordered_values
        return [Point2D(*point) for point in cv2.boxPoints(((x, y), (w, h), angle_deg))]

    @property
    def long_sides_offset(self) -> SidePair:
        """Calculate the long sides of the bounding box with an offset.

        This method adjusts the width or height of the bounding box by a factor to ensure the long sides are longer than the short sides.

        Returns:
            SidePair: A SidePair object containing the two long sides of the bounding box.
        """
        offset_factor: float = 1.6
        if self.h > self.w:
            self.w *= offset_factor
        else:
            self.h *= offset_factor
        corners = cv2.boxPoints(((self.x, self.y), (self.w, self.h), self.angle_deg))
        points = [Point2D(*corner) for corner in corners]
        sides = [Line(points[n], points[n - 1]) for n in range(len(corners))]
        sides.sort(key=lambda side: side.length)
        side1, side2 = sides[2:]
        return SidePair(side1, side2.flipped)
