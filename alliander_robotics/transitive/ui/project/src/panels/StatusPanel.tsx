// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import Table from "react-bootstrap/esm/Table";
import type { Ros } from "../ros/ros";
import "./panels.css";

export function StatusPanel({ ros }: Readonly<{ ros: Ros }>) {
  return (
    <div className="panelRow">
      <div className="sectionTitle">Status</div>
      <Table>
        <TableBody sx={{ "& .MuiTableCell-root": { py: 0.25 } }}>
          <TableRow>
            <TableCell>Time:</TableCell>
            <TableCell>{ros.subscriptions.time}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Battery:</TableCell>
            <TableCell>{ros.subscriptions.battery?.toFixed(2)}</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>E-Stop:</TableCell>
            <TableCell>TODO</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
}
