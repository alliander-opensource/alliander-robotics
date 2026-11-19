// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { HealthMonitor } from "../capabilities/HealthMonitor";
import { RosTool } from "../capabilities/RosTool";
import { Teleoperation } from "../capabilities/Teleoperation";
import type { Ros } from "../ros/ros";
import { FloatingPanel } from "./floating_panel/FloatingPanel";
import "./panels.css";

export function WindowsPanel({
  device,
  ros,
}: Readonly<{ device: string; ros: Ros }>) {
  const rosTool = <RosTool device={device} />;
  const teleoperation = <Teleoperation device={device} />;
  const healthMonitor = <HealthMonitor device={device} ros={ros} />;

  return (
    <div className="panelRow">
      <div className="sectionTitle">Windows</div>
      <FloatingPanel
        label="Teleoperation"
        device={device}
        content={teleoperation}
      />
      <FloatingPanel
        label="Health Monitor"
        device={device}
        content={healthMonitor}
      />
      <FloatingPanel label="ROS Tool" device={device} content={rosTool} />
    </div>
  );
}
