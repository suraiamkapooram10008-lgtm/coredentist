import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileDown, CheckCircle2, AlertCircle, Database } from "lucide-react";

export default function DataMigration() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('idle');

    // Simulate parsing CSV and migrating to database
    setTimeout(() => {
      setIsUploading(false);
      setUploadStatus('success');
    }, 2000);
  };

  return (
    <div className="container mx-auto p-6 space-y-8 max-w-5xl">
      <div>
        <h1 className="text-3xl font-black text-slate-800 tracking-tight">Data Migration</h1>
        <p className="text-slate-500 font-medium mt-1">Import patients, schedules, and clinical notes from legacy systems like OpenDental or Dentrix.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* CSV Import */}
        <Card className="border-slate-200 shadow-sm rounded-2xl">
          <CardHeader>
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <Upload className="w-6 h-6" />
            </div>
            <CardTitle className="text-xl font-bold">Import via CSV</CardTitle>
            <CardDescription>
              Upload exported CSV files from your legacy software. We will automatically map the columns to the CoreDent schema.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors">
              <input 
                type="file" 
                id="csv-upload" 
                className="hidden" 
                accept=".csv"
                onChange={handleFileUpload}
              />
              <label htmlFor="csv-upload" className="cursor-pointer flex flex-col items-center">
                <Database className="w-10 h-10 text-slate-300 mb-3" />
                <span className="font-bold text-blue-600 hover:text-blue-700">Click to browse</span>
                <span className="text-xs text-slate-500 mt-1">or drag and drop a .csv file</span>
              </label>
            </div>

            {isUploading && (
              <div className="p-4 bg-blue-50 rounded-xl flex items-center gap-3">
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin shrink-0" />
                <p className="text-sm font-bold text-blue-800">Processing migration mapping...</p>
              </div>
            )}

            {uploadStatus === 'success' && (
              <div className="p-4 bg-emerald-50 rounded-xl flex items-center gap-3 border border-emerald-100">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <div>
                  <p className="text-sm font-bold text-emerald-800">Migration Successful</p>
                  <p className="text-xs text-emerald-600 font-medium">1,204 patient records were imported.</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Export Templates */}
        <Card className="border-slate-200 shadow-sm rounded-2xl">
          <CardHeader>
            <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
              <FileDown className="w-6 h-6" />
            </div>
            <CardTitle className="text-xl font-bold">Download Templates</CardTitle>
            <CardDescription>
              If your legacy system does not export cleanly, you can copy your data into our standard templates before uploading.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button variant="outline" className="w-full justify-start h-12 font-semibold">
              <FileDown className="w-4 h-4 mr-3 text-slate-400" />
              Patients Template (.csv)
            </Button>
            <Button variant="outline" className="w-full justify-start h-12 font-semibold">
              <FileDown className="w-4 h-4 mr-3 text-slate-400" />
              Appointments Template (.csv)
            </Button>
            <Button variant="outline" className="w-full justify-start h-12 font-semibold">
              <FileDown className="w-4 h-4 mr-3 text-slate-400" />
              Treatment Ledger Template (.csv)
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Manual DB Connection (Placeholder) */}
      <Card className="border-amber-200 shadow-sm rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50">
        <CardHeader>
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="w-6 h-6 text-amber-600" />
            <CardTitle className="text-xl font-bold text-amber-900">Direct SQL Connection</CardTitle>
          </div>
          <CardDescription className="text-amber-700">
            Automated direct database extraction from on-premise OpenDental (MySQL) or Dentrix (c-treeACE) servers requires installing the local CoreDent Extraction Agent on your physical server.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button disabled className="bg-amber-600 hover:bg-amber-700 text-white font-bold opacity-50 cursor-not-allowed">
            Configure DB Connection (Beta)
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
