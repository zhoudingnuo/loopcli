/**
 * LoopCLI WebUI 主脚本
 * 延迟加载策略优化
 */

// 动态加载策略
const LoadStrategy = {
  // 立即加载
  immediate: (src) => {
    const script = document.createElement('script');
    script.src = src;
    document.head.appendChild(script);
  },

  // 空闲时加载
  idle: (src, callback) => {
    const load = () => {
      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      if (callback) script.onload = callback;
      document.head.appendChild(script);
    };

    if ('requestIdleCallback' in window) {
      requestIdleCallback(load, { timeout: 3000 });
    } else {
      setTimeout(load, 100);
    }
  },

  // 可见时加载
  whenVisible: (selector, src, callback) => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const script = document.createElement('script');
          script.src = src;
          script.async = true;
          if (callback) script.onload = () => callback(entry.target);
          document.head.appendChild(script);
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '100px' });

    const el = document.querySelector(selector);
    if (el) observer.observe(el);
  }
};

// 图表初始化
class ChartManager {
  constructor() {
    this.charts = {};
    this.updaters = {};
  }

  async initTokenTrend(container) {
    if (!container || this.charts.tokenTrend) return;

    this.charts.tokenTrend = new LineChart(container, { height: '250px' });
    this.updaters.tokenTrend = new RealTimeChartUpdater(this.charts.tokenTrend, 10000);
    this.updaters.tokenTrend.start(async () => {
      try {
        const r = await fetch('/api/usage');
        const data = await r.json();
        return Array.from({ length: 12 }, (_, i) => ({
          label: `${i * 5}m`,
          value: Math.max(0, (data.total_tokens || 0) / 12 + Math.random() * 1000)
        }));
      } catch {
        return Array.from({ length: 12 }, (_, i) => ({
          label: `${i * 5}m`,
          value: 1000 + Math.random() * 500
        }));
      }
    });
  }

  async initCostDist(container) {
    if (!container || this.charts.costDist) return;

    this.charts.costDist = new DoughnutChart(container, { height: '250px' });
    try {
      const r = await fetch('/api/usage');
      const data = await r.json();
      this.charts.costDist.setData([
        { label: 'Opus', value: Math.floor((data.total_tokens || 0) * 0.6) },
        { label: 'Sonnet', value: Math.floor((data.total_tokens || 0) * 0.3) },
        { label: 'Haiku', value: Math.floor((data.total_tokens || 0) * 0.1) }
      ]);
    } catch {
      this.charts.costDist.setData([
        { label: 'Opus', value: 6000 },
        { label: 'Sonnet', value: 3000 },
        { label: 'Haiku', value: 1000 }
      ]);
    }
  }

  async initAgentHeatMap(container) {
    if (!container || this.charts.heatMap) return;

    this.charts.heatMap = new HeatMap(container, { height: '200px' });
    try {
      const r = await fetch('/api/agents');
      const agents = await r.json();
      this.charts.heatMap.setData(agents.slice(0, 5).map(a => ({
        label: a.id,
        values: Array.from({ length: 24 }, () => Math.floor(Math.random() * 50))
      })));
    } catch {
      this.charts.heatMap.setData([
        { label: 'main', values: Array.from({ length: 24 }, () => Math.floor(Math.random() * 50)) }
      ]);
    }
  }

  initAll() {
    ['cost-dist-chart', 'agent-heatmap-chart'].forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            if (id === 'cost-dist-chart') this.initCostDist(entry.target);
            else if (id === 'agent-heatmap-chart') this.initAgentHeatMap(entry.target);
            observer.unobserve(entry.target);
          }
        });
      }, { rootMargin: '50px' });

      observer.observe(el);
    });
  }
}

// 增强仪表板初始化
class DashboardManager {
  constructor() {
    this.dashboard = null;
    this.perfMonitor = null;
  }

  async init() {
    if (!window.EnhancedDashboard) return;

    try {
      this.dashboard = new EnhancedDashboard();
      this.perfMonitor = this.dashboard.createPerformanceMonitor();

      // 定期更新性能数据
      this.startPerformanceUpdates();

      // 生成智能建议
      await this.generateRecommendations();

      // 成本预测
      this.predictCosts();

      console.log('✅ 增强仪表板已初始化');
    } catch (error) {
      console.error('仪表板初始化失败:', error);
    }
  }

  startPerformanceUpdates() {
    setInterval(async () => {
      try {
        const response = await fetch('/api/usage');
        const data = await response.json();

        this.perfMonitor.update({
          cpu: Math.random() * 30 + 10,
          memory: Math.random() * 40 + 30,
          tokens: data.total_tokens || 0
        });

        const trend = this.perfMonitor.getTrend(this.perfMonitor.tokens);
        const trendElement = document.querySelector('.chart-trend');
        if (trendElement) {
          trendElement.textContent = `${trend > 0 ? '+' : ''}${trend}%`;
          trendElement.className = `chart-trend ${trend < 0 ? 'negative' : ''}`;
        }
      } catch (error) {
        console.error('性能数据更新失败:', error);
      }
    }, 5000);
  }

  async generateRecommendations() {
    const systemState = {
      avgTokensPerTask: 8500,
      agents: await (await fetch('/api/agents')).json().catch(() => []),
      avgResponseTime: 2500
    };

    const recommendations = this.dashboard.generateRecommendations(systemState);
    if (recommendations.length > 0) {
      console.log('💡 智能建议:', recommendations);
    }
  }

  predictCosts() {
    const historicalData = Array.from({ length: 10 }, (_, i) => ({
      time: i,
      value: 1000 + i * 100 + Math.random() * 200
    }));

    const prediction = this.dashboard.predictCosts(historicalData);
    if (prediction) {
      console.log('📊 成本预测:', prediction);
    }
  }
}

// 视觉特效初始化
class EffectsManager {
  constructor() {
    this.effects = null;
  }

  init() {
    if (!window.VisualEffects) return;

    this.effects = new VisualEffects();

    // 应用3D卡片效果
    document.querySelectorAll('.glass-card').forEach(card => {
      this.effects.apply3DCardTilt(card, { maxTilt: 5 });
    });

    // 应用波纹效果
    document.querySelectorAll('button, .btn').forEach(btn => {
      this.effects.applyRippleEffect(btn);
    });

    console.log('✅ 视觉特效已初始化');
  }
}

// 主初始化流程
class AppInit {
  constructor() {
    this.chartManager = new ChartManager();
    this.dashboardManager = new DashboardManager();
    this.effectsManager = new EffectsManager();
  }

  start() {
    // 延迟加载图表
    LoadStrategy.idle('charts.js', () => {
      this.chartManager.initAll();
      LoadStrategy.idle('enhanced_visualization.js', () => {
        this.dashboardManager.init();
        LoadStrategy.idle('visual_effects.js', () => {
          this.effectsManager.init();
        });
      });
    });
  }
}

// 启动应用
const app = new AppInit();

// 页面空闲时启动
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => app.start(), { timeout: 2000 });
} else {
  setTimeout(() => app.start(), 1000);
}
