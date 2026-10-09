// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import { MissionPanel } from "./MissionPanel";

import { pendingWaypoints } from "../missionHelpers";
import type { Ros } from "../ros/ros";
import "./Map.css";
import { UseWaypoints } from "./useWaypoints";
import { WaypointMarker } from "./Waypoint";
import { WaypointPanel } from "./WaypointPanel";

const HOME: [number, number] = [52.06, 5.38];
const ZOOM: number = 7;
const MAX_ZOOM = 20;
const ROBOT_PANE = "robotPane";

function RobotPane() {
  const map = useMap();
  if (!map.getPane(ROBOT_PANE)) {
    const pane = map.createPane(ROBOT_PANE);
    pane.style.zIndex = "650";
  }
  return null;
}

function ClickToAdd({ onAdd }: { onAdd: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => onAdd(e.latlng.lat, e.latlng.lng),
  });
  return null;
}

function Controls({ position }: Readonly<{ position?: [number, number] | null }>) {
  const map = useMap();
  const controlsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (controlsRef.current) {
      L.DomEvent.disableClickPropagation(controlsRef.current);
    }
  }, []);

  function home() {
    map.setView(HOME, ZOOM);
  }

  function robot() {
    if (position) {
      map.setView(position, MAX_ZOOM);
    }
  }

  return (
    <div ref={controlsRef} className="leaflet-bottom leaflet-left leaflet-control controls">
      <button onClick={home}>
        <span className="button">🏠</span>
      </button>
      <button onClick={robot}>
        <span className="button">🤖</span>
      </button>
    </div>
  );
}

export function MapComponent({ ros }: Readonly<{ ros: Ros }>) {
  const wp = UseWaypoints();
  const route: [number, number][] = wp.waypoints.map((w) => [w.lat, w.lng]);

  const [missionActive, setMissionActive] = useState(false);
  const current = missionActive
    ? (pendingWaypoints(wp.waypoints, wp.reached)[0]?.id ?? null)
    : null;

  const missionPanel = <MissionPanel ros={ros} wp={wp} onMissionActiveChange={setMissionActive} />;
  const waypointPanel = <WaypointPanel wp={wp} />;

  const position = ros.subscriptions.position;
  const map = (
    <MapContainer center={position ?? HOME} zoom={ZOOM} maxZoom={MAX_ZOOM}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxNativeZoom={18}
        maxZoom={MAX_ZOOM}
      />
      <RobotPane />
      {route.length > 1 && <Polyline positions={route} />}
      {wp.waypoints.map((w, i) => (
        <WaypointMarker
          key={w.id}
          index={i}
          waypoint={w}
          reached={wp.reached.has(w.id)}
          current={w.id === current}
          onMove={wp.onMove}
          onRemove={wp.onRemove}
        />
      ))}
      {position && <CircleMarker center={position} radius={5} fillOpacity={1} pane={ROBOT_PANE} />}
      <ClickToAdd onAdd={wp.onAdd} />
      <Controls position={position} />
    </MapContainer>
  );

  return (
    <div className="mapRow">
      <div className="map">{map}</div>
      <div className="panelStack">
        <div className="mission">{missionPanel}</div>
        <div className="waypoints">{waypointPanel}</div>
      </div>
    </div>
  );
}
