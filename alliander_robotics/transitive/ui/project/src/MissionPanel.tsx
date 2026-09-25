// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import type { Waypoint } from "./waypoints";

export function MissionPanel({
  device,
  waypoints,
  position,
}: {
  device: string;
  waypoints: Waypoint[];
  position: [number, number] | null;
}) {
  const [status, setStatus] = useState<"idle" | "running" | "paused">("idle");
  const [remaining, setRemaining] = useState<Waypoint[]>([]);

  return (
    <div>
      <div className="missionActions">
        Mission
        <button
          onClick={() => setStatus("running")}
          disabled={status === "running"}
        >
          Start
        </button>
        <button onClick={() => setStatus("idle")} disabled={status === "idle"}>
          Stop
        </button>
        <button
          onClick={() =>
            setStatus((s) => (s === "running" ? "paused" : "running"))
          }
          disabled={status === "idle"}
        >
          {status === "paused" ? "Resume" : "Pause"}
        </button>
      </div>
    </div>
  );
}
