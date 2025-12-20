export interface User {
  username: string;
  password: string;
}

export interface AuthResponse {
  'control:Auth-Type': string;
  'reply:Reply-Message': string;
  'reply:Framed-IP-Address'?: string;
  'reply:Session-Timeout'?: string;
  'reply:Service-Type'?: string;
  [key: string]: string | undefined;
}

export interface AuthRequest {
  username: string;
  password: string;
  nas_ip_address?: string;
  nas_identifier?: string;
  service_type?: string;
}

export interface SessionInfo {
  sessionId: string;
  username: string;
  startTime: Date;
  ipAddress?: string;
  timeout?: number;
}

export interface AccountingRequest {
  username: string;
  session_id: string;
  status_type: 'Start' | 'Stop' | 'Interim-Update';
  nas_ip_address?: string;
  input_octets?: string;
  output_octets?: string;
  input_packets?: string;
  output_packets?: string;
  session_time?: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface NetworkInfo {
  ssid?: string;
  macAddress?: string;
  ipAddress?: string;
  userAgent?: string;
}
