// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import type { Waypoint } from "./waypoints";
import {
  addWaypoint,
  removeWaypoint,
  moveWaypoint,
  reorderWaypoint,
  clearWaypoints,
} from "./waypoints";
import { downloadWaypoints, readWaypointsFile } from "./waypointIO";

export function useWaypoints() {
  const [waypoints, setWaypoints] = useState<Waypoint[]>([]);
  const [reached, setReached] = useState<Set<number>>(new Set());

  const onAdd = (lat: number, lng: number) => {
    setWaypoints((wps) => addWaypoint(wps, lat, lng));
  };
  const onRemove = (id: number) => {
    setWaypoints((wps) => removeWaypoint(wps, id));
  };
  const onMove = (id: number, lat: number, lng: number) => {
    setWaypoints((wps) => moveWaypoint(wps, id, lat, lng));
  };
  const onReorder = (id: number, direction: "up" | "down") => {
    setWaypoints((wps) => reorderWaypoint(wps, id, direction));
  };
  const onSave = () => {
    downloadWaypoints(waypoints);
  };
  const onLoad = async (file: File) => {
    try {
      setWaypoints(await readWaypointsFile(file));
    } catch (err) {
      console.error("Failed to load waypoints:", err);
    }
  };
  const onClear = () => {
    setWaypoints((wps) => clearWaypoints(wps));
  };

  return {
    waypoints,
    reached,
    onReachedChange: setReached,
    onAdd,
    onRemove,
    onMove,
    onReorder,
    onSave,
    onLoad,
    onClear,
  };
}
