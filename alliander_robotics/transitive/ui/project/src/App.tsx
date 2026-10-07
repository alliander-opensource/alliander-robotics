// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';
import './App.css';
import { HealthMonitor } from './capabilities/HealthMonitor';
import type { Subscription } from './capabilities/RosTool';
import { RosTool } from './capabilities/RosTool';
import { Teleoperation } from './capabilities/Teleoperation';
import { Map } from './Map';

type Device = 'simulation' | 'lynx' | 'panther' | 'none';
const DEVICE: Device = 'simulation';

function App() {
  const device_stored = sessionStorage.getItem(DEVICE) as Device | null;
  const [device] = useState<Device>(device_stored ?? DEVICE);
  const [position, setPosition] = useState<[number, number] | null>(null);
  const [plan, setPlan] = useState<[number, number][] | null>(null);
  const [time, setTime] = useState<number | null>(null);

  const handleDeviceChange = (value: Device) => {
    sessionStorage.setItem(DEVICE, value);
    window.location.reload();
  };

  const deviceSelector = <div>
    <label>
      <input
        type="radio"
        checked={device === 'simulation'}
        onChange={() => handleDeviceChange("simulation")} />
      simulation
    </label>
    <label>
      <input
        type="radio"
        checked={device === 'lynx'}
        onChange={() => handleDeviceChange("lynx")} />
      lynx
    </label>
    <label>
      <input
        type="radio"
        checked={device === 'panther'}
        onChange={() => handleDeviceChange("panther")} />
      panther
    </label>
    <label>
      <input
        type="radio"
        checked={device === 'none'}
        onChange={() => handleDeviceChange("none")} />
      none
    </label>
  </div>

  //Subscription on GPS topic: 
  const gps_callback = (data: any) => {
    if (data && data.length >= 2) {
      setPosition([data[0], data[1]]);
    }
  };
  const gps_subscription: Subscription = {
    topic: '/ublox/gps/fix',
    fields: ['/latitude', '/longitude'],
    callback: gps_callback,
  };

  // Subscription on plan_gps topic:
  const plan_callback = (data: any) => {
    let plan: [number, number][] = [];
    if (data && data.length >= 1) {
      const GeoPath = data[0];
      for (const GeoPoseStamped of GeoPath) {
        const GeoPose = GeoPoseStamped.pose;
        const GeoPoint = GeoPose.position;
        console.log(GeoPoint);
        plan.push([GeoPoint.latitude, GeoPoint.longitude]);
      }
    }
    setPlan(plan);
  };
  const plan_subscription: Subscription = {
    topic: '/panther/plan_gps',
    fields: ['/poses'],
    callback: plan_callback,
  };

  // Subscription on Clock topic:
  const clock_callback = (data: any) => {
    if (data && data.length >= 1) {
      setTime(data[0]);
    }
  };
  const clock_subscription: Subscription = {
    topic: '/clock',
    fields: ['/clock/sec'],
    callback: clock_callback,
  };

  // Define ROS tool
  const subscriptions: Subscription[] = [gps_subscription, clock_subscription, plan_subscription];
  const rosTool = <RosTool device={device} subscriptions={subscriptions} />;

  const teleoperation = <Teleoperation device={device} />;
  const healthMonitor = <HealthMonitor device={device} time={time} />;

  const map = <Map position={position} plan={plan} />;

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
        <div className="map">
          {map}
        </div>
      </div>
    </>
  );
}

export default App
