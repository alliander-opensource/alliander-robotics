// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <string>

/// Struct that links joystick buttons to topics.
struct Button {
  /// Joystick button key.
  int key;
  /// Topic to publish on.
  std::string topic;
  /// Service to publish on.
  std::string service;
  /// Joystick button state.
  int state = -1;
};
