import React, { useState } from 'react';
import { 
  Upload, 
  FileText, 
  AlertCircle, 
  CheckCircle, 
  Download, 
  Settings2, 
  RefreshCw,
  Info
} from 'lucide-react';
import { api } from '../services/api';

export default function DataImportPage({ sources, onRefreshSources }) {
  const [file, setFile] = useState(null);
  const [sourceName, setSourceName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [selectedQualitySource, setSelectedQualitySource] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Custom column mapping state
  const [showMapping, setShowMapping] = useState(false);
  const [mapping, setMapping] = useState({
    source_record_id: 'id',
    parcel_or_survey_number: 'survey_no',
    owner_name: 'owner',
    property_address: 'address',
    land_area: 'area',
    area_unit: 'area_unit',
    latitude: 'latitude',
    longitude: 'longitude',
    parcel_geometry: 'geometry',
    land_use_category: 'land_use',
    record_date: 'date',
    village_or_locality: 'village'
  });

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setFile(f);
      if (!sourceName) {
        setSourceName(f.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ').toUpperCase());
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg('Please select a file to upload.');
      return;
    }
    if (!sourceName) {
      setErrorMsg('Please enter a source name.');
      return;
    }

    setUploading(true);
    setErrorMsg('');
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_name', sourceName);
    if (showMapping) {
      formData.append('column_mapping', JSON.stringify(mapping));
    }

    try {
      const res = await api.uploadSource(formData);
      setUploadResult(res);
      setFile(null);
      setSourceName('');
      onRefreshSources();
    } catch (err) {
      setErrorMsg(err.message || 'Upload and validation failed');
    } finally {
      setUploading(false);
    }
  };

  const handleInspectQuality = async (sourceId) => {
    try {
      const report = await api.getSourceQuality(sourceId);
      setSelectedQualitySource(report);
    } catch (err) {
      alert('Error fetching quality report: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Data Ingestion & Quality Normalization</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ingest cadastral records from CSV, Excel, GeoJSON, or Shapefile ZIPs with schema mapping & validation.
          </p>
        </div>
      </div>

      {/* Upload Wizard Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <form onSubmit={handleUpload} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Data Source Name
              </label>
              <input
                type="text"
                placeholder="e.g. Tehsil Cadastral Registry 2024"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                className="w-full text-sm px-3.5 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Select File (CSV, Excel, GeoJSON, ZIP)
              </label>
              <input
                type="file"
                accept=".csv, .xlsx, .xls, .geojson, .json, .zip"
                onChange={handleFileChange}
                className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
              />
            </div>
          </div>

          {/* Toggle Schema Mapping Wizard */}
          <div className="pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setShowMapping(!showMapping)}
              className="text-xs text-slate-700 font-medium flex items-center space-x-1 hover:text-emerald-700"
            >
              <Settings2 className="w-3.5 h-3.5" />
              <span>{showMapping ? 'Hide Custom Column Mapping Wizard' : 'Configure Custom Column Mappings (Optional)'}</span>
            </button>

            {showMapping && (
              <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-3">
                <div className="text-xs text-slate-600 flex items-center space-x-1.5">
                  <Info className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Specify the source file's column header names corresponding to the internal common schema:</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                  {Object.keys(mapping).map((field) => (
                    <div key={field}>
                      <span className="text-slate-500 block truncate font-mono mb-1">{field}:</span>
                      <input
                        type="text"
                        value={mapping[field]}
                        onChange={(e) => setMapping({ ...mapping, [field]: e.target.value })}
                        className="w-full px-2.5 py-1.5 rounded border border-slate-300 text-xs focus:ring-1 focus:ring-emerald-500 font-mono"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {errorMsg && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {uploadResult && (
            <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 space-y-1">
              <div className="font-semibold flex items-center space-x-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span>Source "{uploadResult.source_name}" successfully normalized and ingested!</span>
              </div>
              <p>
                Total records: {uploadResult.quality_report?.total_records} | Valid: {uploadResult.quality_report?.valid_records_count} | 
                Invalid: {uploadResult.quality_report?.invalid_records_count} | Warnings: {uploadResult.quality_report?.warnings_count}
              </p>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={uploading}
              className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              <Upload className="w-4 h-4" />
              <span>{uploading ? 'Validating & Normalizing...' : 'Upload & Validate'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Connected Sources & Quality Reports Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h2 className="font-semibold text-slate-900 text-sm mb-4">Ingested Sources & Quality Verification</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-y border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4">Source ID</th>
                <th className="py-2.5 px-4">Agency / Source Name</th>
                <th className="py-2.5 px-4">Format</th>
                <th className="py-2.5 px-4">Total Records</th>
                <th className="py-2.5 px-4">Valid Records</th>
                <th className="py-2.5 px-4">Invalid Records</th>
                <th className="py-2.5 px-4">Quality Warnings</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sources.map((s) => (
                <tr key={s.source_id} className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-mono font-medium text-slate-700">{s.source_id}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{s.source_name}</td>
                  <td className="py-3 px-4 font-mono text-slate-600">{s.file_format}</td>
                  <td className="py-3 px-4 text-slate-800 font-medium">{s.total_records}</td>
                  <td className="py-3 px-4 text-emerald-700 font-medium">{s.valid_records}</td>
                  <td className="py-3 px-4">
                    {s.invalid_records > 0 ? (
                      <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-700 font-semibold">{s.invalid_records}</span>
                    ) : (
                      <span className="text-slate-400">0</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    {s.warnings_count > 0 ? (
                      <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">{s.warnings_count} warnings</span>
                    ) : (
                      <span className="text-emerald-600">None</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleInspectQuality(s.source_id)}
                      className="text-xs px-2.5 py-1 rounded border border-slate-300 text-slate-700 hover:bg-slate-100 font-medium"
                    >
                      Inspect Report
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Quality Modal / Drawer */}
      {selectedQualitySource && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-bold text-slate-900 text-base">
                Data Quality Audit: {selectedQualitySource.source_name}
              </h3>
              <p className="text-xs text-slate-500">
                Audited {selectedQualitySource.total_records} rows. Found {selectedQualitySource.validation_issues?.length || 0} validation issue(s).
              </p>
            </div>
            <button
              onClick={() => setSelectedQualitySource(null)}
              className="text-xs text-slate-500 hover:text-slate-800 font-medium"
            >
              Close
            </button>
          </div>

          <div className="space-y-3">
            {selectedQualitySource.validation_issues?.length === 0 ? (
              <div className="p-4 bg-emerald-50 rounded-lg text-emerald-800 text-xs">
                All records passed structural checks, CRS verification, and mandatory schema constraints.
              </div>
            ) : (
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
                {selectedQualitySource.validation_issues?.map((iss, i) => (
                  <div key={i} className="p-3 text-xs bg-slate-50/50 flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                    <div>
                      <div className="font-semibold text-slate-800">
                        Row #{iss.row_index} • Record ID: <span className="font-mono">{iss.source_record_id || '<MISSING>'}</span>
                      </div>
                      <div className="text-slate-600 mt-0.5 space-y-0.5">
                        {iss.warnings.map((w, wi) => (
                          <div key={wi} className="text-amber-700 font-medium">• {w}</div>
                        ))}
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      iss.is_valid ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {iss.is_valid ? 'Flagged Warning' : 'Rejected Invalid'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

