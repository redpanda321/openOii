/**
 * Web Vitals 性能监控
 * 监控核心 Web 指标：LCP, FID, CLS, FCP, TTFB
 */

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

type MetricCallback = (metric: PerformanceMetric) => void;

// 性能阈值（基于 Google 推荐）
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 },
  FID: { good: 100, poor: 300 },
  CLS: { good: 0.1, poor: 0.25 },
  FCP: { good: 1800, poor: 3000 },
  TTFB: { good: 800, poor: 1800 },
};

function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS];
  if (!threshold) return 'good';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
}

/**
 * 监控 Largest Contentful Paint (LCP)
 * 最大内容绘制时间
 */
export function observeLCP(callback: MetricCallback) {
  if (!('PerformanceObserver' in window)) return;

  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1] as PerformanceEntry & { renderTime?: number; loadTime?: number };

      const value = lastEntry.renderTime || lastEntry.loadTime || 0;
      callback({
        name: 'LCP',
        value,
        rating: getRating('LCP', value),
        timestamp: Date.now(),
      });
    });

    observer.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {
    console.warn('LCP observation failed:', e);
  }
}

/**
 * 监控 First Input Delay (FID)
 * 首次输入延迟
 */
export function observeFID(callback: MetricCallback) {
  if (!('PerformanceObserver' in window)) return;

  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        const fidEntry = entry as PerformanceEntry & { processingStart?: number };
        const value = fidEntry.processingStart ? fidEntry.processingStart - entry.startTime : 0;

        callback({
          name: 'FID',
          value,
          rating: getRating('FID', value),
          timestamp: Date.now(),
        });
      });
    });

    observer.observe({ type: 'first-input', buffered: true });
  } catch (e) {
    console.warn('FID observation failed:', e);
  }
}

/**
 * 监控 Cumulative Layout Shift (CLS)
 * 累积布局偏移
 */
export function observeCLS(callback: MetricCallback) {
  if (!('PerformanceObserver' in window)) return;

  let clsValue = 0;

  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        const layoutShift = entry as PerformanceEntry & { hadRecentInput?: boolean; value?: number };
        if (!layoutShift.hadRecentInput) {
          clsValue += layoutShift.value || 0;
        }
      });

      callback({
        name: 'CLS',
        value: clsValue,
        rating: getRating('CLS', clsValue),
        timestamp: Date.now(),
      });
    });

    observer.observe({ type: 'layout-shift', buffered: true });
  } catch (e) {
    console.warn('CLS observation failed:', e);
  }
}

/**
 * 监控 First Contentful Paint (FCP)
 * 首次内容绘制
 */
export function observeFCP(callback: MetricCallback) {
  if (!('PerformanceObserver' in window)) return;

  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.name === 'first-contentful-paint') {
          callback({
            name: 'FCP',
            value: entry.startTime,
            rating: getRating('FCP', entry.startTime),
            timestamp: Date.now(),
          });
        }
      });
    });

    observer.observe({ type: 'paint', buffered: true });
  } catch (e) {
    console.warn('FCP observation failed:', e);
  }
}

/**
 * 监控 Time to First Byte (TTFB)
 * 首字节时间
 */
export function observeTTFB(callback: MetricCallback) {
  if (!('performance' in window) || !performance.timing) return;

  try {
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (navigationEntry) {
      const value = navigationEntry.responseStart - navigationEntry.requestStart;
      callback({
        name: 'TTFB',
        value,
        rating: getRating('TTFB', value),
        timestamp: Date.now(),
      });
    }
  } catch (e) {
    console.warn('TTFB observation failed:', e);
  }
}

/**
 * 初始化所有性能监控
 */
export function initPerformanceMonitoring(callback: MetricCallback) {
  observeLCP(callback);
  observeFID(callback);
  observeCLS(callback);
  observeFCP(callback);
  observeTTFB(callback);
}

/**
 * 发送性能指标到分析服务
 * 可以集成 Google Analytics, Sentry 等
 */
export function reportPerformanceMetrics(metric: PerformanceMetric) {
  // 开发环境打印到控制台
  if (import.meta.env.DEV) {
    console.log(`[Performance] ${metric.name}:`, {
      value: `${metric.value.toFixed(2)}ms`,
      rating: metric.rating,
    });
  }

  // 生产环境发送到分析服务
  // 示例：发送到 Google Analytics
  if (typeof window !== 'undefined' && 'gtag' in window) {
    (window as unknown as { gtag: (...args: unknown[]) => void }).gtag('event', metric.name, {
      value: Math.round(metric.value),
      metric_rating: metric.rating,
      event_category: 'Web Vitals',
    });
  }

  // 示例：发送到自定义分析端点
  if (import.meta.env.PROD) {
    navigator.sendBeacon?.(
      '/api/analytics/performance',
      JSON.stringify(metric)
    );
  }
}
