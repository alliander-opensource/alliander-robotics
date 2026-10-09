// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import { TransitiveCapability } from '@transitive-sdk/utils-web';
import { useEffect, useState } from 'react';
import type { Ros } from '../ros/ros';
import './card.css';
import './HealthMonitor.css';
import { generateJWT } from './jwt';


export function HealthMonitor({ device, ros }: Readonly<{ device: string, ros: Ros }>) {
  const [jwtToken, setJwtToken] = useState('');
  const [jwtError, setJwtError] = useState<string | null>(null);
  const [capability, setCapability] = useState(<div className="health-capability"></div>);

  // Generate JWT token on mount
  useEffect(() => {
    generateJWT(device, '@transitive-robotics/health-monitoring').then(({ jwtToken: token, jwtError: error }) => {
      setJwtToken(token);
      setJwtError(error);
    });
  }, [device]);

  // Update the capability when the JWT token changes
  useEffect(() => {
    if (!jwtToken) {
      return;
    }

    const embed = <TransitiveCapability
      key={`${device}`}
      jwt={jwtToken}
      ssl="true"
    />;

    setCapability(<div className="capability">{embed}</div>);
  }, [jwtToken]);


  // Create a widget
  const widget = (
    <>
      {capability}
    </>
  );

  // Render as a card with a title and the widget.
  return (
    <div className="card">
      <div className="header"><b>Health Monitor ({device})</b></div>
      <div className="widget">
        Time: {ros.subscriptions.time}
        {jwtError ? <p>Error: {jwtError}</p> : widget}
      </div>
    </div>
  );
}