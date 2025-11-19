# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import shutil
import subprocess

import xmltodict
from pyproj import Geod
from rcdt_utilities.launch_utils import get_file_path
from rclpy.logging import get_logger
from termcolor import colored

logger = get_logger("create_sdf")


def create_map_world(lon: float, lat: float) -> None:
    """Create a map world SDF file based on the given longitude and latitude.

    Args:
        lon (float): The longitude of the map center.
        lat (float): The latitude of the map center.
    """
    download_map(lon, lat)
    convert_map()
    create_sfd(lon, lat)


def download_map(lon: float, lat: float) -> None:
    """Download map data from OpenStreetMap for the specified longitude and latitude.

    Args:
        lon (float): The longitude of the map center.
        lat (float): The latitude of the map center.
    """
    logger.info(colored("Downloading map data from OpenStreetMap...", "dark_grey"))
    geo = Geod(ellps="WGS84")
    distance = 100  # meters

    lats = []
    longs = []
    angle = 45

    for _ in range(4):
        corner = geo.fwd(lon, lat, angle, distance)
        longs.append(corner[0])
        lats.append(corner[1])
        angle += 90

    min_lon = min(longs)
    max_lon = max(longs)
    min_lat = min(lats)
    max_lat = max(lats)

    cmd_download = [
        "wget",
        "-O",
        "/tmp/map.osm",
        f"https://api.openstreetmap.org/api/0.6/map?bbox={min_lon},{min_lat},{max_lon},{max_lat}",
    ]
    subprocess.run(cmd_download, check=False, stderr=subprocess.DEVNULL)


def convert_map() -> None:
    """Convert the downloaded OSM map data to glb format."""
    logger.info(colored("Converting map data to glb format...", "dark_grey"))
    shutil.copy(
        get_file_path("rcdt_gazebo", ["config"], "osm2world.properties"),
        "/home/rcdt/osm2world/osm2world.properties",
    )
    cmd_convert = [
        "bash",
        "/home/rcdt/osm2world/osm2world.sh",
        "convert",
        "--config",
        "/home/rcdt/osm2world/osm2world.properties",
        "-i",
        "/tmp/map.osm",
        "-o",
        "/tmp/map.glb",
    ]
    subprocess.run(cmd_convert, check=False)


def create_sfd(lon: float, lat: float) -> None:
    """Create an SDF world file from the glb map object.

    Args:
        lon (float): The longitude of the map center.
        lat (float): The latitude of the map center.
    """
    logger.info(colored("Creating SDF file from glb object...", "dark_grey"))
    file_path = get_file_path("rcdt_gazebo", ["worlds"], "world.sdf")
    with open(file_path, encoding="utf-8") as fd:
        sdf_string = fd.read()

    sdf_dict = xmltodict.parse(sdf_string)
    sdf_dict["sdf"]["world"]["spherical_coordinates"]["longitude_deg"] = lon
    sdf_dict["sdf"]["world"]["spherical_coordinates"]["latitude_deg"] = lat

    with open("/tmp/world.sdf", "w", encoding="utf-8") as fd:
        fd.write(xmltodict.unparse(sdf_dict))
