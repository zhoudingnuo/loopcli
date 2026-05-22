// WebUI 通知系统
class NotificationSystem {
  constructor() {
    this.container = null;
    this.init();
  }

  init() {
    // 创建通知容器
    this.container = document.createElement('div');
    this.container.id = 'notification-container';
    this.container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
    `;
    document.body.appendChild(this.container);
  }

  show(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    const colors = {
      info: '#58a6ff',
      success: '#06d6a0',
      warning: '#ffd000',
      error: '#ff4757'
    };

    notification.style.cssText = `
      background: #161b22;
      border: 1px solid ${colors[type]};
      border-left: 4px solid ${colors[type]};
      border-radius: 8px;
      padding: 12px 16px;
      min-width: 280px;
      max-width: 400px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
      animation: slideIn 0.3s ease;
      display: flex;
      align-items: center;
      gap: 10px;
    `;

    const icons = {
      info: 'ℹ',
      success: '✓',
      warning: '⚠',
      error: '✕'
    };

    notification.innerHTML = `
      <span style="color: ${colors[type]}; font-size: 18px;">${icons[type]}</span>
      <span style="flex: 1; font-size: 13px;">${message}</span>
    `;

    this.container.appendChild(notification);

    // 自动消失
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, duration);

    return notification;
  }

  info(message, duration) { return this.show(message, 'info', duration); }
  success(message, duration) { return this.show(message, 'success', duration); }
  warning(message, duration) { return this.show(message, 'warning', duration); }
  error(message, duration) { return this.show(message, 'error', duration); }
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
`;
document.head.appendChild(style);

// 全局实例
const notify = new NotificationSystem();
