/**
 * LoopCLI WebUI 数据可视化组件
 * 特性：实时图表、Token趋势、Agent活动热力图
 */

class ChartComponent {
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;
    this.options = {
      width: '100%',
      height: '300px',
      theme: 'dark',
      animation: true,
      ...options
    };
    this.data = [];
    this.init();
  }

  init() {
    this.canvas = document.createElement('canvas');
    this.canvas.width = this.container.offsetWidth || 600;
    this.canvas.height = parseInt(this.options.height) || 300;
    this.canvas.style.width = this.options.width;
    this.canvas.style.height = this.options.height;
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
  }

  setData(data) {
    this.data = data;
    this.render();
  }

  render() {
    // 子类实现
  }

  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  getColor(value, alpha = 1) {
    const colors = {
      primary: `rgba(167, 139, 250, ${alpha})`,
      secondary: `rgba(244, 114, 182, ${alpha})`,
      accent: `rgba(56, 189, 248, ${alpha})`,
      success: `rgba(0, 230, 118, ${alpha})`,
      warning: `rgba(255, 193, 7, ${alpha})`,
      error: `rgba(255, 82, 82, ${alpha})`
    };
    return colors[value] || colors.primary;
  }
}

/**
 * 折线图 - 用于Token使用趋势
 */
class LineChart extends ChartComponent {
  render() {
    this.clear();
    if (this.data.length === 0) return;

    const padding = 40;
    const chartWidth = this.canvas.width - padding * 2;
    const chartHeight = this.canvas.height - padding * 2;

    // 计算数据范围
    const values = this.data.map(d => d.value);
    const maxVal = Math.max(...values) * 1.1;
    const minVal = Math.min(...values) * 0.9;
    const range = maxVal - minVal || 1;

    // 绘制网格
    this.drawGrid(padding, chartWidth, chartHeight, maxVal, minVal);

    // 绘制线条
    this.ctx.beginPath();
    this.ctx.strokeStyle = this.getColor('primary');
    this.ctx.lineWidth = 3;
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';

    const points = this.data.map((d, i) => ({
      x: padding + (i / (this.data.length - 1)) * chartWidth,
      y: padding + chartHeight - ((d.value - minVal) / range) * chartHeight
    }));

    this.ctx.moveTo(points[0].x, points[0].y);

    // 使用贝塞尔曲线平滑连接
    for (let i = 1; i < points.length; i++) {
      const xc = (points[i].x + points[i - 1].x) / 2;
      const yc = (points[i].y + points[i - 1].y) / 2;
      this.ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
    }
    this.ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    this.ctx.stroke();

    // 绘制渐变填充
    const gradient = this.ctx.createLinearGradient(0, padding, 0, this.canvas.height - padding);
    gradient.addColorStop(0, this.getColor('primary', 0.3));
    gradient.addColorStop(1, this.getColor('primary', 0));

    this.ctx.lineTo(points[points.length - 1].x, this.canvas.height - padding);
    this.ctx.lineTo(points[0].x, this.canvas.height - padding);
    this.ctx.closePath();
    this.ctx.fillStyle = gradient;
    this.ctx.fill();

    // 绘制数据点
    points.forEach((point, i) => {
      this.ctx.beginPath();
      this.ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
      this.ctx.fillStyle = this.getColor('accent');
      this.ctx.fill();
      this.ctx.strokeStyle = '#fff';
      this.ctx.lineWidth = 2;
      this.ctx.stroke();

      // 绘制数值标签
      this.ctx.fillStyle = this.options.theme === 'dark' ? '#fff' : '#333';
      this.ctx.font = '11px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(
        this.data[i].value.toLocaleString(),
        point.x,
        point.y - 10
      );
    });
  }

  drawGrid(padding, chartWidth, chartHeight, maxVal, minVal) {
    this.ctx.strokeStyle = this.options.theme === 'dark'
      ? 'rgba(255, 255, 255, 0.1)'
      : 'rgba(0, 0, 0, 0.1)';
    this.ctx.lineWidth = 1;

    // 水平线
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight / 5) * i;
      this.ctx.beginPath();
      this.ctx.moveTo(padding, y);
      this.ctx.lineTo(padding + chartWidth, y);
      this.ctx.stroke();

      // Y轴标签
      const value = maxVal - ((maxVal - minVal) / 5) * i;
      this.ctx.fillStyle = this.options.theme === 'dark' ? '#888' : '#666';
      this.ctx.font = '10px sans-serif';
      this.ctx.textAlign = 'right';
      this.ctx.fillText(
        Math.round(value).toLocaleString(),
        padding - 10,
        y + 4
      );
    }
  }
}

/**
 * 圆环图 - 用于成本分布
 */
class DoughnutChart extends ChartComponent {
  render() {
    this.clear();
    if (this.data.length === 0) return;

    const centerX = this.canvas.width / 2;
    const centerY = this.canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 40;
    const innerRadius = radius * 0.6;

    const total = this.data.reduce((sum, d) => sum + d.value, 0);
    let startAngle = -Math.PI / 2;

    const colors = ['primary', 'secondary', 'accent', 'success', 'warning', 'error'];

    this.data.forEach((item, i) => {
      const sliceAngle = (item.value / total) * Math.PI * 2;
      const endAngle = startAngle + sliceAngle;

      // 绘制扇形
      this.ctx.beginPath();
      this.ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      this.ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
      this.ctx.closePath();
      this.ctx.fillStyle = this.getColor(colors[i % colors.length]);
      this.ctx.fill();

      // 绘制标签
      const midAngle = startAngle + sliceAngle / 2;
      const labelRadius = radius + 20;
      const labelX = centerX + Math.cos(midAngle) * labelRadius;
      const labelY = centerY + Math.sin(midAngle) * labelRadius;

      this.ctx.fillStyle = this.options.theme === 'dark' ? '#fff' : '#333';
      this.ctx.font = '11px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(item.label, labelX, labelY);
      this.ctx.font = '10px sans-serif';
      this.ctx.fillStyle = this.options.theme === 'dark' ? '#888' : '#666';
      this.ctx.fillText(
        `${((item.value / total) * 100).toFixed(1)}%`,
        labelX,
        labelY + 12
      );

      startAngle = endAngle;
    });

    // 中心文字
    this.ctx.fillStyle = this.options.theme === 'dark' ? '#fff' : '#333';
    this.ctx.font = 'bold 16px sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText('总计', centerX, centerY - 10);
    this.ctx.font = '14px sans-serif';
    this.ctx.fillStyle = this.getColor('accent');
    this.ctx.fillText(total.toLocaleString(), centerX, centerY + 10);
  }
}

/**
 * 热力图 - 用于Agent活动
 */
class HeatMap extends ChartComponent {
  render() {
    this.clear();
    if (this.data.length === 0) return;

    const padding = 40;
    const cellWidth = (this.canvas.width - padding * 2) / this.data[0].values.length;
    const cellHeight = (this.canvas.height - padding * 2) / this.data.length;

    // 找到最大值用于颜色映射
    const allValues = this.data.flatMap(d => d.values);
    const maxVal = Math.max(...allValues);

    this.data.forEach((row, rowIndex) => {
      row.values.forEach((value, colIndex) => {
        const x = padding + colIndex * cellWidth;
        const y = padding + rowIndex * cellHeight;
        const intensity = value / maxVal;

        // 绘制热力单元
        const gradient = this.ctx.createRadialGradient(
          x + cellWidth / 2, y + cellHeight / 2, 0,
          x + cellWidth / 2, y + cellHeight / 2, cellWidth / 2
        );
        gradient.addColorStop(0, `rgba(0, 230, 118, ${0.3 + intensity * 0.7})`);
        gradient.addColorStop(1, `rgba(0, 230, 118, ${0.1 + intensity * 0.4})`);

        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(x + 2, y + 2, cellWidth - 4, cellHeight - 4);

        // 数值标签
        this.ctx.fillStyle = intensity > 0.5 ? '#fff' : (this.options.theme === 'dark' ? '#ccc' : '#666');
        this.ctx.font = '10px sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(
          value,
          x + cellWidth / 2,
          y + cellHeight / 2
        );
      });

      // 行标签
      this.ctx.fillStyle = this.options.theme === 'dark' ? '#fff' : '#333';
      this.ctx.textAlign = 'right';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(row.label, padding - 10, padding + rowIndex * cellHeight + cellHeight / 2);
    });
  }
}

/**
 * 实时数据更新器
 */
class RealTimeChartUpdater {
  constructor(chart, updateInterval = 5000) {
    this.chart = chart;
    this.updateInterval = updateInterval;
    this.intervalId = null;
  }

  start(fetchData) {
    this.stop();
    this.fetchData = fetchData;
    this.update();

    this.intervalId = setInterval(() => {
      this.update();
    }, this.updateInterval);
  }

  async update() {
    try {
      const data = await this.fetchData();
      this.chart.setData(data);
    } catch (error) {
      console.error('Failed to update chart:', error);
    }
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}

// 导出
window.LineChart = LineChart;
window.DoughnutChart = DoughnutChart;
window.HeatMap = HeatMap;
window.RealTimeChartUpdater = RealTimeChartUpdater;
