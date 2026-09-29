// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useContext, useEffect, useState } from "react";
import type { Waypoint } from "./waypoints";
import { generateJWT } from "./capabilities/jwt";
import {
  CapabilityContext,
  CapabilityContextProvider,
} from "@transitive-sdk/utils-web";
import { remainingWaypoints, toGeoPath } from "./missionHelpers";

export function MissionPanel({
  device,
  waypoints,
  position,
  onWaypointsChange,
}: {
  device: string;
  waypoints: Waypoint[];
  position: [number, number] | null;
  onWaypointsChange: (waypoints: Waypoint[]) => void;
}) {
  const [jwtToken, setJwtToken] = useState("");
  const [jwtError, setJwtError] = useState<string | null>(null);

  useEffect(() => {
    generateJWT(device, "@transitive-robotics/ros-tool").then(
      ({ jwtToken, jwtError }) => {
        setJwtToken(jwtToken);
        setJwtError(jwtError);
      },
    );
  }, [device]);

  if (!jwtToken) return <div>{jwtError ?? "Loading..."}</div>;

  return (
    <CapabilityContextProvider jwt={jwtToken}>
      <MissionControls
        device={device}
        waypoints={waypoints}
        position={position}
        onWaypointsChange={onWaypointsChange}
      />
    </CapabilityContextProvider>
  );
}

export function MissionControls({
  device,
  waypoints,
  position,
  onWaypointsChange,
}: {
  device: string;
  waypoints: Waypoint[];
  position: [number, number] | null;
  onWaypointsChange: (waypoints: Waypoint[]) => void;
}) {
  const { isReady, publish, callService } = useContext(CapabilityContext);

  const [status, setStatus] = useState<"idle" | "running" | "paused">("idle");
  const [remaining, setRemaining] = useState<Waypoint[]>([]);

  const onStart = () => {
    setStatus("idle");

    if (!isReady?.()) return;

    publish(
      2,
      "/gps_waypoints",
      "geographic_msgs/msg/GeoPath",
      toGeoPath(waypoints),
    );

    setStatus("running");
    setRemaining(waypoints);
    console.log("Started mission.");
  };

  const onStop = () => {
    if (!isReady?.()) return;

    callService(
      2,
      "/panther/nav2_manager/stop",
      "std_srvs/srv/Trigger",
      {},
      (err, _) => {
        if (err) {
          console.warn("Failed to stop mission", err);
        }
      },
    );

    setStatus("idle");
    setRemaining([]);
  };

  const onPauseResume = () => {
    if (status === "running") {
      callService(
        2,
        "/panther/nav2_manager/stop",
        "std_srvs/srv/Trigger",
        {},
        (err, _) => {
          if (err) {
            console.warn("Failed to pause mission", err);
          }
        },
      );
      const stillToVisit = remainingWaypoints(waypoints, position);
      setStatus("paused");
      setRemaining(stillToVisit);
      onWaypointsChange(stillToVisit);
    } else {
      publish(
        2,
        "/gps_waypoints",
        "geographic_msgs/msg/GeoPath",
        toGeoPath(remaining),
      );
      setStatus("running");
    }
  };

  return (
    <div>
      <div className="missionActions">
        Mission
        <button
          onClick={() => onStart()}
          disabled={
            status === "running" || status == "paused" || waypoints.length === 0
          }
        >
          Start
        </button>
        <button onClick={() => onStop()} disabled={status === "idle"}>
          Stop
        </button>
        <button onClick={() => onPauseResume()} disabled={status === "idle"}>
          {status === "paused" ? "Resume" : "Pause"}
        </button>
      </div>
    </div>
  );
}
