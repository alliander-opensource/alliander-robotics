// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { WebRTC } from "../capabilities/WebRTC";
import type { Device } from "../missionHelpers";
import "./panels.css";

export const CameraPanel = ({
  device,
  camera,
}: {
  device: Device;
  camera: string;
}) => {
  const webRTC = <WebRTC device={device} camera={camera} />;

  return <div className="panelRow">{webRTC}</div>;
};
