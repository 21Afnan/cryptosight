import React, { createContext, useContext, useState, useCallback } from 'react';

const SearchContext = createContext({ query: '', setQuery: () => {} });

export function SearchProvider({ children }) {
  const [query, setQuery] = useState('');
  const clear = useCallback(() => setQuery(''), []);
  return (
    <SearchContext.Provider value={{ query, setQuery, clear }}>
      {children}
    </SearchContext.Provider>
  );
}

export function useSearch() {
  return useContext(SearchContext);
}
