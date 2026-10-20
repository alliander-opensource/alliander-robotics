// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import type { Subscription } from "./ros_subscriptions";
import { Publishers } from "./ros_publishers";
import { Services } from "./ros_services";
import { Subscriptions } from "./ros_subscriptions";

export interface Ros {
  subscription_list: Subscription[];
  subscriptions: Subscriptions;
  publishers: Publishers;
  services: Services;
}

export function createRos(namespace: string) {
  const { subscriptions, subscription_list } = Subscriptions(namespace);
  const { publishers } = Publishers();
  const { services } = Services(namespace);

  return { subscriptions, subscription_list, publishers, services };
}
