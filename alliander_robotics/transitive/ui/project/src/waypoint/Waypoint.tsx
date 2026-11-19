// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import L from "leaflet";
import { useCallback, useMemo, useRef, useState } from "react";
import { Marker } from "react-leaflet";
import type { Waypoint } from "./waypoints";

function waypointIcon(
  index: number,
  reached: boolean,
  current: boolean,
  selected: boolean,
  rotation: number | null,
) {
  const classes = [
    "waypoint-marker",
    reached && "reached",
    current && "current",
    selected && "selected",
  ]
    .filter(Boolean)
    .join(" ");

  const heading =
    rotation !== null
      ? `<div class="waypoint-marker heading" style="transform: rotate(${rotation}rad)"></div>`
      : "";

  return L.divIcon({
    className: "",
    html: `<div class="${classes}">${heading}${index + 1}</div>`,
    iconAnchor: [12, 12],
  });
}

export function WaypointMarker({
  index,
  waypoint,
  reached,
  current,
  onMove,
  onRemove,
  onRotate,
}: Readonly<{
  index: number;
  waypoint: Waypoint;
  reached: boolean;
  current: boolean;
  onMove: (id: number, lat: number, lng: number) => void;
  onRemove: (id: number) => void;
  onRotate: (id: number, rotation: number) => void;
}>) {
  const [selected, setSelected] = useState(false);
  const markerPosition = useRef<[number, number] | null>(null);
  const onRotateRef = useRef(onRotate);

  const icon = useMemo(
    () => waypointIcon(index, reached, current, selected, waypoint.rot),
    [index, reached, current, selected, waypoint.rot],
  );
  const position = useMemo<[number, number]>(
    () => [waypoint.lat, waypoint.lng],
    [waypoint.lat, waypoint.lng],
  );

  const handle_mouse_movement = useCallback(
    (event: MouseEvent) => {
      markerPosition.current ??= [event.clientX, event.clientY];
      const delta_x = event.clientX - markerPosition.current[0];
      const delta_y = event.clientY - markerPosition.current[1];
      const rot = Math.atan2(delta_x, -delta_y);
      onRotateRef.current(waypoint.id, rot);
    },
    [waypoint.id],
  );

  function start_mouse_tracking() {
    markerPosition.current = null;
    window.addEventListener("mousemove", handle_mouse_movement);
  }

  function stop_mouse_tracking() {
    window.removeEventListener("mousemove", handle_mouse_movement);
  }

  function control_heading() {
    setSelected(!selected);
    if (selected) {
      stop_mouse_tracking();
    } else {
      start_mouse_tracking();
    }
  }

  return (
    <Marker
      position={position}
      icon={icon}
      draggable
      eventHandlers={{
        dragend: (e) => {
          const latlng = e.target.getLatLng();
          onMove(waypoint.id, latlng.lat, latlng.lng);
        },
        click: () => control_heading(),
        contextmenu: () => onRemove(waypoint.id),
      }}
    />
  );
}
