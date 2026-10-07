// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";

import { MissionPanel } from "./MissionPanel";
import { WaypointPanel } from "./WaypointPanel";
import "./Map.css";
import { useWaypoints } from "./useWaypoints";
import type { Waypoint } from "./waypoints";
import type { Device } from "./missionHelpers";
import { pendingWaypoints } from "./missionHelpers";

const HOME: [number, number] = [52.06, 5.38];
const ZOOM: number = 7;
const MAX_ZOOM = 20;
const ROBOT_PANE = "robotPane";

function waypointIcon(index: number, reached: boolean, current: boolean) {
  const classes = ["waypoint-marker", reached && "reached", current && "current"]
    .filter(Boolean)
    .join(" ");
  return L.divIcon({
    className: "",
    html: `<div class="${classes}">${index + 1}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function RobotPane() {
  const map = useMap();
  if (!map.getPane(ROBOT_PANE)) {
    const pane = map.createPane(ROBOT_PANE);
    pane.style.zIndex = "650";
  }
  return null;
}

function WaypointMarker({
  index,
  waypoint,
  reached,
  current,
  onMove,
  onRemove,
}: {
  index: number;
  waypoint: Waypoint;
  reached: boolean;
  current: boolean;
  onMove: (id: number, lat: number, lng: number) => void;
  onRemove: (id: number) => void;
}) {
  const icon = useMemo(() => waypointIcon(index, reached, current), [index, reached, current]);
  const position = useMemo<[number, number]>(
    () => [waypoint.lat, waypoint.lng],
    [waypoint.lat, waypoint.lng],
  );

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
        contextmenu: () => onRemove(waypoint.id),
      }}
    />
  );
}

function ClickToAdd({ onAdd }: { onAdd: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => onAdd(e.latlng.lat, e.latlng.lng),
  });
  return null;
}

function Controls({ position }: { position?: [number, number] | null }) {
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

export function MapComponent({
  position,
  device,
}: {
  position?: [number, number] | null;
  device: Device;
}) {
  const {
    waypoints,
    reached,
    onReachedChange,
    onAdd,
    onRemove,
    onMove,
    onReorder,
    onSave,
    onLoad,
    onClear,
  } = useWaypoints();
  const route: [number, number][] = waypoints.map((w) => [w.lat, w.lng]);

  const [missionActive, setMissionActive] = useState(false);
  const current = missionActive ? (pendingWaypoints(waypoints, reached)[0]?.id ?? null) : null;

  const missionPanel = (
    <MissionPanel
      device={device}
      waypoints={waypoints}
      reached={reached}
      onReachedChange={onReachedChange}
      onMissionActiveChange={setMissionActive}
    />
  );

  const waypointPanel = (
    <WaypointPanel
      waypoints={waypoints}
      reached={reached}
      current={current}
      onRemove={onRemove}
      onReorder={onReorder}
      onSave={onSave}
      onLoad={onLoad}
      onClear={onClear}
    />
  );

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
      {waypoints.map((w, i) => (
        <WaypointMarker
          key={w.id}
          index={i}
          waypoint={w}
          reached={reached.has(w.id)}
          current={w.id === current}
          onMove={onMove}
          onRemove={onRemove}
        />
      ))}
      {position && <CircleMarker center={position} radius={5} fillOpacity={1} pane={ROBOT_PANE} />}
      <ClickToAdd onAdd={onAdd} />
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
