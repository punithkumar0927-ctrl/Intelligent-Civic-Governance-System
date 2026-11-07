import React, { useRef, useState } from 'react';
import { Upload, ImageIcon, X, CheckCircle } from 'lucide-react';

interface UploadPanelProps {
  label: string;
  onFileSelect: (file: File | null) => void;
  value?: File | null;
}

export default function UploadPanel({ label, onFileSelect, value }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string>('');
  const [dragging, setDragging] = useState(false);

  const handleFile = (file: File | null) => {
    if (file) {
      const url = URL.createObjectURL(file);
      setPreview(url);
    } else {
      setPreview('');
    }
    onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) handleFile(file);
  };

  const clear = () => {
    handleFile(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>

      {preview ? (
        <div className="relative rounded-xl border-2 border-green-300 overflow-hidden bg-gray-50">
          <img src={preview} alt="preview" className="w-full h-48 object-cover" />
          <div className="absolute top-2 right-2 flex items-center gap-2">
            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded flex items-center gap-1">
              <CheckCircle size={12} /> Attached
            </span>
            <button
              type="button"
              onClick={clear}
              className="p-1 bg-white rounded-full shadow hover:bg-red-50 text-gray-500 hover:text-red-500"
            >
              <X size={16} />
            </button>
          </div>
          <div className="absolute bottom-2 left-2 text-xs bg-black/50 text-white px-2 py-1 rounded">
            {value?.name}
          </div>
        </div>
      ) : (
        <div
          className={`
            flex flex-col items-center justify-center gap-2 h-36 rounded-xl
            border-2 border-dashed transition-colors cursor-pointer
            ${dragging
              ? 'border-nexus-400 bg-nexus-50'
              : 'border-gray-300 bg-gray-50 hover:border-nexus-300 hover:bg-nexus-50'
            }
          `}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <Upload size={28} className={dragging ? 'text-nexus-500' : 'text-gray-400'} />
          <p className="text-sm text-gray-500 text-center px-4">
            Drag & drop image or <span className="text-nexus-600 font-medium">browse</span>
          </p>
          <p className="text-xs text-gray-400">JPG, PNG, WebP · Max 20MB</p>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/bmp"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}
