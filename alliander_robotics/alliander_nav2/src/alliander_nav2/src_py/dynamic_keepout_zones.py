#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import math

import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import NavSatFix
from std_srvs.srv import Trigger


class DynamicKeepoutPublisher(Node):
    """Publishes a dynamically generated static keepout mask."""

    def __init__(self):
        """Initialize the dynamic keepout publisher."""
        super().__init__("dynamic_keepout_publisher")

        # ============================================================
        # MAP
        # ============================================================

        self.resolution = 0.1
        self.width = 400
        self.height = 400

        self.origin_x = -10.0
        self.origin_y = -10.0

        # ============================================================
        # GPS
        # ============================================================

        self.current_lat = None
        self.current_lon = None

        self.previous_lat = None
        self.previous_lon = None

        # Heading in radians.
        #
        # 0 rad      = East
        # pi/2 rad   = North
        #
        self.heading = None

        # Eerste GPS positie = lokale GPS oorsprong
        self.reference_lat = None
        self.reference_lon = None

        self.gps_subscriber = self.create_subscription(
            NavSatFix,
            "/ublox/gps/fix",
            self.gps_callback,
            10,
        )

        # ============================================================
        # KEEP OUT MAP
        # ============================================================
        mask_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.publisher_ = self.create_publisher(
            OccupancyGrid,
            "/panther/keepout_filter_mask",
            qos_profile=mask_qos,
        )

        # Elke service-call voegt een nieuwe zone toe
        self.srv = self.create_service(
            Trigger,
            "/add_ui_nogozone",
            self.add_zone_callback,
        )

        # ============================================================
        # MAP DATA
        # ============================================================

        # 0   = free
        # 100 = keepout
        self.mask_data = [0] * (self.width * self.height)

        # Aantal keepout-zones
        self.zone_count = 0

        # Lege mask publiceren
        self.publish_mask()

        # self.mask_timer = self.create_timer(
        #     1.0,
        #     self.publish_mask
        # )

        self.get_logger().info(
            "Dynamic GPS Keepout Publisher gestart."
        )

    # ================================================================
    # GPS
    # ================================================================

    def gps_callback(self, msg):
        """Process a new GPS position."""
        if msg.status.status < 0:
            self.get_logger().warn(
                "Ongeldige GPS-fix ontvangen."
            )
            return

        # Eerste GPS-fix
        if self.reference_lat is None:
            self.reference_lat = msg.latitude
            self.reference_lon = msg.longitude

            self.get_logger().info(
                f"GPS referentie ingesteld:\n"
                f"  lat = {self.reference_lat:.8f}\n"
                f"  lon = {self.reference_lon:.8f}"
            )

        # Als we al een vorige positie hebben,
        # kunnen we de rijrichting bepalen.
        if self.previous_lat is not None:

            delta_x, delta_y = self.gps_to_local_xy(
                msg.latitude,
                msg.longitude,
            )

            previous_x, previous_y = self.gps_to_local_xy(
                self.previous_lat,
                self.previous_lon,
            )

            dx = delta_x - previous_x
            dy = delta_y - previous_y

            distance = math.sqrt(
                dx * dx + dy * dy
            )

            # Alleen heading aanpassen als de robot
            # daadwerkelijk bewogen is.
            if distance > 0.05:
                self.heading = math.atan2(
                    dy,
                    dx,
                )

        # Huidige positie opslaan
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

        self.previous_lat = msg.latitude
        self.previous_lon = msg.longitude

    # ================================================================
    # GPS -> LOKALE METERS
    # ================================================================

    def gps_to_local_xy(self, latitude, longitude):
        """Convert GPS coordinates to local East/North coordinates."""
        if self.reference_lat is None:
            return None, None

        earth_radius = 6378137.0

        delta_lat = math.radians(
            latitude - self.reference_lat
        )

        delta_lon = math.radians(
            longitude - self.reference_lon
        )

        reference_lat_rad = math.radians(
            self.reference_lat
        )

        north = (
            earth_radius *
            delta_lat
        )

        east = (
            earth_radius *
            math.cos(reference_lat_rad) *
            delta_lon
        )

        return east, north

    # ================================================================
    # LOKALE METERS -> MAP PIXELS
    # ================================================================

    def local_to_pixel(self, x, y):
        """Convert local map coordinates to OccupancyGrid pixels."""
        pixel_x = int(
            (x - self.origin_x) /
            self.resolution
        )

        pixel_y = int(
            (y - self.origin_y) /
            self.resolution
        )

        return pixel_x, pixel_y

    # ================================================================
    # STATISCHE KEEP OUT TOEVOEGEN
    # ================================================================

    def add_zone_callback(self, request, response):
        """Add a new 1x1 m keepout zone 3 m in front of the robot."""

        # ------------------------------------------------------------
        # Controle GPS
        # ------------------------------------------------------------

        if self.current_lat is None:

            response.success = False
            response.message = (
                "Nog geen GPS-fix ontvangen."
            )

            return response

        # ------------------------------------------------------------
        # Controle heading
        # ------------------------------------------------------------

        if self.heading is None:

            response.success = False
            response.message = (
                "Nog geen geldige rijrichting beschikbaar. "
                "Laat de robot eerst een klein stukje bewegen."
            )

            return response

        # ------------------------------------------------------------
        # Robotpositie
        # ------------------------------------------------------------

        robot_x, robot_y = self.gps_to_local_xy(
            self.current_lat,
            self.current_lon,
        )

        self.get_logger().info(
            f"Robotpositie:\n"
            f"  X = {robot_x:.2f} m\n"
            f"  Y = {robot_y:.2f} m"
        )

        # ------------------------------------------------------------
        # Robot heading
        #
        # heading:
        #   0       = East
        #   pi/2    = North
        #   pi      = West
        #   -pi/2   = South
        # ------------------------------------------------------------

        heading_x = math.cos(self.heading)
        heading_y = math.sin(self.heading)

        heading_degrees = math.degrees(
            self.heading
        )

        self.get_logger().info(
            f"Robot heading: "
            f"{heading_degrees:.1f} graden"
        )

        # ------------------------------------------------------------
        # 3 meter VOOR de robot
        # ------------------------------------------------------------

        distance_in_front = 3.0

        zone_center_x = (
            robot_x +
            heading_x * distance_in_front
        )

        zone_center_y = (
            robot_y +
            heading_y * distance_in_front
        )

        # ------------------------------------------------------------
        # Vierkant 1 x 1 meter
        # ------------------------------------------------------------

        size = 1.0

        min_x = (
            zone_center_x -
            size / 2.0
        )

        max_x = (
            zone_center_x +
            size / 2.0
        )

        min_y = (
            zone_center_y -
            size / 2.0
        )

        max_y = (
            zone_center_y +
            size / 2.0
        )

        # ------------------------------------------------------------
        # Naar pixels
        # ------------------------------------------------------------

        min_px, min_py = self.local_to_pixel(
            min_x,
            min_y,
        )

        max_px, max_py = self.local_to_pixel(
            max_x,
            max_y,
        )

        # ------------------------------------------------------------
        # Binnen map houden
        # ------------------------------------------------------------

        min_px = max(
            0,
            min_px,
        )

        min_py = max(
            0,
            min_py,
        )

        max_px = min(
            self.width,
            max_px,
        )

        max_py = min(
            self.height,
            max_py,
        )

        # ------------------------------------------------------------
        # Controleren of zone binnen de map valt
        # ------------------------------------------------------------

        if (
            min_px >= max_px or
            min_py >= max_py
        ):

            response.success = False
            response.message = (
                "Keepout-zone valt buiten de map."
            )

            return response

        # ------------------------------------------------------------
        # Vierkant tekenen
        #
        # BELANGRIJK:
        # bestaande zones worden NIET gewist.
        # We zetten alleen extra pixels op 100.
        # ------------------------------------------------------------

        for y in range(
            min_py,
            max_py,
        ):

            for x in range(
                min_px,
                max_px,
            ):

                index = (
                    y * self.width +
                    x
                )

                self.mask_data[index] = 100

        # ------------------------------------------------------------
        # Zone counter
        # ------------------------------------------------------------

        self.zone_count += 1

        # ------------------------------------------------------------
        # Nieuwe mask publiceren
        # ------------------------------------------------------------

        self.publish_mask()

        self.get_logger().info(
            f"KEEP OUT #{self.zone_count} AANGEMAAKT\n"
            f"Centrum:\n"
            f"  X = {zone_center_x:.2f} m\n"
            f"  Y = {zone_center_y:.2f} m\n"
            f"Grootte: 1 x 1 meter\n"
            f"Afstand voor robot: 3 meter"
        )

        response.success = True

        response.message = (
            f"Keepout #{self.zone_count} "
            f"(1x1m) geplaatst op 3 meter "
            f"voor de robot."
        )

        return response

    # ================================================================
    # PUBLICEREN
    # ================================================================

    def publish_mask(self):
        """Publish the current keepout mask."""
        msg = OccupancyGrid()

        msg.header.stamp = (
            self.get_clock().now().to_msg()
        )

        msg.header.frame_id = "map"

        msg.info.resolution = self.resolution
        msg.info.width = self.width
        msg.info.height = self.height

        msg.info.origin.position.x = (
            self.origin_x
        )

        msg.info.origin.position.y = (
            self.origin_y
        )

        msg.info.origin.orientation.w = 1.0

        msg.data = self.mask_data

        self.publisher_.publish(msg)


def main(args=None):
    """Start the dynamic keepout publisher."""
    rclpy.init(args=args)

    node = DynamicKeepoutPublisher()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
