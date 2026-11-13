// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

export interface Service {
  name: string;
  type: string;
}

export interface Services {
  estop_trigger: Service;
  estop_reset: Service;
  nav2_stop: Service;
}

export function Services(namespace: string) {
  const services: Services = {
    estop_trigger: {
      name: `/${namespace}/hardware/e_stop_trigger`,
      type: "std_srvs/srv/Trigger",
    },
    estop_reset: {
      name: `/${namespace}/hardware/e_stop_reset`,
      type: "std_srvs/srv/Trigger",
    },
    nav2_stop: {
      name: `/${namespace}/nav2_manager/stop`,
      type: "std_srvs/srv/Trigger",
    },
  };

  return { services };
}
