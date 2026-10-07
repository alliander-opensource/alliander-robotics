// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useRef } from "react";
import type { ChangeEvent } from "react";
import type { Waypoint } from "./waypoints";
import "./panels.css";

export function WaypointPanel({
  waypoints,
  reached,
  current,
  onRemove,
  onReorder,
  onSave,
  onLoad,
  onClear,
}: {
  waypoints: Waypoint[];
  reached: Set<number>;
  current: number | null;
  onRemove: (id: number) => void;
  onReorder: (id: number, direction: "up" | "down") => void;
  onSave: () => void;
  onLoad: (file: File) => void;
  onClear: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isEmpty = waypoints.length === 0;

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onLoad(file);
    }
    e.target.value = "";
  };

  return (
    <div>
      <div className="panelActions">
        <div className="sectionTitle">Waypoints</div>
        <div className="buttonRow">
          <button onClick={onSave} disabled={isEmpty}>
            Save
          </button>
          <button onClick={() => fileInputRef.current?.click()}>Load</button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            onChange={handleFileChange}
            hidden
          />
          <button onClick={onClear} disabled={isEmpty}>
            Clear
          </button>
        </div>
      </div>
      <ol>
        {waypoints.map((w, i) => (
          <li
            key={w.id}
            className={
              [reached.has(w.id) && "reached", w.id === current && "current"]
                .filter(Boolean)
                .join(" ") || undefined
            }
          >
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
    </div>
  );
}
