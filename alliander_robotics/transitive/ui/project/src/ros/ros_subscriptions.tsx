// SPDX-FileCopyrightText: Alliander N. V.
//
// SPDX-License-Identifier: Apache-2.0

import { useState } from "react";

export interface Subscription {
  topic: string;
  fields: string[];
  callback: (data: any) => void;
}

export interface Subscriptions {
  time: number | null;
  battery: number | null;
  estop: boolean | null;
  position: [number, number] | null;
  reachedCount: number | null;
  plan: [number, number][] | null;
}

export function Subscriptions(namespace: string) {
  const [time, setTime] = useState<number | null>(null);
  const [battery, setBattery] = useState<number | null>(null);
  const [estop, setEstop] = useState<boolean | null>(null);
  const [position, setPosition] = useState<[number, number] | null>(null);
  const [reachedCount, setReachedCount] = useState<number | null>(null);
  const [plan, setPlan] = useState<[number, number][] | null>(null);

  const subscription_list: Subscription[] = [
    {
      topic: "/clock",
      fields: ["/clock/sec"],
      callback: (data: any) => {
        if (data && data.length >= 1) {
          setTime(data[0]);
        }
      },
    },
    {
      topic: `/${namespace}/battery/battery_status`,
      fields: ["/percentage"],
      callback: (data: any) => {
        if (data && data.length >= 1) {
          setBattery(data[0]);
        }
      },
    },
    {
      topic: `/${namespace}/hardware/e_stop`,
      fields: ["/data"],
      callback: (data: any) => {
        console.log("E-Stop data received:", data);
        if (data && data.length >= 1) {
          setEstop(data[0]);
        }
      },
    },
    {
      topic: "/ublox/gps/fix",
      fields: ["/latitude", "/longitude"],
      callback: (data: any) => {
        if (data && data.length >= 2) {
          setPosition([data[0], data[1]]);
        }
      },
    },
    {
      topic: `/${namespace}/nav2_manager/reached_count`,
      fields: ["/data"],
      callback: (data: any) => {
        if (data && data.length >= 1) {
          setReachedCount(data[0]);
        }
      },
    },
    {
      topic: `/${namespace}/plan_gps`,
      fields: ["/poses"],
      callback: (data: any) => {
        const plan: [number, number][] = [];
        if (data && data.length >= 1) {
          const GeoPath = data[0];
          for (const GeoPoseStamped of GeoPath) {
            const GeoPose = GeoPoseStamped.pose;
            const GeoPoint = GeoPose.position;
            plan.push([GeoPoint.latitude, GeoPoint.longitude]);
          }
        }
        setPlan(plan);
      },
    },
  ];

  const subscriptions: Subscriptions = {
    time,
    battery,
    estop,
    position,
    reachedCount,
    plan,
  };

  return { subscriptions, subscription_list };
}
