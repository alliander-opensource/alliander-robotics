import type { Service } from "../capabilities/RosTool";


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