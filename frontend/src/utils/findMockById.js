/**
 * findMockById.js
 * Shared utility for safe, type-coerced lookup of items by ID from any mock array.
 * Eliminates route-param string vs integer / ID key mismatch bugs across all detail pages.
 *
 * @param {Array}          list     - Array of mock objects
 * @param {string|number}  targetId - ID passed from route or caller
 * @param {Array<string>}  customKeys - Optional list of ID keys to check
 * @returns {Object|null}
 */
export function findMockById(list, targetId, customKeys = []) {
  if (!Array.isArray(list) || targetId == null || targetId === '') {
    return null;
  }

  const targetStr = String(targetId).trim().toLowerCase();

  return list.find((item) => {
    if (!item || typeof item !== 'object') return false;

    // Always clone customKeys so we never mutate the input parameter
    const keysToCheck = customKeys.length > 0
      ? [...customKeys]
      : ['id', 'backtest_id', 'strategy_id', 'execution_id', 'model_id', 'wallet_id'];

    // Also include any key on the object that ends with '_id' or equals 'id'
    const itemKeys = Object.keys(item);
    for (const key of itemKeys) {
      if (key === 'id' || key.endsWith('_id')) {
        if (!keysToCheck.includes(key)) {
          keysToCheck.push(key);
        }
      }
    }

    for (const key of keysToCheck) {
      const val = item[key];
      if (val != null && String(val).trim().toLowerCase() === targetStr) {
        return true;
      }
    }

    return false;
  }) ?? null;
}
