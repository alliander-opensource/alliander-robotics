import type { Publisher } from "../capabilities/RosTool";

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