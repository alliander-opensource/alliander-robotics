// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

import 'leaflet/dist/leaflet.css';
import { CircleMarker, MapContainer, Polyline, TileLayer, useMap } from 'react-leaflet';
import './Map.css';

const HOME: [number, number] = [52.06, 5.38];
const ZOOM: number = 7;
const MAX_ZOOM = 20;

export function Map({ position, plan }: { position?: [number, number] | null, plan?: [number, number][] | null }) {

    function Controls() {
        const map = useMap();

        function home() {
            map.setView(HOME, ZOOM);
        }

        function robot() {
            if (position) {
                map.setView(position, MAX_ZOOM);
            }
        }

        return (
            <div className="leaflet-bottom leaflet-left leaflet-control controls">
                <button onClick={home}><span className='button'>🏠</span></button>
                <button onClick={robot}><span className='button'>🤖</span></button>
            </div>
        )
    }

    const map = <MapContainer center={position ? position : HOME} zoom={ZOOM} maxZoom={MAX_ZOOM}>
        <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxNativeZoom={18}
            maxZoom={MAX_ZOOM}
        />
        {position && <CircleMarker center={position} radius={5} fillOpacity={1}></CircleMarker>}
        {plan && <Polyline positions={plan} color='rgb(25, 255, 0)' />}
        <Controls />
    </MapContainer>

    return (
        map
    );
}