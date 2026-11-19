import "leaflet/dist/leaflet.css";

import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, useMap } from "react-leaflet";

import type { RouteResult } from "../lib/api";

function FitRoute({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 1) map.fitBounds(points, { padding: [24, 24] });
  }, [map, points]);
  return null;
}

/** Visual map for sighted helpers. The steps list is the accessible version. */
export default function RouteMap({ from, route }: { from: { lat: number; lon: number }; route: RouteResult }) {
  const end: [number, number] = [route.destination.lat, route.destination.lon];
  const points = route.geometry.length > 1 ? route.geometry : [[from.lat, from.lon] as [number, number], end];

  return (
    <div aria-hidden className="h-96 overflow-hidden rounded-[32px] border-2 border-line lg:h-full lg:min-h-96">
      <MapContainer center={[from.lat, from.lon]} zoom={15} className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={points} pathOptions={{ color: "#16150F", weight: 8 }} />
        <Polyline positions={points} pathOptions={{ color: "#FFC800", weight: 4 }} />
        <CircleMarker center={[from.lat, from.lon]} radius={9} pathOptions={{ color: "#16150F", fillColor: "#0047FF", fillOpacity: 1 }} />
        <CircleMarker center={end} radius={9} pathOptions={{ color: "#16150F", fillColor: "#FFC800", fillOpacity: 1 }} />
        <FitRoute points={points} />
      </MapContainer>
    </div>
  );
}
