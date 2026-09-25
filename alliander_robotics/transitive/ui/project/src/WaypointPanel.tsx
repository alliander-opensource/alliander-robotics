// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useRef } from "react";
import type { Waypoint } from "./waypoints";

export function WaypointPanel({
  waypoints,
  onRemove,
  onReorder,
  onSave,
  onLoad,
  onClear,
}: {
  waypoints: Waypoint[];
  onRemove: (id: number) => void;
  onReorder: (id: number, direction: "up" | "down") => void;
  onSave: () => void;
  onLoad: (file: File) => void;
  onClear: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onLoad(file);
    }
    e.target.value = "";
  };

  const waypointList = (
    <ol>
      {waypoints.map((w, i) => (
        <li key={w.id}>
          {i + 1}: {w.lat.toFixed(5)}, {w.lng.toFixed(5)}
          <button onClick={() => onReorder(w.id, "up")} disabled={i === 0}>
            ↑
          </button>
          <button
            onClick={() => onReorder(w.id, "down")}
            disabled={i === waypoints.length - 1}
          >
            ↓
          </button>
          <button onClick={() => onRemove(w.id)}>✕</button>
        </li>
      ))}
    </ol>
  );

  return (
    <div>
      <div className="waypointActions">
        Waypoints
        <button onClick={onSave} disabled={waypoints.length === 0}>
          Save
        </button>
        <button onClick={() => fileInputRef.current?.click()}>Load</button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/json,.json"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <button onClick={onClear} disabled={waypoints.length === 0}>
          Clear
        </button>
      </div>
      {waypointList}
    </div>
  );
}
