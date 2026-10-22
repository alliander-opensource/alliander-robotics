// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

export interface Publisher {
  topic: string;
  type: string;
}

export interface Publishers {
  geopath: Publisher;
}

export function Publishers() {
  const publishers: Publishers = {
    geopath: {
      topic: "/gps_waypoints",
      type: "geographic_msgs/msg/GeoPath",
    },
  };

  return { publishers };
}
