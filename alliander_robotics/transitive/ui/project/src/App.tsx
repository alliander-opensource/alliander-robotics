// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import "./App.css";
import { HealthMonitor } from "./capabilities/HealthMonitor";
import { RosProvider, RosTool } from "./capabilities/RosTool";
import { Teleoperation } from "./capabilities/Teleoperation";
import { MapComponent } from "./map/Map";
import type { Device } from "./missionHelpers";
import { Ros } from "./ros/ros";

const DEVICES: Device[] = ["simulation", "lynx", "panther", "none"];
const DEFAULT_DEVICE: Device = "simulation";
const DEVICE_STORAGE_KEY = "device";

function App() {
  const [device] = useState<Device>(
    (sessionStorage.getItem(DEVICE_STORAGE_KEY) as Device | null) ?? DEFAULT_DEVICE,
  );
  const namespace = device == "lynx" ? "lynx" : "panther";

  const handleDeviceChange = (value: Device) => {
    sessionStorage.setItem(DEVICE_STORAGE_KEY, value);
    window.location.reload();
  };

  const deviceSelector = (
    <div>
      {DEVICES.map((name) => (
        <label key={name}>
          <input type="radio" checked={device === name} onChange={() => handleDeviceChange(name)} />
          {name}
        </label>
      ))}
    </div>
  );

  // ROS:
  const { ros } = Ros(namespace);

  // Capabilities:
  const rosTool = <RosTool device={device} />;
  const teleoperation = <Teleoperation device={device} />;
  const healthMonitor = <HealthMonitor device={device} ros={ros} />;

  // UI Components:
  const map = <MapComponent ros={ros} />;

  return (
    <RosProvider device={device} ros={ros}>
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
        {map}
      </div>
    </RosProvider>
  );
}

export default App;
