export type DocumentStatus = "UPLOADING" | "UPLOADED" | "PROCESSING" | "READY" | "FAILED";

export interface BusinessDocument {
  id: string;
  business_id: string;
  uploaded_by: string;
  file_name: string;
  original_name: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentStatusInfo {
  id: string;
  status: DocumentStatus;
}
