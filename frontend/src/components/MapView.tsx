import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import { Issue } from '../types';
import { SEVERITY_COLORS, CATEGORY_LABELS } from '../types';
import { Link } from 'react-router-dom';

// Custom colored circle marker
const makeIcon = (color: string) =>
  L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      width:18px;height:18px;border-radius:50%;
      background:${color};border:2px solid white;
      box-shadow:0 2px 6px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });

interface MapViewProps {
  points: Array<{
    id: number; lat: number; lon: number;
    severity: string; category: string; status: string;
  }>;
  center?: [number, number];
  zoom?: number;
  height?: string;
  onSelect?: (id: number) => void;
}

export default function MapView({
  points,
  center = [12.9716, 77.5946],   // Bengaluru default
  zoom = 12,
  height = '400px',
  onSelect,
}: MapViewProps) {
  return (
    <div style={{ height, borderRadius: '12px', overflow: 'hidden' }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        {points.map((p) => (
          <Marker
            key={p.id}
            position={[p.lat, p.lon]}
            icon={makeIcon(
              SEVERITY_COLORS[p.severity as keyof typeof SEVERITY_COLORS] ?? '#6b7280'
            )}
            eventHandlers={{ click: () => onSelect?.(p.id) }}
          >
            <Popup>
              <div className="text-sm min-w-40">
                <div className="font-semibold capitalize mb-1">{p.category.replace('_', ' ')}</div>
                <div className="text-gray-500 capitalize mb-2">
                  Severity: <span className="font-medium">{p.severity}</span>
                </div>
                <div className="text-gray-500 capitalize mb-2">
                  Status: <span className="font-medium">{p.status.replace('_', ' ')}</span>
                </div>
                <Link
                  to={`/issue/${p.id}`}
                  className="text-nexus-600 hover:underline text-xs font-medium"
                >
                  View Issue →
                </Link>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
