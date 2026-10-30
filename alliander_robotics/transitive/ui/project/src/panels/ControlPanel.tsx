// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import type { Ros } from "../ros/ros";
import "./panels.css";

export function ControlPanel({ ros }: Readonly<{ ros: Ros }>) {
  return (
    <div className="panelRow">
      <div className="sectionTitle">Control</div>
      <Stack direction="row" spacing={1}>
        <Button variant="contained" onClick={() => {}} disabled={true}>
          Go Home
        </Button>
        <Button variant="contained" onClick={() => {}} disabled={true}>
          E-Stop
        </Button>
      </Stack>
    </div>
  );
}
