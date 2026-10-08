// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import "./App.css";
import { HealthMonitor } from "./capabilities/HealthMonitor";
import type { Publisher, Service, Subscription } from "./capabilities/RosTool";
import { RosProvider, RosTool } from "./capabilities/RosTool";
import { Teleoperation } from "./capabilities/Teleoperation";
import { MapComponent } from "./Map";
import type { Device } from "./missionHelpers";
import type { MissionProps } from "./MissionPanel";

const DEVICES: Device[] = ["simulation", "lynx", "panther", "none"];
const DEFAULT_DEVICE: Device = "simulation";
const DEVICE_STORAGE_KEY = "device";

function App() {
  const [device] = useState<Device>(
    (sessionStorage.getItem(DEVICE_STORAGE_KEY) as Device | null) ?? DEFAULT_DEVICE,
  );
  const [position, setPosition] = useState<[number, number] | null>(null);
  const [time, setTime] = useState<number | null>(null);
  const [namespace, setNamespace] = useState<string>(device);
  const [reachedCount, setReachedCount] = useState<number | null>(null);

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

  // Subscription on GPS topic:
  const gpsCallback = (data: any) => {
    if (data && data.length >= 2) {
      setPosition([data[0], data[1]]);
    }
  };
  const gpsSubscription: Subscription = {
    topic: "/ublox/gps/fix",
    fields: ["/latitude", "/longitude"],
    callback: gpsCallback,
  };

  // Subscription on Clock topic:
  const clockCallback = (data: any) => {
    if (data && data.length >= 1) {
      setTime(data[0]);
    }
  };
  const clockSubscription: Subscription = {
    topic: "/clock",
    fields: ["/clock/sec"],
    callback: clockCallback,
  };

  // Subscription on nav2 manager progress topic:
  const reachedCountCallback = (data: any) => {
    if (data && data.length >= 1) {
      setReachedCount(data[0]);
    }
  };
  const reachedCountSubscription: Subscription = {
    topic: `/${namespace}/nav2_manager/reached_count`,
    fields: ["/data"],
    callback: reachedCountCallback,
  };

  // Publisher on GPS waypoints topic:
  const waypointsPublisher: Publisher = {
    topic: "/gps_waypoints",
    type: "geographic_msgs/msg/GeoPath",
  };

  // Service to stop the nav2 manager:
  const stopService: Service = {
    name: `/${namespace}/nav2_manager/stop`,
    type: "std_srvs/srv/Trigger",
  };

  const subscriptions: Subscription[] = [
    gpsSubscription,
    clockSubscription,
    reachedCountSubscription,
  ];
  const missionProps: MissionProps = {
    namespace,
    onNamespaceChange: setNamespace,
    waypointsPublisher,
    stopService,
    reachedCount,
  };

  const rosTool = <RosTool device={device} />;
  const teleoperation = <Teleoperation device={device} />;
  const healthMonitor = <HealthMonitor device={device} time={time} />;

  const map = <MapComponent position={position} missionProps={missionProps} />;

  return (
    <RosProvider device={device} subscriptions={subscriptions}>
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
