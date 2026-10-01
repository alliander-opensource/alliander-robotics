// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import type { Waypoint } from "./waypoints";

interface GeoPoint {
  latitude: number;
  longitude: number;
  altitude: number;
}

interface Quaternion {
  x: number;
  y: number;
  z: number;
  w: number;
}

interface GeoPoseStamped {
  header: { frame_id: string };
  pose: {
    position: GeoPoint;
    orientation: Quaternion;
  };
}

interface GeoPath {
  header: { frame_id: string };
  poses: GeoPoseStamped[];
}

export function toGeoPath(waypoints: Waypoint[]): GeoPath {
  return {
    header: { frame_id: "map" },
    poses: waypoints.map((wp) => ({
      header: { frame_id: "map" },
      pose: {
        position: { latitude: wp.lat, longitude: wp.lng, altitude: 0 },
        orientation: { x: 0, y: 0, z: 0, w: 1 },
      },
    })),
  };
}

export function remainingWaypoints(
  waypoints: Waypoint[],
  position: [number, number] | null,
): Waypoint[] {
  // TODO: we should base this on feedback from the robot about its current waypoint
  if (position === null || waypoints.length === 0) {
    return waypoints;
  }

  let closestIndex = 0;
  let minDist = Infinity;
  waypoints.forEach((wp, index) => {
    const dist = getDistance(position, wp);
    if (dist < minDist) {
      minDist = dist;
      closestIndex = index;
    }
  });

  return waypoints.slice(closestIndex);
}

function getDistance(curr: [number, number], wp: Waypoint) {
  return Math.hypot(curr[0] - wp.lat, curr[1] - wp.lng);
}
