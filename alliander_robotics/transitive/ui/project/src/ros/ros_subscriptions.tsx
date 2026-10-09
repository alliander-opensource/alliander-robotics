import { useState } from "react";
import type { Subscription } from "../capabilities/RosTool";

export interface Subscriptions {
    time: number | null;
    position: [number, number] | null;
    reachedCount: number | null;
}

export function Subscriptions(namespace: string) {
    const [position, setPosition] = useState<[number, number] | null>(null);
    const [time, setTime] = useState<number | null>(null);
    const [reachedCount, setReachedCount] = useState<number | null>(null);

    const subscription_list: Subscription[] = [
        {
            topic: "/clock",
            fields: ["/clock/sec"],
            callback: (data: any) => {
                if (data && data.length >= 1) {
                    setTime(data[0]);
                }
            }
        },
        {
            topic: "/ublox/gps/fix",
            fields: ["/latitude", "/longitude"],
            callback: (data: any) => {
                if (data && data.length >= 2) {
                    setPosition([data[0], data[1]]);
                }
            }
        },
        {
            topic: `/${namespace}/nav2_manager/reached_count`,
            fields: ["/data"],
            callback: (data: any) => {
                if (data && data.length >= 1) {
                    setReachedCount(data[0]);
                }
            },
        }
    ];

    const subscriptions: Subscriptions = { time, position, reachedCount };

    return { subscriptions, subscription_list };
}