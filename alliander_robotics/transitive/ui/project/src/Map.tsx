// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import "./Map.css";
import type { Waypoint } from "./waypoints";

const HOME: [number, number] = [52.06, 5.38];
const ZOOM: number = 7;
const MAX_ZOOM = 20;

function waypointIcon(index: number) {
  return L.divIcon({
    className: "",
    html: `<div class="waypoint-marker">${index + 1}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function ClickToAdd({ onAdd }: { onAdd: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => onAdd(e.latlng.lat, e.latlng.lng),
  });
  return null;
}

function Controls({ position }: { position?: [number, number] | null }) {
  const map = useMap();

  function home() {
    map.setView(HOME, ZOOM);
  }

  function robot() {
    if (position) {
      map.setView(position, MAX_ZOOM);
    }
  }

  return (
    <div className="leaflet-bottom leaflet-left leaflet-control controls">
      <button onClick={home}>
        <span className="button">🏠</span>
      </button>
      <button onClick={robot}>
        <span className="button">🤖</span>
      </button>
    </div>
  );
}

export function Map({
  position,
  waypoints,
  onAdd,
  onRemove,
  onMove,
}: {
  position?: [number, number] | null;
  waypoints: Waypoint[];
  onAdd: (lat: number, lng: number) => void;
  onRemove: (id: number) => void;
  onMove: (id: number, lat: number, lng: number) => void;
}) {
  const route: [number, number][] = waypoints.map((w) => [w.lat, w.lng]);

  const map = (
    <MapContainer
      center={position ? position : HOME}
      zoom={ZOOM}
      maxZoom={MAX_ZOOM}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        maxNativeZoom={18}
        maxZoom={MAX_ZOOM}
      />
      {position && (
        <CircleMarker
          center={position}
          radius={5}
          fillOpacity={1}
        ></CircleMarker>
      )}
      {route.length > 1 && <Polyline positions={route} />}
      {waypoints.map((w, i) => (
        <Marker
          key={w.id}
          position={[w.lat, w.lng]}
          icon={waypointIcon(i)}
          draggable
          eventHandlers={{
            dragend: (e) => {
              const latlng = e.target.getLatLng();
              onMove(w.id, latlng.lat, latlng.lng);
            },
            contextmenu: () => onRemove(w.id),
          }}
        />
      ))}
      <ClickToAdd onAdd={onAdd} />
      <Controls position={position} />
    </MapContainer>
  );

  return map;
}
