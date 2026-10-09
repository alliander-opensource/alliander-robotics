// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import type { ChangeEvent } from "react";
import { useRef } from "react";
import "./panels.css";
import type { UseWaypoints } from "./useWaypoints";

export function WaypointPanel({ wp }: Readonly<{ wp: UseWaypoints }>) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isEmpty = wp.waypoints.length === 0;

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      wp.onLoad(file);
    }
    e.target.value = "";
  };

  return (
    <div>
      <div className="panelActions">
        <div className="sectionTitle">Waypoints</div>
        <div className="buttonRow">
          <button onClick={wp.onSave} disabled={isEmpty}>
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
          <button onClick={wp.onClear} disabled={isEmpty}>
            Clear
          </button>
        </div>
      </div>
      <ol>
        {wp.waypoints.map((w, i) => (
          <li
            key={w.id}
            className={
              [wp.reached.has(w.id) && "reached", w.id === wp.current && "current"]
                .filter(Boolean)
                .join(" ") || undefined
            }
          >
            {i + 1}: {w.lat.toFixed(5)}, {w.lng.toFixed(5)}
            <button onClick={() => wp.onReorder(w.id, "up")} disabled={i === 0}>
              ↑
            </button>
            <button
              onClick={() => wp.onReorder(w.id, "down")}
              disabled={i === wp.waypoints.length - 1}
            >
              ↓
            </button>
            <button onClick={() => wp.onRemove(w.id)}>✕</button>
          </li>
        ))}
      </ol>
    </div>
  );
}
