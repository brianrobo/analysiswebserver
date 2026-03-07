import { useState, useRef } from 'react'
import { Upload, File, X } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void
  selectedFile: File | null
  onClear: () => void
}

export function FileUploadZone({ onFileSelect, selectedFile, onClear }: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): boolean => {
    return file.name.endsWith('.py') || file.name.endsWith('.zip')
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) {
      if (validateFile(file)) {
        onFileSelect(file)
      } else {
        toast.error('.py 또는 .zip 파일만 업로드 가능합니다.')
      }
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (validateFile(file)) {
        onFileSelect(file)
      } else {
        toast.error('.py 또는 .zip 파일만 업로드 가능합니다.')
      }
    }
  }

  if (selectedFile) {
    return (
      <div className="flex items-center gap-3 p-4 border rounded-lg bg-muted/30">
        <File className="h-8 w-8 text-primary shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{selectedFile.name}</p>
          <p className="text-sm text-muted-foreground">
            {selectedFile.size >= 1024 * 1024
              ? `${(selectedFile.size / 1024 / 1024).toFixed(1)} MB`
              : `${(selectedFile.size / 1024).toFixed(1)} KB`}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={onClear}>
          <X className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
        isDragging
          ? 'border-primary bg-primary/5'
          : 'border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/30'
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".py,.zip"
        className="hidden"
        onChange={handleInputChange}
      />
      <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
      <p className="font-medium">파일을 드래그하거나 클릭해서 선택</p>
      <p className="text-sm text-muted-foreground mt-1">.py 또는 .zip 파일 지원</p>
    </div>
  )
}
