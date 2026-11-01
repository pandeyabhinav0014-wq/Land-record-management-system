import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Layers, Eye, MapPin, Info, CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

// Custom Map center controller
function ChangeView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

// Custom Leaflet DivIcon for pins
const createCustomIcon = (color) => {
  return L.divIcon({
    className: 'custom-pin',
    html: `<div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.4);"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

export default function GisMapPage({ candidatePairs, onNavigateToConflict }) {
  const [selectedLayer, setSelectedLayer] = useState('ALL');
  const [highlightDecision, setHighlightDecision] = useState('ALL');
  const [selectedPair, setSelectedPair] = useState(null);

  const defaultCenter = [28.6250, 77.2150]; // Delhi / Shamli Cadastre region

  // Extract all spatial features from candidate pairs
  const spatialFeatures = [];
  candidatePairs.forEach(p => {
    const isHigh = p.match_decision === 'HIGH_CONFIDENCE';
    const isMed = p.match_decision === 'MEDIUM_CONFIDENCE';
    const color = isHigh ? '#10b981' : isMed ? '#f59e0b' : '#ef4444';

    // Record A geometry / point
    if (p.record_a?.parcel_geometry && p.record_a.parcel_geometry.type === 'Polygon') {
      const coords = p.record_a.parcel_geometry.coordinates[0].map(pt => [pt[1], pt[0]]);
      spatialFeatures.push({
        id: `${p.pair_id}_a_poly`,
        type: 'polygon',
        coords,
        color,
        source: p.source_a_name,
        recordId: p.source_record_id_a,
        surveyNo: p.record_a.parcel_or_survey_number,
        owner: p.record_a.owner_name,
        area: p.record_a.land_area,
        pair: p
      });
    } else if (p.record_a?.latitude && p.record_a?.longitude) {
      spatialFeatures.push({
        id: `${p.pair_id}_a_pt`,
        type: 'point',
        coords: [p.record_a.latitude, p.record_a.longitude],
        color,
        source: p.source_a_name,
        recordId: p.source_record_id_a,
        surveyNo: p.record_a.parcel_or_survey_number,
        owner: p.record_a.owner_name,
        area: p.record_a.land_area,
        pair: p
      });
    }

    // Record B geometry / point
    if (p.record_b?.parcel_geometry && p.record_b.parcel_geometry.type === 'Polygon') {
      const coords = p.record_b.parcel_geometry.coordinates[0].map(pt => [pt[1], pt[0]]);
      spatialFeatures.push({
        id: `${p.pair_id}_b_poly`,
        type: 'polygon',
        coords,
        color,
        source: p.source_b_name,
        recordId: p.source_record_id_b,
        surveyNo: p.record_b.parcel_or_survey_number,
        owner: p.record_b.owner_name,
        area: p.record_b.land_area,
        pair: p
      });
    } else if (p.record_b?.latitude && p.record_b?.longitude) {
      spatialFeatures.push({
        id: `${p.pair_id}_b_pt`,
        type: 'point',
        coords: [p.record_b.latitude, p.record_b.longitude],
        color,
        source: p.source_b_name,
        recordId: p.source_record_id_b,
        surveyNo: p.record_b.parcel_or_survey_number,
        owner: p.record_b.owner_name,
        area: p.record_b.land_area,
        pair: p
      });
    }
  });

  const filteredFeatures = spatialFeatures.filter(f => {
    if (selectedLayer !== 'ALL' && f.source !== selectedLayer) return false;
    if (highlightDecision !== 'ALL' && f.pair.match_decision !== highlightDecision) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Top Header & Layer Toggles */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900">GIS Cadastral Map & Spatial Overlay</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Visualize parcel centroids, polygon boundaries, and topological overlap across departments.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Decision highlight filter */}
          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg">
            <span className="text-slate-500 px-2 font-medium">Status:</span>
            {['ALL', 'HIGH_CONFIDENCE', 'MEDIUM_CONFIDENCE', 'LOW_CONFIDENCE'].map(d => (
              <button
                key={d}
                onClick={() => setHighlightDecision(d)}
                className={`px-2.5 py-1 rounded font-medium transition-colors ${
                  highlightDecision === d ? 'bg-white shadow-xs text-slate-900 font-bold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {d === 'ALL' ? 'All' : d === 'HIGH_CONFIDENCE' ? 'Matched' : d === 'MEDIUM_CONFIDENCE' ? 'Review' : 'Rejected'}
              </button>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center space-x-3 text-[11px] font-medium bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span>Matched (≥ 80%)</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
              <span>Review (55-79%)</span>
            </span>
            <span className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
              <span>Conflict / Low (&lt;55%)</span>
            </span>
          </div>
        </div>
      </div>

      {/* Map Canvas and Side Feature Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[650px]">
        {/* Leaflet Map */}
        <div className="lg:col-span-3 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden relative">
          <MapContainer
            center={defaultCenter}
            zoom={13}
            scrollWheelZoom={true}
            style={{ width: '100%', height: '100%' }}
          >
            <ChangeView center={defaultCenter} zoom={13} />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {filteredFeatures.map(f => {
              if (f.type === 'polygon') {
                return (
                  <Polygon
                    key={f.id}
                    positions={f.coords}
                    pathOptions={{
                      color: f.color,
                      fillColor: f.color,
                      fillOpacity: 0.35,
                      weight: 2
                    }}
                    eventHandlers={{
                      click: () => setSelectedPair(f.pair)
                    }}
                  >
                    <Popup>
                      <div className="text-xs space-y-1">
                        <div className="font-bold text-slate-800">{f.source}</div>
                        <div>Survey: <span className="font-mono font-semibold">{f.surveyNo}</span></div>
                        <div>ID: <span className="font-mono text-slate-500">{f.recordId}</span></div>
                        <div>Area: {f.area ? `${f.area} m²` : 'N/A'}</div>
                        <div className="text-emerald-700 font-medium pt-1">
                          Match Score: {(f.pair.final_confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </Popup>
                  </Polygon>
                );
              } else if (f.type === 'point') {
                return (
                  <Marker
                    key={f.id}
                    position={f.coords}
                    icon={createCustomIcon(f.color)}
                    eventHandlers={{
                      click: () => setSelectedPair(f.pair)
                    }}
                  >
                    <Popup>
                      <div className="text-xs space-y-1">
                        <div className="font-bold text-slate-800">{f.source}</div>
                        <div>Survey: <span className="font-mono font-semibold">{f.surveyNo}</span></div>
                        <div>Owner: {f.owner || '<Missing>'}</div>
                        <div>Coords: {f.coords[0].toFixed(4)}, {f.coords[1].toFixed(4)}</div>
                        <div className="text-emerald-700 font-medium pt-1">
                          Match Score: {(f.pair.final_confidence * 100).toFixed(1)}%
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                );
              }
              return null;
            })}
          </MapContainer>
        </div>

        {/* Feature Detail Sidebar */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm overflow-y-auto space-y-4">
          <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
            Selected Parcel Spatial Inspection
          </h2>

          {selectedPair ? (
            <div className="space-y-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="font-mono font-bold text-emerald-800">{selectedPair.pair_id}</span>
                  <span className={`px-2 py-0.5 rounded font-bold ${
                    selectedPair.match_decision === 'HIGH_CONFIDENCE'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {(selectedPair.final_confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="text-slate-600 font-medium">
                  {selectedPair.source_a_name} ↔ {selectedPair.source_b_name}
                </div>
              </div>

              {/* Spatial metrics */}
              <div className="space-y-2">
                <div className="font-semibold text-slate-800">Spatial Metrics:</div>
                <div className="p-2.5 rounded bg-slate-50 space-y-1 text-slate-700">
                  <div>Distance: <span className="font-mono font-medium">{selectedPair.raw_metrics?.distance_meters ? `${selectedPair.raw_metrics.distance_meters}m` : '0m / Contained'}</span></div>
                  <div>Polygon IoU: <span className="font-mono font-medium">{selectedPair.raw_metrics?.polygon_iou !== undefined ? `${(selectedPair.raw_metrics.polygon_iou * 100).toFixed(1)}%` : 'Points only'}</span></div>
                  <div>Containment: <span className="font-mono font-medium">{selectedPair.raw_metrics?.containment_ratio !== undefined ? `${(selectedPair.raw_metrics.containment_ratio * 100).toFixed(1)}%` : 'N/A'}</span></div>
                </div>
              </div>

              {/* Explanation narrative */}
              <div className="space-y-1">
                <div className="font-semibold text-slate-800">Reconciliation Evidence:</div>
                <p className="text-slate-600 italic bg-emerald-50/50 p-2.5 rounded border border-emerald-100 leading-relaxed">
                  "{selectedPair.explanation?.summary}"
                </p>
              </div>

              <button
                onClick={() => onNavigateToConflict(selectedPair.pair_id)}
                className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-xs transition-colors"
              >
                Resolve in Conflict Desk
              </button>
            </div>
          ) : (
            <div className="text-center py-20 text-slate-400 text-xs">
              <MapPin className="w-8 h-8 mx-auto text-slate-300 mb-2" />
              <span>Click on any parcel boundary polygon or pin on the GIS map to inspect spatial attributes and discrepancies.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

