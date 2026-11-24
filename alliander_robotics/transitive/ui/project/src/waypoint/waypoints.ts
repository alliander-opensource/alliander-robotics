// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

export class Waypoint {
  readonly id: number;
  lat: number;
  lng: number;
  rot: number | null;
  selected: boolean;

  constructor(id: number, lat: number, lng: number, rot: number | null = null) {
    this.id = id;
    this.lat = lat;
    this.lng = lng;
    this.rot = rot;
    this.selected = false;
  }

  rot_deg(): number | null {
    return this.rot !== null ? (this.rot * (180 / Math.PI) + 360) % 360 : null;
  }
  rot_str(): string {
    const deg = this.rot_deg();
    return deg !== null ? String(Math.floor(deg)).padStart(3, "0") : "";
  }
}

let nextId = 0;

export function newWaypoint(
  lat: number,
  lng: number,
  rot: number | null = null,
): Waypoint {
  return new Waypoint(nextId++, lat, lng, rot);
}

export function addWaypoint(
  waypoints: Waypoint[],
  lat: number,
  lng: number,
): Waypoint[] {
  return [...waypoints, newWaypoint(lat, lng)];
}

export function removeWaypoint(waypoints: Waypoint[], id: number): Waypoint[] {
  return waypoints.filter((w) => w.id !== id);
}

export function moveWaypoint(
  waypoints: Waypoint[],
  id: number,
  lat: number,
  lng: number,
): Waypoint[] {
  return waypoints.map((w) =>
    w.id === id ? new Waypoint(w.id, lat, lng, w.rot) : w,
  );
}

export function reorderWaypoint(
  waypoints: Waypoint[],
  id: number,
  direction: "up" | "down",
): Waypoint[] {
  const index = waypoints.findIndex((w) => w.id === id);
  const target = direction === "up" ? index - 1 : index + 1;

  // At boundaries, disable reorder
  if (index === -1 || target < 0 || target >= waypoints.length) {
    return waypoints;
  }

  const result = [...waypoints];
  [result[index], result[target]] = [result[target], result[index]];
  return result;
}

export function clearWaypoints(_waypoints: Waypoint[]): Waypoint[] {
  return [];
}
