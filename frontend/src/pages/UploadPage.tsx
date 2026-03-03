import {
  CheckCircle2,
  FileSpreadsheet,
  Loader2,
  Upload,
  X,
} from "lucide-react";
import { useCallback, useState, type DragEvent } from "react";
import { Link } from "react-router-dom";

import { transactionApi, type UploadResponse } from "@/lib/api";

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState("");

  const handleDrag = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragging(true);
    else if (e.type === "dragleave") setDragging(false);
  }, []);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.name.endsWith(".csv") || f.type === "text/csv"
    );
    setFiles((prev) => [...prev, ...dropped]);
    setResult(null);
    setError("");
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
      setResult(null);
      setError("");
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const res = await transactionApi.upload(files);
      setResult(res);
      setFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-12 px-6">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white/90 mb-2">
          Upload Transactions
        </h1>
        <p className="text-white/40 text-sm">
          Drop your CIBC CSV bank statements here
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative rounded-xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
          dragging
            ? "border-amber-500/50 bg-amber-500/[0.04]"
            : "border-white/[0.08] hover:border-white/[0.15] bg-white/[0.02]"
        }`}
      >
        <input
          type="file"
          accept=".csv"
          multiple
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <Upload
          className={`w-10 h-10 mx-auto mb-4 ${dragging ? "text-amber-400" : "text-white/20"}`}
        />
        <p className="text-white/60 text-sm mb-1">
          Drag & drop CSV files here, or click to browse
        </p>
        <p className="text-white/25 text-xs">
          Supports CIBC debit and credit card formats
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          {files.map((file, i) => (
            <div
              key={`${file.name}-${i}`}
              className="flex items-center justify-between px-4 py-3 rounded-lg bg-white/[0.03] border border-white/[0.06]"
            >
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-4 h-4 text-amber-400/70" />
                <span className="text-sm text-white/70">{file.name}</span>
                <span className="text-xs text-white/25">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
              <button
                onClick={() => removeFile(i)}
                className="text-white/20 hover:text-white/50 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full mt-4 py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-[#0a0a0b] font-semibold text-sm rounded-lg transition-all disabled:opacity-50 cursor-pointer"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing...
              </span>
            ) : (
              `Upload ${files.length} file${files.length > 1 ? "s" : ""}`
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mt-6 p-6 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span className="text-white/80 font-medium">Upload Complete</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-white/35 text-xs uppercase tracking-wider mb-1">
                Uploaded
              </p>
              <p className="text-2xl font-semibold text-white/90">
                {result.uploaded}
              </p>
            </div>
            <div>
              <p className="text-white/35 text-xs uppercase tracking-wider mb-1">
                Duplicates Skipped
              </p>
              <p className="text-2xl font-semibold text-white/50">
                {result.duplicates_skipped}
              </p>
            </div>
          </div>
          {result.months_affected.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/[0.06]">
              <p className="text-white/35 text-xs uppercase tracking-wider mb-2">
                Months Affected
              </p>
              <div className="flex gap-2 flex-wrap">
                {result.months_affected.map((month) => (
                  <Link
                    key={month}
                    to={`/transactions?month=${month}`}
                    className="px-3 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs hover:bg-amber-500/20 transition-colors"
                  >
                    {month}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
