// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { TransitiveCapability } from "@transitive-sdk/utils-web";
import { useCallback, useEffect, useState } from "react";
import "./capability.css";
import { generateJWT } from "./jwt";
import "./Teleoperation.css";

export function Teleoperation({
  device,
  camera,
}: Readonly<{ device: string; camera: string }>) {
  const [capability, setCapability] = useState(<div></div>);

  // Load the WebRTC capability with the given JWT token.
  const load_capability = useCallback(
    (token: string) => {
      if (camera === "none") {
        setCapability(<div className="capability">No camera selected</div>);
        return;
      }
      const embed = (
        <TransitiveCapability
          key={`${device}`}
          jwt={token}
          ssl="true"
          count="1"
          disabledeviceverification="true"
          type="rostopic"
          rosversion="2"
          source={`/${camera}/color/image`}
          hardware="nvidia"
          control_topic="/joy"
          control_type="sensor_msgs/Joy"
          alwayson="true"
          inverted="true"
        />
      );
      setCapability(<div className="capability">{embed}</div>);
    },
    [device, camera],
  );

  // Generate JWT token on mount
  useEffect(() => {
    generateJWT(device, "@transitive-robotics/remote-teleop").then(
      ({ jwtToken: token }) => {
        load_capability(token);
      },
      (error) => {
        setCapability(<div className="capability">Error: {error}</div>);
      },
    );
  }, [device, load_capability]);

  // Render as a card with a title and the widget.
  return <div className="widget">{capability}</div>;
}
