// WebUI 自动更新模块
// 自动刷新 agent 状态，无需手动刷新页面

class AutoRefresh {
  constructor(options = {}) {
    this.interval = options.interval || 5000; // 默认5秒
    this.callback = options.callback;
    this.timer = null;
    this.isActive = false;
  }

  start() {
    if (this.isActive) return;
    this.isActive = true;
    this.timer = setInterval(() => {
      if (this.callback) this.callback();
    }, this.interval);
    console.log(`自动刷新已启动 (${this.interval}ms)`);
  }

  stop() {
    if (!this.isActive) return;
    this.isActive = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    console.log('自动刷新已停止');
  }

  setInterval(ms) {
    this.interval = ms;
    if (this.isActive) {
      this.stop();
      this.start();
    }
  }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AutoRefresh;
}
