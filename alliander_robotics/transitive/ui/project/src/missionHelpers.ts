import type { Waypoint } from "./waypoints";

export function toGeoPath(waypoints: Waypoint[]) {
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
) {
  // TODO: we should base this on feedback from the robot about its current waypoint
  if (position === null) {
    return waypoints;
  }

  var closest_wp_idx = 0;
  var min_dist = 1e9;
  for (const wp of waypoints) {
    var dist = getDistance(position, wp);
    if (dist < min_dist) {
      min_dist = dist;
      closest_wp_idx = wp.id;
    }
  }

  console.debug("Closest waypoint: ", closest_wp_idx);
  return waypoints.splice(0, closest_wp_idx);
}

function getDistance(curr: [number, number], wp: Waypoint) {
  // TODO: indexing correct?
  return Math.sqrt((curr[0] - wp.lat) ** 2 + (curr[1] - wp.lng) ** 2);
}
