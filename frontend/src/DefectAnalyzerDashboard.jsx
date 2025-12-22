import React, { useState, useCallback } from 'react';
import { Upload, AlertTriangle, CheckCircle, XCircle, BarChart3, Factory, Wrench, FileText, Camera } from 'lucide-react';

// Main Dashboard Component
export default function DefectAnalyzerDashboard() {
  const [activeTab, setActiveTab] = useState('analyze');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [formData, setFormData] = useState({
    product_sku: 'WK-KN-200',
    facility: 'yangjiang'
  });

  // Product SKU options based on Wiko's catalog
  const skuOptions = [
    { value: 'WK-KN-200', label: 'WK-KN-200 - 8" Chef Knife' },
    { value: 'WK-KN-150', label: 'WK-KN-150 - 6" Utility Knife' },
    { value: 'WK-SC-200', label: 'WK-SC-200 - Kitchen Scissors' },
    { value: 'WK-CI-200', label: 'WK-CI-200 - 20cm Cast Iron Pan' },
    { value: 'WK-CI-240', label: 'WK-CI-240 - 24cm Cast Iron Pan' },
    { value: 'WK-CI-280', label: 'WK-CI-280 - 28cm Pro Pan' },
    { value: 'WK-CI-W280', label: 'WK-CI-W280 - 28cm Wok' },
  ];

  const facilityOptions = [
    { value: 'yangjiang', label: 'Yangjiang Production' },
    { value: 'shenzhen', label: 'Shenzhen R&D' },
    { value: 'hongkong', label: 'Hong Kong HQ' },
  ];

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAnalysisResult(null);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAnalysisResult(null);
    }
  }, []);

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    
    setIsAnalyzing(true);
    
    // Simulate API call - replace with actual API endpoint
    const formDataObj = new FormData();
    formDataObj.append('image', selectedFile);
    formDataObj.append('product_sku', formData.product_sku);
    formDataObj.append('facility', formData.facility);
    const response = await fetch('/api/v1/analyze', { method: 'POST', body: formDataObj });
    
    const result = await response.json();
    if(result.success) {
      setAnalysisResult(result.analysis);
    } else {
      // A simple error handling. You might want to show a notification to the user.
      console.error("Analysis failed:", result.error);
      setAnalysisResult(null);
    }
    setIsAnalyzing(false);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-500',
      major: 'bg-orange-500',
      minor: 'bg-yellow-500',
      cosmetic: 'bg-green-500'
    };
    return colors[severity] || 'bg-gray-500';
  };

  const getSeverityIcon = (severity) => {
    if (severity === 'critical' || severity === 'major') {
      return <XCircle className="w-5 h-5" />;
    }
    if (severity === 'minor') {
      return <AlertTriangle className="w-5 h-5" />;
    }
    return <CheckCircle className="w-5 h-5" />;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Factory className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Wiko Manufacturing Intelligence</h1>
              <p className="text-sm text-gray-400">Defect Analysis Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">Powered by Azure AI Foundry</span>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6">
        <div className="flex gap-1">
          {[
            { id: 'analyze', label: 'Analyze', icon: Camera },
            { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
            { id: 'reports', label: 'Reports', icon: FileText },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="p-6">
        {activeTab === 'analyze' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Upload Section */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-400" />
                Product Inspection
              </h2>
              
              {/* Configuration */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Product SKU</label>
                  <select
                    value={formData.product_sku}
                    onChange={(e) => setFormData({...formData, product_sku: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {skuOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Facility</label>
                  <select
                    value={formData.facility}
                    onChange={(e) => setFormData({...formData, facility: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {facilityOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Drop Zone */}
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                  previewUrl ? 'border-blue-500 bg-blue-500/10' : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                {previewUrl ? (
                  <div className="space-y-4">
                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="max-h-64 mx-auto rounded-lg shadow-lg"
                    />
                    <p className="text-sm text-gray-400">{selectedFile?.name}</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Upload className="w-12 h-12 mx-auto text-gray-500" />
                    <p className="text-gray-400">Drag & drop product image here</p>
                    <p className="text-sm text-gray-500">or click to browse</p>
                  </div>
                )}
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  style={{ position: 'relative' }}
                />
              </div>

              {/* Analyze Button */}
              <button
                onClick={handleAnalyze}
                disabled={!selectedFile || isAnalyzing}
                className={`w-full mt-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
                  !selectedFile || isAnalyzing
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Analyzing with GPT-5.2...
                  </>
                ) : (
                  <>
                    <Camera className="w-5 h-5" />
                    Analyze for Defects
                  </>
                )}
              </button>
            </div>

            {/* Results Section */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                Analysis Results
              </h2>

              {analysisResult ? (
                <div className="space-y-4">
                  {/* Status Badge */}
                  <div className={`flex items-center gap-3 p-4 rounded-lg ${
                    analysisResult.defect_detected ? 'bg-red-500/20' : 'bg-green-500/20'
                  }`}>
                    {analysisResult.defect_detected ? (
                      <XCircle className="w-8 h-8 text-red-400" />
                    ) : (
                      <CheckCircle className="w-8 h-8 text-green-400" />
                    )}
                    <div>
                      <p className="font-semibold text-lg">
                        {analysisResult.defect_detected ? 'Defect Detected' : 'No Defects Found'}
                      </p>
                      <p className="text-sm text-gray-400">
                        Confidence: {(analysisResult.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {/* Analysis Details - Always show */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-1">Defect Type</p>
                      <p className="font-medium capitalize">
                        {analysisResult.defect_type.replace(/_/g, ' ')}
                      </p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-1">Severity</p>
                      <div className="flex items-center gap-2">
                        <span className={`w-3 h-3 rounded-full ${getSeverityColor(analysisResult.severity)}`}></span>
                        <span className="font-medium capitalize">{analysisResult.severity}</span>
                      </div>
                    </div>
                  </div>

                  {/* Description */}
                  {analysisResult.description && (
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-1">Description</p>
                      <p className="text-sm">{analysisResult.description}</p>
                    </div>
                  )}

                  {/* Affected Area */}
                  {analysisResult.affected_area && (
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-1">Affected Area</p>
                      <p className="text-sm capitalize">{analysisResult.affected_area}</p>
                    </div>
                  )}

                  {/* Root Cause Analysis */}
                  {analysisResult.root_cause && (
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                        <Wrench className="w-3 h-3" />
                        Root Cause Analysis
                      </p>
                      <p className="text-sm font-medium mb-2">{analysisResult.root_cause}</p>
                      {analysisResult.probable_stage && (
                        <>
                          <p className="text-xs text-gray-400 mb-1 mt-3">Probable Stage</p>
                          <p className="text-sm capitalize">{analysisResult.probable_stage?.replace(/_/g, ' ')}</p>
                        </>
                      )}
                    </div>
                  )}

                  {/* 5-Why Analysis */}
                  {analysisResult.five_why_chain && analysisResult.five_why_chain.length > 0 && (
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-2">5-Why Analysis Chain</p>
                      <ol className="space-y-2">
                        {analysisResult.five_why_chain.map((why, i) => (
                          <li key={i} className="text-sm flex items-start gap-2">
                            <span className="text-blue-400 font-semibold">Why {i + 1}:</span>
                            <span className="flex-1">{why}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Ishikawa (Fishbone) Analysis */}
                  {analysisResult.ishikawa_analysis && (
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-3">Ishikawa (Fishbone) Analysis</p>
                      <div className="grid grid-cols-2 gap-3">
                        {Object.entries(analysisResult.ishikawa_analysis).map(([category, description]) => (
                          description && (
                            <div key={category} className="bg-gray-800/50 rounded p-2">
                              <p className="text-xs font-semibold text-yellow-400 capitalize mb-1">{category}</p>
                              <p className="text-xs text-gray-300">{description}</p>
                            </div>
                          )
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Contributing Factors */}
                  {analysisResult.contributing_factors && analysisResult.contributing_factors.length > 0 && (
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-2">Contributing Factors</p>
                      <ul className="space-y-1">
                        {analysisResult.contributing_factors.map((factor, i) => (
                          <li key={i} className="text-sm flex items-start gap-2">
                            <span className="text-yellow-500 mt-1">•</span>
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Actions */}
                  {((analysisResult.corrective_actions && analysisResult.corrective_actions.length > 0) ||
                    (analysisResult.preventive_actions && analysisResult.preventive_actions.length > 0)) && (
                    <div className="grid grid-cols-1 gap-4">
                      {analysisResult.corrective_actions && analysisResult.corrective_actions.length > 0 && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                          <p className="text-xs text-red-400 mb-2 font-medium">Corrective Actions (Immediate)</p>
                          <ul className="space-y-1">
                            {analysisResult.corrective_actions.map((action, i) => (
                              <li key={i} className="text-sm flex items-start gap-2">
                                <span className="text-red-400 mt-1">→</span>
                                {action}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {analysisResult.preventive_actions && analysisResult.preventive_actions.length > 0 && (
                        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                          <p className="text-xs text-blue-400 mb-2 font-medium">Preventive Actions (Long-term)</p>
                          <ul className="space-y-1">
                            {analysisResult.preventive_actions.map((action, i) => (
                              <li key={i} className="text-sm flex items-start gap-2">
                                <span className="text-blue-400 mt-1">→</span>
                                {action}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Model & Performance Metadata */}
                  <div className="bg-gray-700/30 rounded-lg p-3 border border-gray-600">
                    <p className="text-xs font-semibold text-gray-400 mb-2">GPT Analysis Metadata</p>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <p className="text-gray-500">Model</p>
                        <p className="text-gray-300 font-mono">{analysisResult.model_version || 'gpt-5.2'}</p>
                      </div>
                      {analysisResult.reasoning_tokens_used > 0 && (
                        <div>
                          <p className="text-gray-500">Reasoning Tokens</p>
                          <p className="text-blue-400 font-mono">{analysisResult.reasoning_tokens_used.toLocaleString()}</p>
                        </div>
                      )}
                      <div>
                        <p className="text-gray-500">Defect ID</p>
                        <p className="text-gray-300 font-mono">{analysisResult.defect_id}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Analyzed</p>
                        <p className="text-gray-300">{new Date(analysisResult.timestamp).toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Facility</p>
                        <p className="text-gray-300 capitalize">{analysisResult.facility}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Product SKU</p>
                        <p className="text-gray-300 font-mono">{analysisResult.product_sku}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Camera className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Upload an image to analyze</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="text-center py-12 text-gray-500">
            <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Dashboard view coming soon</p>
            <p className="text-sm">Real-time defect metrics and trends</p>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="text-center py-12 text-gray-500">
            <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Reports view coming soon</p>
            <p className="text-sm">Shift reports and export functionality</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 px-6 py-4 mt-auto">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <p>© 2025 Wiko Cutlery Ltd. Manufacturing Intelligence Platform</p>
          <p>Hong Kong | Shenzhen | Yangjiang</p>
        </div>
      </footer>
    </div>
  );
}
