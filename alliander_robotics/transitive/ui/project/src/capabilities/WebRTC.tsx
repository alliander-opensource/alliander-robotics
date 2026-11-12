// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { TransitiveCapability } from "@transitive-sdk/utils-web";
import { useCallback, useEffect, useState } from "react";
import "./capability.css";
import { generateJWT } from "./jwt";

export function WebRTC({
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
        <div className="camera_only">
          <TransitiveCapability
            key={`${device}`}
            jwt={token}
            ssl="true"
            count="1"
            disabledeviceverification="true"
            type="rostopic"
            rosversion="2"
            source={`/${camera}/color/image`}
            bitrate="5"
            framerate="5/1"
            hardware="nvidia"
          />
        </div>
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

  // Render the widget.
  return <div className="widget">{capability}</div>;
}
