// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import { downloadWaypoints, readWaypointsFile } from "./waypointIO";
import type { Waypoint } from "./waypoints";
import {
  addWaypoint,
  clearWaypoints,
  moveWaypoint,
  removeWaypoint,
  reorderWaypoint,
} from "./waypoints";

export interface UseWaypoints {
  waypoints: Waypoint[];
  reached: Set<number>;
  onAdd: (lat: number, lng: number) => void;
  onRemove: (id: number) => void;
  onMove: (id: number, lat: number, lng: number) => void;
  onReorder: (id: number, direction: "up" | "down") => void;
  onSave: () => void;
  onLoad: (file: File) => Promise<void>;
  onClear: () => void;
  onReachedChange: (reached: Set<number>) => void;
}

export function UseWaypoints() {
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

  const use_waypoints: UseWaypoints = {
    waypoints,
    reached,
    onAdd,
    onRemove,
    onMove,
    onReorder,
    onSave,
    onLoad,
    onClear,
    onReachedChange: setReached,
  };

  return use_waypoints;
}
