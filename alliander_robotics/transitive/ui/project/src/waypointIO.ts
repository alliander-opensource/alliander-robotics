// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import type { Waypoint } from "./waypoints";
import { parseWaypoints, serializeWaypoints } from "./waypoints";

export function downloadWaypoints(
  waypoints: Waypoint[],
  filename = "waypoints.json",
): void {
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
