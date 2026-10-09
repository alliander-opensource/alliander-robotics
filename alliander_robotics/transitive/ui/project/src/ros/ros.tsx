import type { Subscription } from "../capabilities/RosTool";
import { Publishers } from "./ros_publishers";
import { Services } from "./ros_services";
import { Subscriptions } from "./ros_subscriptions";


export interface Ros {
    subscription_list: Subscription[];
    subscriptions: Subscriptions;
    publishers: Publishers;
    services: Services;
}

export function Ros(namespace: string) {

    const { subscriptions, subscription_list } = Subscriptions(namespace);
    const { publishers } = Publishers();
    const { services } = Services(namespace);


    const ros: Ros = {
        subscription_list: subscription_list,
        subscriptions: subscriptions,
        publishers: publishers,
        services: services
    };


    return { ros };
}