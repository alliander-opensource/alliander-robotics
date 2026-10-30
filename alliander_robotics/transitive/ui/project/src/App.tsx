// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { useState } from "react";
import "./App.css";
import { RosProvider } from "./capabilities/RosTool";
import { MapComponent } from "./map/Map";
import type { Device } from "./missionHelpers";
import { ControlPanel } from "./panels/ControlPanel";
import { DevicePanel } from "./panels/DevicePanel";
import { MissionPanel } from "./panels/MissionPanel";
import { StatusPanel } from "./panels/StatusPanel";
import { WaypointPanel } from "./panels/WaypointPanel";
import { WindowsPanel } from "./panels/WindowsPanel";
import { createRos } from "./ros/ros";
import { UseWaypoints } from "./waypoint/useWaypoints";

const DEFAULT_DEVICE: Device = "simulation";

function App() {
  const [device, setDevice] = useState<Device>(DEFAULT_DEVICE);
  const namespace = device === "lynx" ? "lynx" : "panther";
  const ros = createRos(namespace);
  const wp = UseWaypoints();

  // TODO: Can this be defined inside the MissionPanel? Difficult because the map also needs to know if the mission is active.
  const [missionActive, setMissionActive] = useState(false);

  // UI Components:
  const map = <MapComponent ros={ros} wp={wp} missionActive={missionActive} />;

  // Panels:
  const devicePanel = <DevicePanel device={device} setDevice={setDevice} />;
  const windowsPanel = <WindowsPanel device={device} ros={ros} />;
  const statusPanel = <StatusPanel ros={ros} />;
  const controlPanel = <ControlPanel ros={ros} />;
  const waypointPanel = <WaypointPanel wp={wp} />;
  const missionPanel = (
    <MissionPanel ros={ros} wp={wp} onMissionActiveChange={setMissionActive} />
  );

  // Sections:
  const mapSection = <div className="mapSection">{map}</div>;
  const rightSection = (
    <div className="rightSection">
      {devicePanel}
      {windowsPanel}
      {statusPanel}
      {controlPanel}
      {missionPanel}
      {waypointPanel}
    </div>
  );

  return (
    <RosProvider device={device} ros={ros}>
      <div className="app">
        {mapSection}
        {rightSection}
      </div>
    </RosProvider>
  );
}

export default App;
