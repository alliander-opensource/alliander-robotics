// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import { useEffect } from "react";
import type { Device } from "../missionHelpers";

export const DevicePanel = ({
  device,
  setDevice,
}: {
  device: Device;
  setDevice: (device: Device) => void;
}) => {
  const DEVICES: Device[] = ["simulation", "panther", "lynx"];
  const DEVICE_STORAGE_KEY = "device";

  useEffect(() => {
    setDevice(sessionStorage.getItem(DEVICE_STORAGE_KEY) as Device);
  }, [setDevice]);

  const handleDeviceChange = (value: Device) => {
    setDevice(value);
    sessionStorage.setItem(DEVICE_STORAGE_KEY, value);
    window.location.reload();
  };

  return (
    <div className="panelRow">
      <div className="sectionTitle">Device</div>
      <FormControl>
        <RadioGroup
          row
          value={device}
          onChange={(e) => handleDeviceChange(e.target.value as Device)}
        >
          {DEVICES.map((name) => (
            <FormControlLabel
              key={name}
              value={name}
              control={<Radio />}
              label={name.charAt(0).toUpperCase() + name.slice(1)}
            />
          ))}
        </RadioGroup>
      </FormControl>
    </div>
  );
};
