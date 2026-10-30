// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import CloseIcon from "@mui/icons-material/Close";
import NorthIcon from "@mui/icons-material/North";
import SouthIcon from "@mui/icons-material/South";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import type { ChangeEvent } from "react";
import { useRef } from "react";
import ButtonGroup from "react-bootstrap/esm/ButtonGroup";
import Table from "react-bootstrap/esm/Table";
import type { UseWaypoints } from "../waypoint/useWaypoints";
import "./panels.css";

export function WaypointPanel({ wp }: Readonly<{ wp: UseWaypoints }>) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isEmpty = wp.waypoints.length === 0;

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      wp.onLoad(file);
    }
    e.target.value = "";
  };

  return (
    <div className="panelRow">
      <div>
        <div className="sectionTitle">Waypoints</div>
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            type="button"
            onClick={wp.onSave}
            disabled={isEmpty}
          >
            Save
          </Button>
          <Button
            variant="contained"
            type="button"
            onClick={() => fileInputRef.current?.click()}
          >
            Load
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            onChange={handleFileChange}
            hidden
          />
          <Button
            variant="contained"
            type="button"
            onClick={() => {
              if (
                window.confirm(`Clear all ${wp.waypoints.length} waypoint?`)
              ) {
                wp.onClear();
              }
            }}
            disabled={isEmpty}
          >
            Clear
          </Button>
        </Stack>
      </div>
      <Table>
        <TableBody sx={{ "& .MuiTableCell-root": { padding: "0px 2px" } }}>
          {wp.waypoints.map((w, i) => (
            <TableRow key={w.id}>
              <TableCell component="th" scope="row">
                {i + 1}
              </TableCell>
              <TableCell>
                {w.lat.toFixed(5)}, {w.lng.toFixed(5)}
              </TableCell>
              <TableCell>
                <ButtonGroup>
                  <IconButton
                    type="button"
                    onClick={() => wp.onReorder(w.id, "up")}
                    disabled={i === 0}
                  >
                    <NorthIcon />
                  </IconButton>
                  <IconButton
                    type="button"
                    onClick={() => wp.onReorder(w.id, "down")}
                    disabled={i === wp.waypoints.length - 1}
                  >
                    <SouthIcon />
                  </IconButton>
                  <IconButton type="button" onClick={() => wp.onRemove(w.id)}>
                    <CloseIcon />
                  </IconButton>
                </ButtonGroup>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
