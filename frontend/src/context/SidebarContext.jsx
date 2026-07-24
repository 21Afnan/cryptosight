import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const SIDEBAR_STORAGE_KEY = 'cryptosight_sidebar_collapsed';

export const SIDEBAR_WIDTH = 240;
export const SIDEBAR_COLLAPSED_WIDTH = 76;

const SidebarContext = createContext({
  collapsed: false,
  toggleSidebar: () => {},
  sidebarWidth: SIDEBAR_WIDTH,
});

export function SidebarProvider({ children }) {
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  });

  const toggleSidebar = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
      } catch {
        // ignore
      }
      return next;
    });
  }, []);

  const sidebarWidth = collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;

  const value = useMemo(
    () => ({ collapsed, toggleSidebar, sidebarWidth }),
    [collapsed, toggleSidebar, sidebarWidth]
  );

  return (
    <SidebarContext.Provider value={value}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  return useContext(SidebarContext);
}
