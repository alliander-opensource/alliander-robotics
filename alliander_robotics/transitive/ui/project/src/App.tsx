// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import "./App.css";
import { HealthMonitor } from "./capabilities/HealthMonitor";
import type { Subscription } from "./capabilities/RosTool";
import { RosTool } from "./capabilities/RosTool";
import { Teleoperation } from "./capabilities/Teleoperation";
import { Map } from "./Map";
import { WaypointPanel } from "./WaypointPanel";
import type { Waypoint } from "./waypoints";
import {
  addWaypoint,
  removeWaypoint,
  moveWaypoint,
  reorderWaypoint,
  clearWaypoints,
} from "./waypoints";
import { downloadWaypoints, readWaypointsFile } from "./waypointIO";

type Device = "simulation" | "lynx" | "panther" | "none";
const DEVICE: Device = "simulation";

function App() {
  const device_stored = sessionStorage.getItem(DEVICE) as Device | null;
  const [device] = useState<Device>(device_stored ?? DEVICE);
  const [position, setPosition] = useState<[number, number] | null>(null);
  const [time, setTime] = useState<number | null>(null);
  const [waypoints, setWaypoints] = useState<Waypoint[]>([]);

  const handleDeviceChange = (value: Device) => {
    sessionStorage.setItem(DEVICE, value);
    window.location.reload();
  };

  const deviceSelector = (
    <div>
      <label>
        <input
          type="radio"
          checked={device === "simulation"}
          onChange={() => handleDeviceChange("simulation")}
        />
        simulation
      </label>
      <label>
        <input
          type="radio"
          checked={device === "lynx"}
          onChange={() => handleDeviceChange("lynx")}
        />
        lynx
      </label>
      <label>
        <input
          type="radio"
          checked={device === "panther"}
          onChange={() => handleDeviceChange("panther")}
        />
        panther
      </label>
      <label>
        <input
          type="radio"
          checked={device === "none"}
          onChange={() => handleDeviceChange("none")}
        />
        none
      </label>
    </div>
  );

  //Subscription on GPS topic:
  const gps_callback = (data: any) => {
    if (data && data.length >= 2) {
      setPosition([data[0], data[1]]);
    }
  };
  const gps_subscription: Subscription = {
    topic: "/ublox/gps/fix",
    fields: ["/latitude", "/longitude"],
    callback: gps_callback,
  };

  // Subscription on Clock topic:
  const clock_callback = (data: any) => {
    if (data && data.length >= 1) {
      setTime(data[0]);
    }
  };
  const clock_subscription: Subscription = {
    topic: "/clock",
    fields: ["/clock/sec"],
    callback: clock_callback,
  };

  // Waypoint functions
  const onAdd = (lat: number, lng: number) => {
    setWaypoints((wps) => addWaypoint(wps, lat, lng));
  };
  const onRemove = (id: number) => {
    setWaypoints((wps) => removeWaypoint(wps, id));
  };
  const onMove = (id: number, lat: number, lng: number) => {
    setWaypoints((wps) => moveWaypoint(wps, id, lat, lng));
  };
  const onReorder = (id: number, direction: "up" | "down") => {
    setWaypoints((wps) => reorderWaypoint(wps, id, direction));
  };
  const onSave = () => {
    downloadWaypoints(waypoints);
  };
  const onLoad = async (file: File) => {
    try {
      setWaypoints(await readWaypointsFile(file));
    } catch (err) {
      console.error("Failed to load waypoints:", err);
    }
  };
  const onClear = () => {
    setWaypoints((wps) => clearWaypoints(wps));
  };

  // Define ROS tool
  const subscriptions: Subscription[] = [gps_subscription, clock_subscription];
  const rosTool = <RosTool device={device} subscriptions={subscriptions} />;

  const teleoperation = <Teleoperation device={device} />;
  const healthMonitor = <HealthMonitor device={device} time={time} />;

  const waypointPanel = (
    <WaypointPanel
      waypoints={waypoints}
      onRemove={onRemove}
      onReorder={onReorder}
      onSave={onSave}
      onLoad={onLoad}
      onClear={onClear}
    />
  );

  const map = (
    <Map
      position={position}
      waypoints={waypoints}
      onAdd={onAdd}
      onRemove={onRemove}
      onMove={onMove}
    />
  );

  return (
    <>
      <div className="app">
        <div className="title">
          <h1>Alliander Robotics Dashboard</h1>
          {deviceSelector}
        </div>
        <div className="cards">
          {teleoperation}
          {healthMonitor}
          {rosTool}
        </div>
        <div className="mapRow">
          <div className="map">{map}</div>
          <div className="panel">{waypointPanel}</div>
        </div>
      </div>
    </>
  );
}

export default App;
