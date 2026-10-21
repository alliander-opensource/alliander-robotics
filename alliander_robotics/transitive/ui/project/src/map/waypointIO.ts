// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import type { Waypoint } from "./waypoints";
import { newWaypoint } from "./waypoints";

export function serializeWaypoints(waypoints: Waypoint[]): string {
  return JSON.stringify(
    waypoints.map(({ lat, lng }) => ({ lat, lng })),
    null,
    2,
  );
}

export function parseWaypoints(json: string): Waypoint[] {
  const raw: unknown = JSON.parse(json);
  if (!Array.isArray(raw)) {
    throw new TypeError("Invalid waypoints file: expected an array");
  }
  return raw.map((entry) => {
    const { lat, lng } = entry ?? {};
    if (typeof lat !== "number" || typeof lng !== "number") {
      throw new TypeError("Invalid waypoints file: each entry needs numeric lat/lng");
    }
    return newWaypoint(lat, lng);
  });
}

export function downloadWaypoints(waypoints: Waypoint[], filename = "waypoints.json"): void {
  const blob = new Blob([serializeWaypoints(waypoints)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
  } finally {
    URL.revokeObjectURL(url);
  }
}

export async function readWaypointsFile(file: File): Promise<Waypoint[]> {
  const text = await file.text();
  return parseWaypoints(text);
}
