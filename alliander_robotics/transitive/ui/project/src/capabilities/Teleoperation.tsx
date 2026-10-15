// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { TransitiveCapability } from '@transitive-sdk/utils-web';
import { useEffect, useState } from 'react';
import './card.css';
import { generateJWT } from './jwt';
import './Teleoperation.css';

export function Teleoperation({ device }: { device: string }) {
  const [jwtToken, setJwtToken] = useState('');
  const [jwtError, setJwtError] = useState<string | null>(null);
  const [cameraTopic, setCameraTopic] = useState('/zed/color/image');
  const [capability, setCapability] = useState(<div className="teleop-capability"></div>);

  // Generate JWT token on mount
  useEffect(() => {
    generateJWT(device, '@transitive-robotics/remote-teleop').then(({ jwtToken: token, jwtError: error }) => {
      setJwtToken(token);
      setJwtError(error);
    });
  }, [device]);

  // Update the capability when the camera topic or JWT token changes
  useEffect(() => {
    if (!jwtToken) {
      return;
    }

    const embed = <TransitiveCapability
      key={`${device}-${cameraTopic}`}
      jwt={jwtToken}
      ssl="true"
      count="1"
      quantizer="40"
      timeout="1800"
      type="rostopic"
      rosVersion="2"
      source={cameraTopic}
      disabledeviceverification="true"
      control_topic="/joy"
      control_type="sensor_msgs/Joy"
      alwayson="true"
      inverted="true"
    />;

    setCapability(<div className="capability">{embed}</div>);
  }, [cameraTopic, jwtToken]);

  // Input field to specify the camera topic
  const inputField = (
    <div>
      <input
        type="text"
        value={cameraTopic}
        onChange={(event) => {
          setCameraTopic(event.target.value);
        }}
        placeholder="/camera_topic"
      />
    </div>
  );

  // Combine the input field and capability into a single widget
  const widget = (
    <>
      {inputField}
      {capability}
    </>
  );

  // Render as a card with a title and the widget.
  return (
    <div className="card">
      <div className="header"><b>Teleoperation ({device})</b></div>
      <div className="widget">
        {jwtError ? <p>Error: {jwtError}</p> : widget}
      </div>
    </div>
  );
}