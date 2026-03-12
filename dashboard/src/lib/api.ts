const API_BASE = '/api';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

// ─── Types ───────────────────────────────────────────────────────────────────

export interface Token {
  access_token: string;
  token_type: string;
}

export interface QueryFilter {
  column: string;
  op: 'eq' | 'ne' | 'in' | 'gt' | 'lt' | 'gte' | 'lte';
  value: string | number | (string | number)[];
}

export interface FrequencyQuery {
  group_by: string[];
  filters: QueryFilter[];
  value_column?: string;
}

export interface MeansQuery {
  group_by: string[];
  value_columns: string[];
  filters: QueryFilter[];
}

export interface FrequencyResult {
  csv: string;
  suppressions: Record<string, Record<number, string>>;
}

export interface MeansResult {
  csv: string;
  count_csv: string;
  suppressions: Record<string, Record<number, string>>;
}

export interface UserScope {
  filters: Record<string, string[]>;
}

export interface User {
  id: number;
  username: string;
  scope: UserScope;
  is_active: boolean;
  is_admin: boolean;
}

export interface UserCreate {
  username: string;
  password: string;
  scope?: UserScope;
  is_admin?: boolean;
}

export interface UserUpdate {
  password?: string;
  scope?: UserScope;
  is_active?: boolean;
  is_admin?: boolean;
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export async function login(username: string, password: string): Promise<Token> {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString()
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail ?? detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<Token>;
}

export async function getMe(token: string): Promise<User> {
  return apiFetch<User>('/admin/me', { headers: authHeaders(token) });
}

// ─── Data ────────────────────────────────────────────────────────────────────

export async function getColumns(token: string): Promise<string[]> {
  return apiFetch<string[]>('/data/columns', { headers: authHeaders(token) });
}

// ─── Queries ─────────────────────────────────────────────────────────────────

export async function queryFrequency(
  token: string,
  query: FrequencyQuery
): Promise<FrequencyResult> {
  return apiFetch<FrequencyResult>('/query/frequency', {
    method: 'POST',
    headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(query)
  });
}

export async function queryMeans(token: string, query: MeansQuery): Promise<MeansResult> {
  return apiFetch<MeansResult>('/query/means', {
    method: 'POST',
    headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(query)
  });
}

// ─── Admin ───────────────────────────────────────────────────────────────────

export async function listUsers(token: string): Promise<User[]> {
  return apiFetch<User[]>('/admin/users', { headers: authHeaders(token) });
}

export async function createUser(token: string, data: UserCreate): Promise<User> {
  return apiFetch<User>('/admin/users', {
    method: 'POST',
    headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

export async function updateUser(token: string, id: number, data: UserUpdate): Promise<User> {
  return apiFetch<User>(`/admin/users/${id}`, {
    method: 'PUT',
    headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

export async function deleteUser(token: string, id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/admin/users/${id}`, {
    method: 'DELETE',
    headers: authHeaders(token)
  });
  if (!res.ok && res.status !== 204) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail ?? detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }
}
