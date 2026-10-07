// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useContext, useEffect, useState } from "react";
import { CapabilityContext, CapabilityContextProvider } from "@transitive-sdk/utils-web";
import { generateJWT } from "./capabilities/jwt";
import { pendingWaypoints, toGeoPath } from "./missionHelpers";
import type { Waypoint } from "./waypoints";
import "./panels.css";

const GPS_WAYPOINTS_TOPIC = "/gps_waypoints";
const GEO_PATH_TYPE = "geographic_msgs/msg/GeoPath";
const TRIGGER_TYPE = "std_srvs/srv/Trigger";

export function MissionPanel({
  device,
  waypoints,
  reached,
  onReachedChange,
  onMissionActiveChange,
}: {
  device: string;
  waypoints: Waypoint[];
  reached: Set<number>;
  onReachedChange: (reached: Set<number>) => void;
  onMissionActiveChange: (active: boolean) => void;
}) {
  const [jwtToken, setJwtToken] = useState("");
  const [jwtError, setJwtError] = useState<string | null>(null);

  useEffect(() => {
    generateJWT(device, "@transitive-robotics/ros-tool").then(({ jwtToken, jwtError }) => {
      setJwtToken(jwtToken);
      setJwtError(jwtError);
    });
  }, [device]);

  if (!jwtToken) return <div>{jwtError ?? "Loading..."}</div>;

  return (
    <CapabilityContextProvider jwt={jwtToken}>
      <MissionControls
        device={device}
        waypoints={waypoints}
        reached={reached}
        onReachedChange={onReachedChange}
        onMissionActiveChange={onMissionActiveChange}
      />
    </CapabilityContextProvider>
  );
}

function latestValue(messages: any, path: string): unknown {
  return path
    .split("/")
    .filter((key) => key !== "")
    .reduce((value: any, key) => value?.[key], messages);
}

function MissionControls({
  device,
  waypoints,
  reached,
  onReachedChange,
  onMissionActiveChange,
}: {
  device: string;
  waypoints: Waypoint[];
  reached: Set<number>;
  onReachedChange: (reached: Set<number>) => void;
  onMissionActiveChange: (active: boolean) => void;
}) {
  const { isReady, publish, callService, subscribe, unsubscribe, deviceData } =
    useContext(CapabilityContext);

  const [status, setStatus] = useState<"idle" | "running" | "paused">("idle");
  const [namespace, setNamespace] = useState(device);
  const [routeIds, setRouteIds] = useState<number[]>([]);

  const stopService = `/${namespace}/nav2_manager/stop`;
  const progressTopic = `/${namespace}/nav2_manager/reached_count`;

  useEffect(() => {
    onMissionActiveChange(status !== "idle");
  }, [status, onMissionActiveChange]);

  useEffect(() => {
    if (!isReady?.()) return;
    subscribe(2, progressTopic);
    return () => unsubscribe?.(2, progressTopic);
  }, [isReady, subscribe, unsubscribe, progressTopic]);

  const [, tick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => tick((t) => t + 1), 250);
    return () => clearInterval(interval);
  }, []);

  const reachedCount = latestValue(deviceData?.ros?.[2]?.messages, `${progressTopic}/data`);

  useEffect(() => {
    if (typeof reachedCount !== "number" || status === "idle") return;
    const done = routeIds.slice(0, reachedCount);
    if (done.length > 0) {
      onReachedChange(new Set([...reached, ...done]));
    }
  }, [reachedCount]);

  const sendRoute = (route: Waypoint[]) => {
    publish(2, GPS_WAYPOINTS_TOPIC, GEO_PATH_TYPE, toGeoPath(route));
    setRouteIds(route.map((w) => w.id));
  };

  const stopNav2 = () => {
    callService(2, stopService, TRIGGER_TYPE, {}, (err, suc) => {
      if (err) {
        console.warn("Failed to stop nav2", err);
      } else {
        console.debug("nav2 stop response", suc);
      }
    });
  };

  const onStart = () => {
    if (!isReady?.()) return;

    const allReached = pendingWaypoints(waypoints, reached).length === 0;
    if (allReached) {
      onReachedChange(new Set());
    }
    sendRoute(allReached ? waypoints : pendingWaypoints(waypoints, reached));

    setStatus("running");
  };

  const onStop = () => {
    if (!isReady?.()) return;

    stopNav2();
    onReachedChange(new Set());
    setStatus("idle");
  };

  const onPauseResume = () => {
    if (!isReady?.()) return;

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
        onChange={(event) => setNamespace(event.target.value)}
        placeholder="vehicle_namespace"
      />
      <div className="buttonRow">
        <button onClick={onStart} disabled={status !== "idle" || waypoints.length === 0}>
          Start
        </button>
        <button onClick={onStop} disabled={status === "idle"}>
          Stop
        </button>
        <button onClick={onPauseResume} disabled={status === "idle"}>
          {status === "paused" ? "Resume" : "Pause"}
        </button>
      </div>
    </div>
  );
}
