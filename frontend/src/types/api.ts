// API Envelope Types

export interface ApiResponse<T> {
  status: 'SUCCESS' | 'ERROR' | 'IDEMPOTENT_DUPLICATE' | 'APPROVAL_REQUIRED';
  data: T;
  error?: {
    error_code: string;
    message: string;
    request_id?: string;
    correlation_id?: string;
  } | null;
  metadata?: {
    request_id?: string;
    correlation_id?: string;
  };
}
