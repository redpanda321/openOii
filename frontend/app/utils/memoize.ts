/**
 * 简单的记忆化函数，缓存函数结果
 * @param fn 要记忆化的函数
 * @returns 记忆化后的函数
 */
export function memoize<T extends (...args: unknown[]) => unknown>(
  fn: T
): T {
  const cache = new Map<string, ReturnType<T>>();

  return ((...args: Parameters<T>) => {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key);
    }

    const result = fn(...args) as ReturnType<T>;
    cache.set(key, result);

    // 限制缓存大小，防止内存泄漏
    if (cache.size > 100) {
      const firstKey = cache.keys().next().value;
      if (firstKey !== undefined) cache.delete(firstKey);
    }

    return result;
  }) as T;
}

/**
 * 带过期时间的记忆化函数
 * @param fn 要记忆化的函数
 * @param ttl 缓存过期时间（毫秒）
 * @returns 记忆化后的函数
 */
export function memoizeWithTTL<T extends (...args: unknown[]) => unknown>(
  fn: T,
  ttl: number
): T {
  const cache = new Map<string, { value: ReturnType<T>; expiry: number }>();

  return ((...args: Parameters<T>) => {
    const key = JSON.stringify(args);
    const now = Date.now();

    const cached = cache.get(key);
    if (cached && cached.expiry > now) {
      return cached.value;
    }

    const result = fn(...args) as ReturnType<T>;
    cache.set(key, { value: result, expiry: now + ttl });

    // 清理过期缓存
    for (const [k, v] of cache.entries()) {
      if (v.expiry <= now) {
        cache.delete(k);
      }
    }

    return result;
  }) as T;
}
