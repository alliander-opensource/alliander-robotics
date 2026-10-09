import L from "leaflet";
import { useMemo } from "react";
import { Marker } from "react-leaflet";
import type { Waypoint } from "./waypoints";

function waypointIcon(index: number, reached: boolean, current: boolean) {
    const classes = ["waypoint-marker", reached && "reached", current && "current"]
        .filter(Boolean)
        .join(" ");
    return L.divIcon({
        className: "",
        html: `<div class="${classes}">${index + 1}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
    });
}

export function WaypointMarker({
    index,
    waypoint,
    reached,
    current,
    onMove,
    onRemove,
}: Readonly<{
    index: number;
    waypoint: Waypoint;
    reached: boolean;
    current: boolean;
    onMove: (id: number, lat: number, lng: number) => void;
    onRemove: (id: number) => void;
}>) {
    const icon = useMemo(() => waypointIcon(index, reached, current), [index, reached, current]);
    const position = useMemo<[number, number]>(
        () => [waypoint.lat, waypoint.lng],
        [waypoint.lat, waypoint.lng],
    );

    return (
        <Marker
            position={position}
            icon={icon}
            draggable
            eventHandlers={{
                dragend: (e) => {
                    const latlng = e.target.getLatLng();
                    onMove(waypoint.id, latlng.lat, latlng.lng);
                },
                contextmenu: () => onRemove(waypoint.id),
            }}
        />
    );
}