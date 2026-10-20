// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

export interface Service {
  name: string;
  type: string;
}

export interface Services {
  nav2_stop: Service;
}

export function Services(namespace: string) {
  const services: Services = {
    nav2_stop: {
      name: `/${namespace}/nav2_manager/stop`,
      type: "std_srvs/srv/Trigger",
    },
  };

  return { services };
}
