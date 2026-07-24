import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * useMockFetch — shared data-fetching hook for all pages.
 * Wraps any async function (mock today, real API tomorrow) and manages
 * loading / error / data state consistently across the app.
 *
 * @param {Function} apiFn  - The async function to call (from src/api/*.js)
 * @param {Array}    deps   - Dependency array; re-fetches when these change
 * @param {Object}   opts   - Options: { immediate: bool, delay: number }
 * @returns {{ data, loading, error, refetch }}
 */
export function useMockFetch(apiFn, deps = [], opts = {}) {
  const { immediate = true, delay = 0 } = opts;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const apiFnRef = useRef(apiFn);
  apiFnRef.current = apiFn;

  const fetch = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFnRef.current(...args);
      setData(result);
    } catch (err) {
      // TODO(security): When real API is wired, ensure error messages from
      // the backend are sanitised before display — never expose raw stack traces.
      setError(err?.message ?? 'An unexpected error occurred.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!immediate) return;
    let cancelled = false;
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFnRef.current();
        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) {
          setError(err?.message ?? 'An unexpected error occurred.');
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    const timer = delay > 0 ? setTimeout(run, delay) : null;
    if (delay === 0) run();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, refetch: fetch };
}
