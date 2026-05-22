/**
 * WebUI 增强可视化组件
 * 新增功能：实时性能监控、成本预测、智能建议
 */

class EnhancedDashboard {
  constructor() {
    this.metrics = {};
    this.charts = {};
    this.updateInterval = 5000;
  }

  /**
   * 实时性能监控组件
   */
  createPerformanceMonitor() {
    const monitor = {
      cpu: [],
      memory: [],
      tokens: [],
      maxPoints: 20,

      update: function(data) {
        const timestamp = new Date().toLocaleTimeString();
        this.cpu.push({ time: timestamp, value: data.cpu || 0 });
        this.memory.push({ time: timestamp, value: data.memory || 0 });
        this.tokens.push({ time: timestamp, value: data.tokens || 0 });

        if (this.cpu.length > this.maxPoints) {
          this.cpu.shift();
          this.memory.shift();
          this.tokens.shift();
        }
      },

      getTrend: function(arr) {
        if (arr.length < 2) return 0;
        const recent = arr.slice(-5);
        const avg = recent.reduce((a, b) => a + b.value, 0) / recent.length;
        const prev = arr.slice(-10, -5);
        const prevAvg = prev.length ? prev.reduce((a, b) => a + b.value, 0) / prev.length : avg;
        return ((avg - prevAvg) / prevAvg * 100).toFixed(1);
      }
    };
    return monitor;
  }

  /**
   * 成本预测分析
   */
  predictCosts(historicalData) {
    if (historicalData.length < 3) return null;

    // 简单线性回归预测
    const n = historicalData.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;

    historicalData.forEach((d, i) => {
      sumX += i;
      sumY += d.value;
      sumXY += i * d.value;
      sumXX += i * i;
    });

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // 预测下一个时间点
    const nextPrediction = slope * n + intercept;
    const confidence = Math.abs(slope) > 0.1 ? 'high' : 'low';

    return {
      prediction: Math.max(0, nextPrediction),
      trend: slope > 0 ? 'increasing' : 'decreasing',
      confidence: confidence,
      recommendation: this.getCostRecommendation(slope, historicalData[historicalData.length - 1].value)
    };
  }

  getCostRecommendation(trend, currentValue) {
    if (trend > 10) {
      return {
        level: 'warning',
        message: '成本快速上升，建议优化Agent使用策略',
        actions: ['禁用空闲Agent', '压缩记忆存储', '优化提示词长度']
      };
    } else if (trend < -5) {
      return {
        level: 'good',
        message: '成本控制良好，保持当前策略'
      };
    } else {
      return {
        level: 'info',
        message: '成本稳定，定期检查即可'
      };
    }
  }

  /**
   * 智能建议引擎
   */
  generateRecommendations(systemState) {
    const recommendations = [];

    // Token使用优化建议
    if (systemState.avgTokensPerTask > 10000) {
      recommendations.push({
        type: 'optimization',
        priority: 'high',
        title: '优化Token使用',
        description: `平均每任务使用${systemState.avgTokensPerTask}个Token，超过建议值`,
        actions: [
          '启用更高效的模型（Haiku）处理简单任务',
          '压缩提示词，移除冗余上下文',
          '使用记忆缓存减少重复查询'
        ],
        potentialSavings: `${Math.round((systemState.avgTokensPerTask - 5000) * 0.003 * 30)}元/月`
      });
    }

    // Agent活动建议
    const idleAgents = systemState.agents.filter(a => a.status === 'idle');
    if (idleAgents.length > 3) {
      recommendations.push({
        type: 'resource',
        priority: 'medium',
        title: '优化Agent资源配置',
        description: `${idleAgents.length}个Agent处于空闲状态`,
        actions: [
          '禁用长期空闲的Agent',
          '合并相似功能的Agent',
          '启用动态调度机制'
        ],
        potentialSavings: '减少内存占用和维护成本'
      });
    }

    // 性能优化建议
    if (systemState.avgResponseTime > 3000) {
      recommendations.push({
        type: 'performance',
        priority: 'high',
        title: '优化响应速度',
        description: `平均响应时间${systemState.avgResponseTime}ms，影响用户体验`,
        actions: [
          '启用请求缓存',
          '优化数据库查询',
          '使用异步处理'
        ]
      });
    }

    return recommendations;
  }

  /**
   * 创建增强型图表容器
   */
  createEnhancedChartContainer(id, title, subtitle = '') {
    return `
      <div class="enhanced-chart-card" id="${id}-card">
        <div class="chart-header">
          <div class="chart-title-group">
            <h4 class="chart-title">${title}</h4>
            ${subtitle ? `<p class="chart-subtitle">${subtitle}</p>` : ''}
          </div>
          <div class="chart-actions">
            <button class="chart-btn" data-action="refresh">刷新</button>
            <button class="chart-btn" data-action="export">导出</button>
          </div>
        </div>
        <div class="chart-content" id="${id}"></div>
        <div class="chart-footer">
          <span class="chart-status"></span>
          <span class="chart-trend"></span>
        </div>
      </div>
    `;
  }

  /**
   * 3D效果增强
   */
  apply3DEffect(element) {
    element.style.transformStyle = 'preserve-3d';
    element.style.transition = 'transform 0.3s ease';

    element.addEventListener('mousemove', (e) => {
      const rect = element.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = (y - centerY) / 10;
      const rotateY = (centerX - x) / 10;

      element.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    element.addEventListener('mouseleave', () => {
      element.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
    });
  }

  /**
   * 创建实时数据流显示
   */
  createDataStream(containerId, dataSource) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const streamElement = document.createElement('div');
    streamElement.className = 'data-stream';
    container.appendChild(streamElement);

    const updateStream = async () => {
      try {
        const data = await dataSource();
        const items = data.map(item => `
          <div class="stream-item ${item.type || 'info'}">
            <span class="stream-time">${item.time}</span>
            <span class="stream-message">${item.message}</span>
            ${item.value ? `<span class="stream-value">${item.value}</span>` : ''}
          </div>
        `).join('');

        streamElement.innerHTML = items;
        streamElement.scrollTop = streamElement.scrollHeight;
      } catch (error) {
        console.error('Failed to update data stream:', error);
      }
    };

    setInterval(updateStream, 2000);
    updateStream();
  }
}

// CSS样式
const enhancedStyles = `
  .enhanced-chart-card {
    background: linear-gradient(135deg, rgba(20, 30, 50, 0.95), rgba(35, 50, 75, 0.9));
    border: 1px solid rgba(120, 140, 180, 0.2);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    transition: all 0.3s ease;
  }

  .enhanced-chart-card:hover {
    box-shadow: 0 12px 48px rgba(183, 148, 246, 0.2);
    border-color: rgba(183, 148, 246, 0.3);
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .chart-title-group h4 {
    font-size: var(--font-xl);
    font-weight: 600;
    color: var(--text);
    margin: 0;
  }

  .chart-subtitle {
    font-size: var(--font-sm);
    color: var(--text3);
    margin: 4px 0 0 0;
  }

  .chart-actions {
    display: flex;
    gap: 8px;
  }

  .chart-btn {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text2);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: var(--font-sm);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .chart-btn:hover {
    background: var(--accent-gradient);
    color: white;
    border-color: transparent;
  }

  .chart-footer {
    display: flex;
    justify-content: space-between;
    margin-top: 16px;
    font-size: var(--font-sm);
  }

  .chart-status {
    color: var(--text3);
  }

  .chart-trend {
    color: var(--green);
    font-weight: 500;
  }

  .chart-trend.negative {
    color: var(--red);
  }

  .data-stream {
    max-height: 300px;
    overflow-y: auto;
    padding: 12px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: var(--radius-sm);
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: var(--font-sm);
  }

  .stream-item {
    display: flex;
    gap: 12px;
    padding: 8px;
    margin-bottom: 4px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.05);
    transition: all 0.2s ease;
  }

  .stream-item:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .stream-item.info {
    border-left: 3px solid var(--blue);
  }

  .stream-item.success {
    border-left: 3px solid var(--green);
  }

  .stream-item.warning {
    border-left: 3px solid var(--yellow);
  }

  .stream-item.error {
    border-left: 3px solid var(--red);
  }

  .stream-time {
    color: var(--text3);
    font-size: var(--font-xs);
    min-width: 60px;
  }

  .stream-message {
    color: var(--text2);
    flex: 1;
  }

  .stream-value {
    color: var(--accent);
    font-weight: 500;
  }
`;

// 导出
window.EnhancedDashboard = EnhancedDashboard;
window.enhancedStyles = enhancedStyles;
