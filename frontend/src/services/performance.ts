/**
 * Real User Monitoring (RUM) - Performance Monitoring Service
 *
 * Tracks frontend performance metrics:
 * - Page load times
 * - API call latency
 * - User interactions
 * - Core Web Vitals (LCP, FID, CLS)
 * - Custom performance marks
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  metadata?: Record<string, any>;
}

interface PageLoadMetrics {
  dns: number;
  tcp: number;
  request: number;
  response: number;
  dom: number;
  load: number;
  ttfb: number; // Time to First Byte
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
}

interface APICallMetric {
  url: string;
  method: string;
  duration: number;
  status: number;
  timestamp: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private apiCalls: APICallMetric[] = [];
  private flushInterval: number = 30000; // 30 seconds
  private flushTimer?: NodeJS.Timeout;
  private apiEndpoint: string = '/api/v1/metrics/rum';

  constructor() {
    if (typeof window !== 'undefined') {
      this.initialize();
    }
  }

  private initialize() {
    // Track page load performance
    if (document.readyState === 'complete') {
      this.trackPageLoad();
    } else {
      window.addEventListener('load', () => this.trackPageLoad());
    }

    // Track Core Web Vitals
    this.trackCoreWebVitals();

    // Track navigation timing
    this.trackNavigationTiming();

    // Track long tasks
    this.trackLongTasks();

    // Start periodic flushing
    this.startFlushTimer();

    // Flush on page unload
    window.addEventListener('beforeunload', () => this.flush());
  }

  /**
   * Track page load performance metrics
   */
  private trackPageLoad() {
    if (!performance.timing) return;

    const timing = performance.timing;
    const navigationStart = timing.navigationStart;

    const metrics: PageLoadMetrics = {
      dns: timing.domainLookupEnd - timing.domainLookupStart,
      tcp: timing.connectEnd - timing.connectStart,
      request: timing.responseStart - timing.requestStart,
      response: timing.responseEnd - timing.responseStart,
      dom: timing.domComplete - timing.domLoading,
      load: timing.loadEventEnd - navigationStart,
      ttfb: timing.responseStart - navigationStart,
      fcp: 0,
      lcp: 0,
    };

    // Track each metric
    Object.entries(metrics).forEach(([key, value]) => {
      if (value > 0) {
        this.track(`page_load_${key}`, value);
      }
    });
  }

  /**
   * Track Core Web Vitals using PerformanceObserver
   */
  private trackCoreWebVitals() {
    // Largest Contentful Paint (LCP)
    try {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        this.track('web_vital_lcp', lastEntry.renderTime || lastEntry.loadTime);
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      // LCP not supported
    }

    // First Input Delay (FID)
    try {
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          this.track('web_vital_fid', entry.processingStart - entry.startTime);
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
    } catch (e) {
      // FID not supported
    }

    // Cumulative Layout Shift (CLS)
    try {
      let clsScore = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsScore += entry.value;
          }
        });
        this.track('web_vital_cls', clsScore);
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (e) {
      // CLS not supported
    }
  }

  /**
   * Track navigation timing (SPA route changes)
   */
  private trackNavigationTiming() {
    // Monitor history changes for SPA navigation
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    const self = this;

    history.pushState = function (...args) {
      self.track('spa_navigation', performance.now());
      return originalPushState.apply(this, args);
    };

    history.replaceState = function (...args) {
      self.track('spa_navigation', performance.now());
      return originalReplaceState.apply(this, args);
    };

    window.addEventListener('popstate', () => {
      self.track('spa_navigation', performance.now());
    });
  }

  /**
   * Track long tasks (>50ms) that block the main thread
   */
  private trackLongTasks() {
    try {
      const longTaskObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          this.track('long_task', entry.duration, {
            name: entry.name,
            startTime: entry.startTime,
          });
        });
      });
      longTaskObserver.observe({ entryTypes: ['longtask'] });
    } catch (e) {
      // Long tasks not supported
    }
  }

  /**
   * Track custom performance metric
   */
  public track(name: string, value: number, metadata?: Record<string, any>) {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      metadata,
    };

    this.metrics.push(metric);

    // Flush if buffer is getting large
    if (this.metrics.length >= 100) {
      this.flush();
    }
  }

  /**
   * Track API call performance
   */
  public trackAPICall(
    url: string,
    method: string,
    duration: number,
    status: number
  ) {
    this.apiCalls.push({
      url,
      method,
      duration,
      status,
      timestamp: Date.now(),
    });

    // Also track as general metric
    this.track('api_call_duration', duration, {
      url,
      method,
      status,
    });
  }

  /**
   * Mark start of custom performance measurement
   */
  public markStart(name: string) {
    if (performance.mark) {
      performance.mark(`${name}-start`);
    }
  }

  /**
   * Mark end of custom performance measurement and track duration
   */
  public markEnd(name: string) {
    if (performance.mark && performance.measure) {
      performance.mark(`${name}-end`);
      try {
        performance.measure(name, `${name}-start`, `${name}-end`);
        const measure = performance.getEntriesByName(name)[0];
        this.track(`custom_${name}`, measure.duration);
      } catch (e) {
        // Measurement failed
      }
    }
  }

  /**
   * Track user interaction timing
   */
  public trackInteraction(name: string, duration: number) {
    this.track(`interaction_${name}`, duration);
  }

  /**
   * Track React component render time
   */
  public trackComponentRender(componentName: string, duration: number) {
    this.track(`render_${componentName}`, duration);
  }

  /**
   * Flush metrics to backend
   */
  private async flush() {
    if (this.metrics.length === 0 && this.apiCalls.length === 0) {
      return;
    }

    const payload = {
      metrics: [...this.metrics],
      api_calls: [...this.apiCalls],
      user_agent: navigator.userAgent,
      url: window.location.href,
      timestamp: Date.now(),
    };

    // Clear buffers
    this.metrics = [];
    this.apiCalls = [];

    // Send to backend (use sendBeacon for reliability)
    if (navigator.sendBeacon) {
      navigator.sendBeacon(
        this.apiEndpoint,
        JSON.stringify(payload)
      );
    } else {
      // Fallback to fetch
      try {
        await fetch(this.apiEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          keepalive: true,
        });
      } catch (e) {
        console.error('Failed to send performance metrics:', e);
      }
    }
  }

  /**
   * Start periodic flushing
   */
  private startFlushTimer() {
    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.flushInterval);
  }

  /**
   * Stop monitoring
   */
  public stop() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flush();
  }

  /**
   * Get current metrics (for debugging)
   */
  public getMetrics(): PerformanceMetric[] {
    return [...this.metrics];
  }

  /**
   * Get performance summary
   */
  public getSummary(): Record<string, any> {
    const summary: Record<string, any> = {};

    this.metrics.forEach((metric) => {
      if (!summary[metric.name]) {
        summary[metric.name] = {
          count: 0,
          total: 0,
          min: Infinity,
          max: -Infinity,
        };
      }

      const stat = summary[metric.name];
      stat.count++;
      stat.total += metric.value;
      stat.min = Math.min(stat.min, metric.value);
      stat.max = Math.max(stat.max, metric.value);
      stat.avg = stat.total / stat.count;
    });

    return summary;
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Export React hook for component performance tracking
export function usePerformanceTracking(componentName: string) {
  const startTime = performance.now();

  return () => {
    const duration = performance.now() - startTime;
    performanceMonitor.trackComponentRender(componentName, duration);
  };
}

// Export utility for API call tracking
export function trackAPICall(
  url: string,
  method: string,
  duration: number,
  status: number
) {
  performanceMonitor.trackAPICall(url, method, duration, status);
}

// Export for custom measurements
export { PerformanceMonitor };
export default performanceMonitor;
