import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, ArrowRight, ArrowLeft, Check, AlertCircle, FileText, Users, Loader2, X, Download } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const STEPS = ['Upload', 'Map Columns', 'Preview', 'Import'];

export default function CSVMemberImport() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [parseResult, setParseResult] = useState(null);
  const [mapping, setMapping] = useState({});
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [parsing, setParsing] = useState(false);

  const handleFileSelect = (e) => {
    const f = e.target.files?.[0];
    if (f && f.name.endsWith('.csv')) {
      setFile(f);
    } else {
      toast.error('Please select a .csv file');
    }
  };

  const handleParse = async () => {
    if (!file) return;
    setParsing(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/members/import/parse`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setParseResult(data);
        // Auto-map by matching headers to system field labels/keys
        const autoMap = {};
        for (const sf of data.system_fields) {
          const match = data.headers.find(h =>
            h.toLowerCase().replace(/[_\s]/g, '') === sf.key.replace(/[_\s]/g, '') ||
            h.toLowerCase().includes(sf.label.toLowerCase().split(' ')[0].toLowerCase())
          );
          if (match) autoMap[sf.key] = match;
        }
        setMapping(autoMap);
        setStep(1);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to parse CSV');
      }
    } catch {
      toast.error('Failed to upload CSV');
    } finally {
      setParsing(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mapping', JSON.stringify(mapping));
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/members/import/execute`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setImportResult(data);
        setStep(3);
        toast.success(`${data.imported} members imported successfully!`);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Import failed');
      }
    } catch {
      toast.error('Import failed');
    } finally {
      setImporting(false);
    }
  };

  const getMappedPreview = () => {
    if (!parseResult?.preview) return [];
    return parseResult.preview.map(row => {
      const mapped = {};
      for (const sf of parseResult.system_fields) {
        const csvCol = mapping[sf.key];
        mapped[sf.label] = csvCol ? row[csvCol] || '' : '';
      }
      return mapped;
    });
  };

  return (
    <div className="space-y-6" data-testid="csv-import-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Import Members</h1>
          <p className="page-subtitle">Upload a CSV file to bulk import members into your church database</p>
        </div>
        <button
          onClick={() => navigate('/people')}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
          data-testid="back-to-members-btn"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Members
        </button>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center gap-2 bg-white border border-slate-200 p-4 rounded-lg" data-testid="step-indicator">
        {STEPS.map((label, idx) => (
          <div key={label} className="flex items-center gap-2 flex-1">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                idx < step ? 'bg-emerald-500 text-white' :
                idx === step ? 'bg-slate-900 text-white' :
                'bg-slate-100 text-slate-400'
              }`}
              data-testid={`step-${idx}`}
            >
              {idx < step ? <Check className="w-4 h-4" /> : idx + 1}
            </div>
            <span className={`text-sm font-medium ${idx <= step ? 'text-slate-900' : 'text-slate-400'}`}>{label}</span>
            {idx < STEPS.length - 1 && <div className={`flex-1 h-0.5 ${idx < step ? 'bg-emerald-500' : 'bg-slate-200'}`} />}
          </div>
        ))}
      </div>

      {/* Step 0: Upload */}
      {step === 0 && (
        <div className="bg-white border border-slate-200 rounded-lg p-8" data-testid="step-upload">
          <div
            className="border-2 border-dashed border-slate-300 rounded-lg p-12 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/30 transition-colors"
            onClick={() => fileInputRef.current?.click()}
            data-testid="upload-dropzone"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
              data-testid="csv-file-input"
            />
            <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-1">
              {file ? file.name : 'Drop your CSV file here or click to browse'}
            </h3>
            <p className="text-sm text-slate-500">
              {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Supports .csv files with headers in the first row'}
            </p>
          </div>

          {file && (
            <div className="mt-4 flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <FileText className="w-8 h-8 text-blue-500" />
                <div>
                  <p className="text-sm font-medium text-slate-900">{file.name}</p>
                  <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setFile(null)} className="text-slate-400 hover:text-red-500">
                  <X className="w-4 h-4" />
                </button>
                <button
                  onClick={handleParse}
                  disabled={parsing}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
                  data-testid="parse-csv-btn"
                >
                  {parsing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  Continue
                </button>
              </div>
            </div>
          )}

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="text-sm font-semibold text-blue-900 mb-1">CSV Format Tips</h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>First row should contain column headers (e.g., First Name, Last Name, Email)</li>
              <li>Each subsequent row represents one member</li>
              <li>Required fields: First Name and Last Name</li>
              <li>Optional: Email, Phone, Gender, Date of Birth, Membership Status</li>
            </ul>
          </div>
        </div>
      )}

      {/* Step 1: Map Columns */}
      {step === 1 && parseResult && (
        <div className="bg-white border border-slate-200 rounded-lg p-6" data-testid="step-map-columns">
          <h2 className="text-lg font-semibold text-slate-900 mb-1">Map Your CSV Columns</h2>
          <p className="text-sm text-slate-500 mb-6">Match your CSV columns to the system fields below. We auto-detected some mappings.</p>

          <div className="space-y-3">
            {parseResult.system_fields.map(sf => (
              <div key={sf.key} className="flex items-center gap-4 py-2 border-b border-slate-100">
                <div className="w-40">
                  <span className="text-sm font-medium text-slate-700">{sf.label}</span>
                  {sf.required && <span className="text-red-500 ml-1 text-xs">*</span>}
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 shrink-0" />
                <select
                  value={mapping[sf.key] || ''}
                  onChange={(e) => setMapping(prev => ({ ...prev, [sf.key]: e.target.value }))}
                  className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  data-testid={`map-${sf.key}`}
                >
                  <option value="">-- Skip --</option>
                  {parseResult.headers.map(h => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-200">
            <button onClick={() => setStep(0)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={() => setStep(2)}
              disabled={!mapping.first_name || !mapping.last_name}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-lg hover:bg-slate-800 disabled:opacity-50"
              data-testid="to-preview-btn"
            >
              Preview <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Preview */}
      {step === 2 && parseResult && (
        <div className="bg-white border border-slate-200 rounded-lg p-6" data-testid="step-preview">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Preview Import</h2>
              <p className="text-sm text-slate-500">{parseResult.total_rows} rows will be processed. Showing first {parseResult.preview.length}.</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full font-medium">
              <Check className="w-4 h-4" /> Ready to import
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  {parseResult.system_fields.filter(sf => mapping[sf.key]).map(sf => (
                    <th key={sf.key} className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{sf.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {getMappedPreview().map((row, idx) => (
                  <tr key={`csv-row-${idx}`} className="border-t border-slate-100 hover:bg-slate-50">
                    {parseResult.system_fields.filter(sf => mapping[sf.key]).map(sf => (
                      <td key={sf.key} className="px-4 py-2.5 text-slate-700">{row[sf.label] || <span className="text-slate-300">--</span>}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-200">
            <button onClick={() => setStep(1)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={handleImport}
              disabled={importing}
              className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 text-white text-sm font-semibold rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              data-testid="execute-import-btn"
            >
              {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />}
              {importing ? 'Importing...' : `Import ${parseResult.total_rows} Members`}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Results */}
      {step === 3 && importResult && (
        <div className="bg-white border border-slate-200 rounded-lg p-8 text-center" data-testid="step-results">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-emerald-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Import Complete</h2>
          <p className="text-slate-500 mb-6">Your CSV has been processed successfully.</p>

          <div className="grid grid-cols-3 gap-4 max-w-md mx-auto mb-6">
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
              <p className="text-2xl font-bold text-emerald-700">{importResult.imported}</p>
              <p className="text-xs text-emerald-600 font-medium">Imported</p>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-2xl font-bold text-amber-700">{importResult.skipped}</p>
              <p className="text-xs text-amber-600 font-medium">Skipped</p>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-2xl font-bold text-red-700">{importResult.errors?.length || 0}</p>
              <p className="text-xs text-red-600 font-medium">Errors</p>
            </div>
          </div>

          {importResult.errors?.length > 0 && (
            <div className="text-left bg-red-50 border border-red-200 rounded-lg p-4 mb-6 max-w-md mx-auto">
              <h4 className="text-sm font-semibold text-red-800 mb-2 flex items-center gap-1">
                <AlertCircle className="w-4 h-4" /> Error Details
              </h4>
              {importResult.errors.map((err, idx) => (
                <p key={`csv-err-${idx}`} className="text-xs text-red-700">Row {err.row}: {err.error}</p>
              ))}
            </div>
          )}

          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => navigate('/people')}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-lg hover:bg-slate-800"
              data-testid="go-to-members-btn"
            >
              <Users className="w-4 h-4" /> View Members
            </button>
            <button
              onClick={() => { setStep(0); setFile(null); setParseResult(null); setMapping({}); setImportResult(null); }}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50"
            >
              Import Another File
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
