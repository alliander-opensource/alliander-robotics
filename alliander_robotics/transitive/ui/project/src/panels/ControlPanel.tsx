// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import HomeIcon from "@mui/icons-material/Home";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import { useState } from "react";
import { useRos } from "../capabilities/RosTool";
import type { TriggerResponse } from "../missionHelpers";
import type { Ros } from "../ros/ros";
import "./panels.css";

export function ControlPanel({ ros }: Readonly<{ ros: Ros }>) {
  const { ready, callService } = useRos();

  const [pressed_estop, setPressed_estop] = useState(false);

  const estop_toggle = (ros: Ros) => {
    setPressed_estop(true);
    const service = ros.subscriptions.estop
      ? ros.services.estop_reset
      : ros.services.estop_trigger;
    callService<TriggerResponse>(service, {})
      .then(() => setPressed_estop(false))
      .catch(() => setPressed_estop(false));
  };

  return (
    <div className="panelRow">
      <div className="sectionTitle">Control</div>
      <Stack direction="row" spacing={1}>
        <Button
          variant="contained"
          color={ros.subscriptions.estop ? "success" : "error"}
          disabled={!ready || pressed_estop}
          onClick={() => estop_toggle(ros)}
        >
          {ros.subscriptions.estop ? <PlayArrowIcon /> : <StopIcon />}
        </Button>
        <Button variant="contained" onClick={() => {}} disabled={true}>
          <HomeIcon />
        </Button>
      </Stack>
    </div>
  );
}
