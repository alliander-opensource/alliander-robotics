// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import type { Waypoint } from "./map/waypoints";

export type Device = "simulation" | "lynx" | "panther" | "none";

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

export interface TriggerResponse {
  success: boolean;
  message: string;
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

export function pendingWaypoints(waypoints: Waypoint[], reached: Set<number>): Waypoint[] {
  return waypoints.filter((wp) => !reached.has(wp.id));
}
