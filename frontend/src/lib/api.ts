const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';
export const ENDPOINTS = {
  members: '/members',
  books: '/books',
  loans: '/loans',
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${API_PREFIX}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface Member {
  id: string;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  membership_date: string;
  is_active: boolean;
  active_loans: number;
  created_at: string;
  updated_at: string;
}

export interface Book {
  id: string;
  title: string;
  author: string;
  isbn?: string;
  genre?: string;
  publisher?: string;
  published_year?: number;
  total_copies: number;
  available_copies: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Loan {
  id: string;
  member_id: string;
  book_id: string;
  borrowed_at: string;
  due_date: string;
  returned_at?: string;
  fine_amount: string;
  fine_paid: boolean;
  notes?: string;
  member_name?: string;
  book_title?: string;
  book_author?: string;
  created_at: string;
  updated_at: string;
}

export interface PagedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface LibraryStats {
  total_books: number;
  total_members: number;
  active_loans: number;
  overdue_loans: number;
  total_fines: string;
}

// ── Members ──────────────────────────────────────────────────────────────────

export const membersApi = {
  list: (params?: { page?: number; size?: number; search?: string; active_only?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set('page', String(params.page));
    if (params?.size) q.set('size', String(params.size));
    if (params?.search) q.set('search', params.search);
    if (params?.active_only) q.set('active_only', 'true');
    return apiFetch<PagedResponse<Member>>(`/members?${q}`);
  },
  get: (id: string) => apiFetch<Member>(`/members/${id}`),
  create: (data: Partial<Member>) =>
    apiFetch<Member>('/members', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<Member>) =>
    apiFetch<Member>(`/members/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => apiFetch<void>(`/members/${id}`, { method: 'DELETE' }),
};

// ── Books ─────────────────────────────────────────────────────────────────────

export const booksApi = {
  list: (params?: { page?: number; size?: number; search?: string; genre?: string; available_only?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set('page', String(params.page));
    if (params?.size) q.set('size', String(params.size));
    if (params?.search) q.set('search', params.search);
    if (params?.genre) q.set('genre', params.genre);
    if (params?.available_only) q.set('available_only', 'true');
    return apiFetch<PagedResponse<Book>>(`/books?${q}`);
  },
  get: (id: string) => apiFetch<Book>(`/books/${id}`),
  create: (data: Partial<Book>) =>
    apiFetch<Book>('/books', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<Book>) =>
    apiFetch<Book>(`/books/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => apiFetch<void>(`/books/${id}`, { method: 'DELETE' }),
};

// ── Loans ─────────────────────────────────────────────────────────────────────

export const loansApi = {
  list: (params?: { page?: number; size?: number; member_id?: string; book_id?: string; active_only?: boolean; overdue_only?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set('page', String(params.page));
    if (params?.size) q.set('size', String(params.size));
    if (params?.member_id) q.set('member_id', params.member_id);
    if (params?.book_id) q.set('book_id', params.book_id);
    if (params?.active_only) q.set('active_only', 'true');
    if (params?.overdue_only) q.set('overdue_only', 'true');
    return apiFetch<PagedResponse<Loan>>(`/loans?${q}`);
  },
  get: (id: string) => apiFetch<Loan>(`/loans/${id}`),
  borrow: (data: { member_id: string; book_id: string; notes?: string }) =>
    apiFetch<Loan>('/loans', { method: 'POST', body: JSON.stringify(data) }),
  return: (id: string, notes?: string) =>
    apiFetch<Loan>(`/loans/${id}/return`, { method: 'POST', body: JSON.stringify({ notes }) }),
  payFine: (id: string) =>
    apiFetch<Loan>(`/loans/${id}/pay-fine`, { method: 'POST', body: '{}' }),
  stats: () => apiFetch<LibraryStats>('/loans/stats'),
};
