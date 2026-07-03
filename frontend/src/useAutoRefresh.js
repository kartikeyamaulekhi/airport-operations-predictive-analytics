import { useEffect, useRef, useCallback } from 'react';

/**
 * Calls `fn` immediately, then every `intervalMs` milliseconds.
 * Cleans up on unmount. This is the "no human needed" automation hook.
 */
export function useAutoRefresh(fn, intervalMs = 5 * 60 * 1000) {
  const fnRef = useRef(fn);
  useEffect(() => { fnRef.current = fn; }, [fn]);

  const run = useCallback(() => fnRef.current(), []);

  useEffect(() => {
    run();
    const id = setInterval(run, intervalMs);
    return () => clearInterval(id);
  }, [run, intervalMs]);
}
