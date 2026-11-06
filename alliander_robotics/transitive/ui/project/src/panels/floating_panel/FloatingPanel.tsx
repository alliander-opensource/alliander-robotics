// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import CloseIcon from "@mui/icons-material/Close";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import { useState } from "react";
import "./FloatingPanel.css";

export const FloatingPanel = ({
  label,
  device,
  content,
}: {
  label: string;
  device: string;
  content: React.ReactNode;
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <Button onClick={() => setIsOpen(true)}>{label}</Button>
      {isOpen && (
        <div className="Panel">
          <div className="Header">
            {label} ({device})
          </div>
          <div className="closeButton">
            <IconButton onClick={() => setIsOpen(false)}>
              <CloseIcon />
            </IconButton>
          </div>
          <div className="Content">{content}</div>
        </div>
      )}
    </div>
  );
};
