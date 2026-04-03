import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  id: number;
  name: string;
  symbols: string[];
}

export interface MarketStatus {
  isOpen: boolean;
  nifty: { price: number; change: number; pctChange: number } | null;
  bankNifty: { price: number; change: number; pctChange: number } | null;
  lastUpdated: number | null;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

// ─── Store slices ─────────────────────────────────────────────────────────────

interface SymbolSlice {
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
  symbolHistory: string[];
  addToHistory: (symbol: string) => void;
}

interface WatchlistSlice {
  watchlists: WatchlistItem[];
  activeWatchlistId: number | null;
  setWatchlists: (watchlists: WatchlistItem[]) => void;
  setActiveWatchlist: (id: number | null) => void;
  addSymbolToWatchlist: (watchlistId: number, symbol: string) => void;
  removeSymbolFromWatchlist: (watchlistId: number, symbol: string) => void;
}

interface MarketSlice {
  marketStatus: MarketStatus;
  setMarketStatus: (status: Partial<MarketStatus>) => void;
}

interface ConnectionSlice {
  connectionStatus: ConnectionStatus;
  setConnectionStatus: (status: ConnectionStatus) => void;
}

interface ThemeSlice {
  darkMode: boolean;
  toggleDarkMode: () => void;
}

interface ActiveTabSlice {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

type Store = SymbolSlice &
  WatchlistSlice &
  MarketSlice &
  ConnectionSlice &
  ThemeSlice &
  ActiveTabSlice;

// ─── Store ────────────────────────────────────────────────────────────────────

export const useStore = create<Store>()(
  persist(
    (set) => ({
      // Symbol
      selectedSymbol: 'RELIANCE',
      setSelectedSymbol: (symbol) =>
        set((state) => {
          const upper = symbol.toUpperCase();
          return {
            selectedSymbol: upper,
            symbolHistory: [
              upper,
              ...state.symbolHistory.filter((s) => s !== upper),
            ].slice(0, 20),
          };
        }),
      symbolHistory: ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY'],
      addToHistory: (symbol) =>
        set((state) => ({
          symbolHistory: [
            symbol,
            ...state.symbolHistory.filter((s) => s !== symbol),
          ].slice(0, 20),
        })),

      // Watchlists
      watchlists: [],
      activeWatchlistId: null,
      setWatchlists: (watchlists) => set({ watchlists }),
      setActiveWatchlist: (id) => set({ activeWatchlistId: id }),
      addSymbolToWatchlist: (watchlistId, symbol) =>
        set((state) => ({
          watchlists: state.watchlists.map((wl) =>
            wl.id === watchlistId && !wl.symbols.includes(symbol)
              ? { ...wl, symbols: [...wl.symbols, symbol] }
              : wl,
          ),
        })),
      removeSymbolFromWatchlist: (watchlistId, symbol) =>
        set((state) => ({
          watchlists: state.watchlists.map((wl) =>
            wl.id === watchlistId
              ? { ...wl, symbols: wl.symbols.filter((s) => s !== symbol) }
              : wl,
          ),
        })),

      // Market status
      marketStatus: {
        isOpen: false,
        nifty: null,
        bankNifty: null,
        lastUpdated: null,
      },
      setMarketStatus: (update) =>
        set((state) => ({
          marketStatus: { ...state.marketStatus, ...update },
        })),

      // Connection
      connectionStatus: 'disconnected',
      setConnectionStatus: (status) => set({ connectionStatus: status }),

      // Theme — persist preference
      darkMode: true,
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),

      // Active tab
      activeTab: 'dashboard',
      setActiveTab: (tab) => set({ activeTab: tab }),
    }),
    {
      name: 'fingraph-store',
      // Only persist user preferences and history, not live market data
      partialize: (state) => ({
        selectedSymbol: state.selectedSymbol,
        symbolHistory: state.symbolHistory,
        activeWatchlistId: state.activeWatchlistId,
        darkMode: state.darkMode,
        activeTab: state.activeTab,
      }),
    },
  ),
);

// ─── Convenience selectors ────────────────────────────────────────────────────

export const useSelectedSymbol = () => useStore((s) => s.selectedSymbol);
export const useSetSelectedSymbol = () => useStore((s) => s.setSelectedSymbol);
export const useActiveTab = () => useStore((s) => s.activeTab);
export const useSetActiveTab = () => useStore((s) => s.setActiveTab);
export const useWatchlists = () => useStore((s) => s.watchlists);
export const useMarketStatus = () => useStore((s) => s.marketStatus);
export const useConnectionStatus = () => useStore((s) => s.connectionStatus);
