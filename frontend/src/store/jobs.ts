import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { SortingState, VisibilityState } from '@tanstack/react-table';

interface JobFilters {
  status?: string;
  query?: string;
}

interface JobsState {
  sorting: SortingState;
  columnVisibility: VisibilityState;
  filters: JobFilters;
  setSorting: (sorting: SortingState) => void;
  setColumnVisibility: (visibility: VisibilityState) => void;
  setFilters: (filters: JobFilters) => void;
  updateFilters: (updates: Partial<JobFilters>) => void;
}

export const useJobStore = create<JobsState>()(
  persist(
    (set) => ({
      sorting: [{ id: 'last_updated_at', desc: true }],
      columnVisibility: {},
      filters: {},
      setSorting: (sorting) => set({ sorting }),
      setColumnVisibility: (columnVisibility) => set({ columnVisibility }),
      setFilters: (filters) => set({ filters }),
      updateFilters: (updates) => set((state) => ({ filters: { ...state.filters, ...updates } })),
    }),
    {
      name: 'cw-jobs-state',
    }
  )
);
