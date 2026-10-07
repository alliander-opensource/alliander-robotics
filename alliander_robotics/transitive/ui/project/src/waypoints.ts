// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

export interface Waypoint {
  id: number;
  lat: number;
  lng: number;
}

let nextId = 0;

export function newWaypoint(lat: number, lng: number): Waypoint {
  return { id: nextId++, lat, lng };
}

export function addWaypoint(waypoints: Waypoint[], lat: number, lng: number): Waypoint[] {
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
  return waypoints.map((w) => (w.id === id ? { ...w, lat, lng } : w));
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
