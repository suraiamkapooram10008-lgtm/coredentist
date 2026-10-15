import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Upload, FileDown, CheckCircle2, Database, Loader2, ArrowRight } from "lucide-react";
import { apiClient } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

interface DryRunResult {
  total_rows: number;
  valid_count: number;
  duplicate_count: number;
  error_count: number;
  errors: string[];
  duplicates: string[];
  preview: Array<{
    first_name: string;
    last_name: string;
    date_of_birth: string;
    email?: string;
    phone?: string;
  }>;
}

export default function DataMigration() {
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(false);
  const [dryRunData, setDryRunData] = useState<DryRunResult | null>(null);
  const [parsedRows, setParsedRows] = useState<any[]>([]);
  const [commitSuccess, setCommitSuccess] = useState<number | null>(null);

  const parseCsvToRows = (text: string) => {
    const lines = text.split(/\r?\n/).filter(line => line.trim().length > 0);
    if (lines.length < 2) return [];
    const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, '').toLowerCase().replace(/[\s-]/g, '_'));

    const rows = [];
    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].split(',').map(p => p.trim().replace(/^["']|["']$/g, ''));
      if (parts.length === 0 || (parts.length === 1 && !parts[0])) continue;
      const row: Record<string, string> = {};
      headers.forEach((header, index) => {
        row[header] = parts[index] || '';
      });
      rows.push(row);
    }
    return rows;
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setDryRunData(null);
    setCommitSuccess(null);

    try {
      const text = await file.text();
      const rows = parseCsvToRows(text);
      if (rows.length === 0) {
        toast({
          title: "Empty or invalid CSV",
          description: "No data rows were found in the uploaded CSV file.",
          variant: "destructive",
        });
        setIsProcessing(false);
        return;
      }

      setParsedRows(rows);

      // Call Stage 1: Dry-Run API
      const response = await apiClient.post<DryRunResult>("/patients/import/dry-run", { rows });
      const data = response.data || (response as any);
      setDryRunData(data);

      toast({
        title: "Dry Run Completed",
        description: `Validated ${data.valid_count || 0} of ${data.total_rows || 0} rows. Review before commit.`,
      });
    } catch (err: any) {
      toast({
        title: "Validation Error",
        description: err?.message || "Failed to parse and validate CSV file.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCommitMigration = async () => {
    if (!parsedRows || parsedRows.length === 0) return;
    setIsProcessing(true);

    try {
      // Call Stage 2: Commit API
      const response = await apiClient.post<{ success: boolean; imported_count: number; message: string }>(
        "/patients/import/commit",
        { rows: parsedRows }
      );
      const data = response.data || (response as any);
      const count = data.imported_count ?? dryRunData?.valid_count ?? 0;
      setCommitSuccess(count);
      setDryRunData(null);
      setParsedRows([]);
      toast({
        title: "Migration Successful",
        description: `${count} patient records were successfully imported.`,
      });
    } catch (err: any) {
      toast({
        title: "Migration Failed",
        description: err?.message || "Failed to commit patient records.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-8 max-w-5xl">
      <div>
        <h1 className="text-3xl font-black text-slate-800 tracking-tight">Data Migration</h1>
        <p className="text-slate-500 font-medium mt-1">Import patients, schedules, and clinical notes from legacy systems like OpenDental or Dentrix.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* CSV Import */}
        <Card className="border-slate-200 shadow-sm rounded-2xl md:col-span-2">
          <CardHeader>
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <Upload className="w-6 h-6" />
            </div>
            <CardTitle className="text-xl font-bold">Two-Stage CSV Import</CardTitle>
            <CardDescription>
              Upload exported CSV files from your legacy software. Step 1 performs a non-destructive dry-run validation with duplicate detection. Step 2 commits valid records into CoreDent.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:bg-slate-50 transition-colors">
              <input 
                type="file" 
                id="csv-upload" 
                className="hidden" 
                accept=".csv"
                onChange={handleFileUpload}
                disabled={isProcessing}
              />
              <label htmlFor="csv-upload" className="cursor-pointer flex flex-col items-center">
                <Database className="w-10 h-10 text-slate-300 mb-3" />
                <span className="font-bold text-blue-600 hover:text-blue-700">Click to browse</span>
                <span className="text-xs text-slate-500 mt-1">or drag and drop a .csv file</span>
              </label>
            </div>

            {isProcessing && (
              <div className="p-4 bg-blue-50 rounded-xl flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin shrink-0" />
                <p className="text-sm font-bold text-blue-800">Processing migration data...</p>
              </div>
            )}

            {commitSuccess !== null && (
              <div className="p-4 bg-emerald-50 rounded-xl flex items-center gap-3 border border-emerald-100">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <div>
                  <p className="text-sm font-bold text-emerald-800">Migration Successful</p>
                  <p className="text-xs text-emerald-600 font-medium">{commitSuccess} patient records were imported.</p>
                </div>
              </div>
            )}

            {dryRunData && (
              <div className="space-y-4 rounded-xl border border-slate-200 p-5 bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800">Dry-Run Validation Report</h3>
                    <p className="text-xs text-slate-500">Review validation stats before committing</p>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                      Valid: {dryRunData.valid_count}
                    </Badge>
                    {dryRunData.duplicate_count > 0 && (
                      <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                        Duplicates: {dryRunData.duplicate_count}
                      </Badge>
                    )}
                    {dryRunData.error_count > 0 && (
                      <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                        Errors: {dryRunData.error_count}
                      </Badge>
                    )}
                  </div>
                </div>

                {dryRunData.preview && dryRunData.preview.length > 0 && (
                  <div className="border rounded-lg bg-white overflow-hidden text-xs">
                    <div className="bg-slate-100 px-3 py-2 font-semibold text-slate-600 border-b">Sample Preview</div>
                    <div className="divide-y">
                      {dryRunData.preview.map((p, idx) => (
                        <div key={idx} className="px-3 py-2 flex justify-between">
                          <span className="font-medium text-slate-800">{p.first_name} {p.last_name}</span>
                          <span className="text-slate-500">DOB: {p.date_of_birth}</span>
                          <span className="text-slate-500">{p.email || p.phone || 'No contact'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {dryRunData.valid_count > 0 && (
                  <Button 
                    onClick={handleCommitMigration} 
                    disabled={isProcessing}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-11"
                  >
                    <ArrowRight className="w-4 h-4 mr-2" />
                    Confirm & Commit {dryRunData.valid_count} Records
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Export Templates */}
        <Card className="border-slate-200 shadow-sm rounded-2xl md:col-span-2">
          <CardHeader>
            <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
              <FileDown className="w-6 h-6" />
            </div>
            <CardTitle className="text-xl font-bold">Standard Import Templates</CardTitle>
            <CardDescription>
              Download pre-formatted CSV headers matching CoreDent's schema for smooth migration.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Button 
              variant="outline" 
              className="w-full justify-start h-12 font-semibold"
              onClick={() => {
                const csv = "first_name,last_name,date_of_birth,gender,email,phone,address_street,address_city,address_state,address_zip\\nJohn,Doe,1990-05-15,male,john.doe@example.com,555-0199,123 Main St,Springfield,IL,62701";
                const blob = new Blob([csv], { type: "text/csv" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "coredent_patients_template.csv";
                a.click();
              }}
            >
              <FileDown className="w-4 h-4 mr-3 text-slate-400" />
              Patients Template (.csv)
            </Button>
            <Button variant="outline" className="w-full justify-start h-12 font-semibold" disabled title="Coming soon">
              <FileDown className="w-4 h-4 mr-3 text-slate-400" />
              Appointments (.csv)
            </Button>
            <Button variant="outline" className="w-full justify-start h-12 font-semibold" disabled title="Coming soon">
              <FileDown className="w-4 h-4 mr-3 text-slate-400" />
              Ledger (.csv)
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
