// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";
import type { Publisher, Service } from "./capabilities/RosTool";
import { useRos } from "./capabilities/RosTool";
import type { TriggerResponse } from "./missionHelpers";
import { pendingWaypoints, toGeoPath } from "./missionHelpers";
import type { Waypoint } from "./waypoints";
import "./panels.css";

export interface MissionProps {
  namespace: string;
  onNamespaceChange: (namespace: string) => void;
  waypointsPublisher: Publisher;
  stopService: Service;
  reachedCount: number | null;
}

export function MissionPanel({
  props: { namespace, onNamespaceChange, waypointsPublisher, stopService, reachedCount },
  waypoints,
  reached,
  onReachedChange,
  onMissionActiveChange,
}: {
  props: MissionProps;
  waypoints: Waypoint[];
  reached: Set<number>;
  onReachedChange: (reached: Set<number>) => void;
  onMissionActiveChange: (active: boolean) => void;
}) {
  const { ready, publish, callService } = useRos();

  const [status, setStatus] = useState<"idle" | "running" | "paused">("idle");
  const [routeIds, setRouteIds] = useState<number[]>([]);

  useEffect(() => {
    onMissionActiveChange(status !== "idle");
  }, [status, onMissionActiveChange]);

  useEffect(() => {
    if (reachedCount === null || status === "idle") return;
    const done = routeIds.slice(0, reachedCount);
    if (done.length > 0) {
      onReachedChange(new Set([...reached, ...done]));
    }
  }, [reachedCount]);

  const sendRoute = (route: Waypoint[]) => {
    publish(waypointsPublisher, toGeoPath(route));
    setRouteIds(route.map((w) => w.id));
  };

  const stopNav2 = () => {
    callService<TriggerResponse>(stopService, {})
      .then((response) => console.debug("nav2 stop response", response))
      .catch((error) => console.warn("Failed to stop nav2", error));
  };

  const onStart = () => {
    const allReached = pendingWaypoints(waypoints, reached).length === 0;
    if (allReached) {
      onReachedChange(new Set());
    }
    sendRoute(allReached ? waypoints : pendingWaypoints(waypoints, reached));

    setStatus("running");
  };

  const onStop = () => {
    stopNav2();
    onReachedChange(new Set());
    setStatus("idle");
  };

  const onPauseResume = () => {
    if (status === "running") {
      stopNav2();
      setStatus("paused");
    } else {
      sendRoute(pendingWaypoints(waypoints, reached));
      setStatus("running");
    }
  };

  return (
    <div className="panelActions">
      <div className="sectionTitle">Mission</div>
      <div className="fieldLabel">Namespace:</div>
      <input
        type="text"
        value={namespace}
        onChange={(event) => onNamespaceChange(event.target.value)}
        placeholder="vehicle_namespace"
      />
      <div className="buttonRow">
        <button onClick={onStart} disabled={!ready || status !== "idle" || waypoints.length === 0}>
          Start
        </button>
        <button onClick={onStop} disabled={!ready || status === "idle"}>
          Stop
        </button>
        <button onClick={onPauseResume} disabled={!ready || status === "idle"}>
          {status === "paused" ? "Resume" : "Pause"}
        </button>
      </div>
    </div>
  );
}
