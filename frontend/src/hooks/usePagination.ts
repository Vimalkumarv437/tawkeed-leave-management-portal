/**
 * usePagination hook for managing table pagination state
 */
import { useState } from 'react';

export interface UsePaginationResult {
  page: number;
  limit: number;
  offset: number;
  total: number;
  totalPages: number;
  setPage: React.Dispatch<React.SetStateAction<number>>;
  setLimit: React.Dispatch<React.SetStateAction<number>>;
  setTotal: React.Dispatch<React.SetStateAction<number>>;
  nextPage: () => void;
  prevPage: () => void;
  goToPage: (p: number) => void;
}

export function usePagination(initialLimit: number = 10): UsePaginationResult {
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [total, setTotal] = useState<number>(0);

  const offset = (page - 1) * limit;
  const totalPages = Math.ceil(total / limit) || 1;

  const nextPage = () => {
    if (page < totalPages) setPage((p) => p + 1);
  };

  const prevPage = () => {
    if (page > 1) setPage((p) => p - 1);
  };

  const goToPage = (p: number) => {
    const target = Math.max(1, Math.min(p, totalPages));
    setPage(target);
  };

  return {
    page,
    limit,
    offset,
    total,
    totalPages,
    setPage,
    setLimit,
    setTotal,
    nextPage,
    prevPage,
    goToPage,
  };
}
