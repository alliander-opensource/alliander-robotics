// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";
import { useRos } from "../capabilities/RosTool";
import type { TriggerResponse } from "../missionHelpers";
import { pendingWaypoints, toGeoPath } from "../missionHelpers";
import type { Ros } from "../ros/ros";
import "./panels.css";
import type { UseWaypoints } from "./useWaypoints";
import type { Waypoint } from "./waypoints";

export function MissionPanel({
  ros,
  wp,
  onMissionActiveChange,
}: Readonly<{
  ros: Ros;
  wp: UseWaypoints;
  onMissionActiveChange: (active: boolean) => void;
}>) {
  const { ready, publish, callService } = useRos();

  const [status, setStatus] = useState<"idle" | "running" | "paused">("idle");
  const [routeIds, setRouteIds] = useState<number[]>([]);

  useEffect(() => {
    onMissionActiveChange(status !== "idle");
  }, [status, onMissionActiveChange]);

  useEffect(() => {
    if (ros.subscriptions.reachedCount === null || status === "idle") return;
    const done = routeIds.slice(0, ros.subscriptions.reachedCount);
    if (done.length > 0) {
      wp.onReachedChange(new Set([...wp.reached, ...done]));
    }
  }, [ros.subscriptions.reachedCount]);

  const sendRoute = (route: Waypoint[]) => {
    publish(ros.publishers.geopath, toGeoPath(route));
    setRouteIds(route.map((w) => w.id));
  };

  const stopNav2 = () => {
    callService<TriggerResponse>(ros.services.nav2_stop, {})
      .then((response) => console.debug("nav2 stop response", response))
      .catch((error) => console.warn("Failed to stop nav2", error));
  };

  const onStart = () => {
    const allReached = pendingWaypoints(wp.waypoints, wp.reached).length === 0;
    if (allReached) {
      wp.onReachedChange(new Set());
    }
    sendRoute(allReached ? wp.waypoints : pendingWaypoints(wp.waypoints, wp.reached));

    setStatus("running");
  };

  const onStop = () => {
    stopNav2();
    wp.onReachedChange(new Set());
    setStatus("idle");
  };

  const onPauseResume = () => {
    if (status === "running") {
      stopNav2();
      setStatus("paused");
    } else {
      sendRoute(pendingWaypoints(wp.waypoints, wp.reached));
      setStatus("running");
    }
  };

  return (
    <div className="panelActions">
      <div className="sectionTitle">Mission</div>
      <div className="buttonRow">
        <button
          onClick={onStart}
          disabled={!ready || status !== "idle" || wp.waypoints.length === 0}
        >
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
