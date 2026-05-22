/**
 * WebUI 视觉特效组件
 * 增强美术风格：动态光效、3D变换、粒子动画
 */

class VisualEffects {
  constructor() {
    this.effects = [];
    this.animationFrame = null;
  }

  /**
   * 霓虹发光效果
   */
  applyNeonGlow(element, options = {}) {
    const {
      color = 'rgba(183, 148, 246, 0.6)',
      intensity = 20,
      speed = 2
    } = options;

    element.style.boxShadow = `0 0 ${intensity}px ${color}`;
    element.style.transition = `box-shadow ${speed}s ease`;

    const animate = () => {
      const pulse = Math.sin(Date.now() / (1000 / speed)) * 0.5 + 0.5;
      const currentIntensity = intensity * (0.5 + pulse * 0.5);
      element.style.boxShadow = `0 0 ${currentIntensity}px ${color}`;
      this.animationFrame = requestAnimationFrame(animate);
    };

    animate();
    this.effects.push({ type: 'neon', stop: () => cancelAnimationFrame(this.animationFrame) });
  }

  /**
   * 全息投影效果
   */
  applyHologramEffect(element) {
    element.style.position = 'relative';
    element.style.overflow = 'hidden';

    // 扫描线
    const scanLine = document.createElement('div');
    scanLine.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(to right, transparent, rgba(94, 201, 255, 0.8), transparent);
      animation: hologramScan 3s linear infinite;
      z-index: 1;
      pointer-events: none;
    `;

    // 添加扫描动画
    if (!document.getElementById('hologram-animations')) {
      const style = document.createElement('style');
      style.id = 'hologram-animations';
      style.textContent = `
        @keyframes hologramScan {
          0% { top: 0; opacity: 0; }
          10% { opacity: 1; }
          90% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
        @keyframes hologramFlicker {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.95; }
          75% { opacity: 0.98; }
        }
        @keyframes hologramGlitch {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-2px); }
          40% { transform: translateX(2px); }
          60% { transform: translateX(-1px); }
          80% { transform: translateX(1px); }
        }
      `;
      document.head.appendChild(style);
    }

    element.appendChild(scanLine);
    element.style.animation = 'hologramFlicker 0.1s infinite';

    this.effects.push({
      type: 'hologram',
      stop: () => {
        element.removeChild(scanLine);
        element.style.animation = '';
      }
    });
  }

  /**
   * 玻璃态增强效果
   */
  applyGlassmorphism(element, options = {}) {
    const {
      blur = 20,
      opacity = 0.1,
      borderOpacity = 0.2
    } = options;

    element.style.cssText += `
      backdrop-filter: blur(${blur}px);
      -webkit-backdrop-filter: blur(${blur}px);
      background: rgba(20, 30, 50, ${opacity});
      border: 1px solid rgba(120, 140, 180, ${borderOpacity});
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    `;

    // 添加鼠标悬停效果
    element.addEventListener('mouseenter', () => {
      element.style.transform = 'translateY(-2px) scale(1.01)';
      element.style.boxShadow = '0 12px 40px rgba(183, 148, 246, 0.2)';
    });

    element.addEventListener('mouseleave', () => {
      element.style.transform = '';
      element.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.3)';
    });
  }

  /**
   * 赛博朋克边框效果
   */
  applyCyberBorder(element, options = {}) {
    const {
      color1 = '#b794f6',
      color2 = '#f585c4',
      color3 = '#5ec9ff',
      thickness = 2
    } = options;

    element.style.position = 'relative';
    element.style.border = 'none';

    // 创建渐变边框
    const border = document.createElement('div');
    border.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      border: ${thickness}px solid transparent;
      border-image: linear-gradient(135deg, ${color1}, ${color2}, ${color3}) 1;
      pointer-events: none;
      border-radius: inherit;
    `;

    element.appendChild(border);
    this.effects.push({
      type: 'cyber',
      stop: () => element.removeChild(border)
    });
  }

  /**
   * 数据流动效果
   */
  applyDataFlow(container, options = {}) {
    const {
      color = 'rgba(94, 201, 255, 0.6)',
      particleCount = 20,
      speed = 2
    } = options;

    container.style.position = 'relative';
    container.style.overflow = 'hidden';

    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'data-flow-particle';
      particle.style.cssText = `
        position: absolute;
        width: 2px;
        height: 20px;
        background: linear-gradient(to bottom, transparent, ${color}, transparent);
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        opacity: ${Math.random() * 0.5 + 0.2};
        animation: dataFlow ${3 + Math.random() * 2}s linear infinite;
        animation-delay: ${Math.random() * 2}s;
      `;
      container.appendChild(particle);
    }

    // 添加流动动画
    if (!document.getElementById('data-flow-animations')) {
      const style = document.createElement('style');
      style.id = 'data-flow-animations';
      style.textContent = `
        @keyframes dataFlow {
          0% { transform: translateY(-20px); opacity: 0; }
          10% { opacity: 0.6; }
          90% { opacity: 0.6; }
          100% { transform: translateY(400px); opacity: 0; }
        }
      `;
      document.head.appendChild(style);
    }

    this.effects.push({
      type: 'dataFlow',
      stop: () => {
        container.querySelectorAll('.data-flow-particle').forEach(p => p.remove());
      }
    });
  }

  /**
   * 打字机效果
   */
  applyTypewriter(element, text, options = {}) {
    const {
      speed = 50,
      cursor = '▋',
      callback = null
    } = options;

    let index = 0;
    element.textContent = '';

    const type = () => {
      if (index < text.length) {
        element.textContent = text.slice(0, index + 1) + cursor;
        index++;
        setTimeout(type, speed);
      } else {
        element.textContent = text;
        if (callback) callback();
      }
    };

    type();
  }

  /**
   * 3D卡片倾斜效果
   */
  apply3DCardTilt(element, options = {}) {
    const {
      maxTilt = 10,
      perspective = 1000
    } = options;

    element.style.transformStyle = 'preserve-3d';
    element.style.perspective = `${perspective}px`;

    element.addEventListener('mousemove', (e) => {
      const rect = element.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const rotateX = ((y - centerY) / centerY) * -maxTilt;
      const rotateY = ((x - centerX) / centerX) * maxTilt;

      element.style.transform = `perspective(${perspective}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    element.addEventListener('mouseleave', () => {
      element.style.transform = 'perspective(${perspective}px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
    });
  }

  /**
   * 波纹扩散效果
   */
  applyRippleEffect(element, options = {}) {
    const {
      color = 'rgba(183, 148, 246, 0.4)',
      duration = 600
    } = options;

    element.style.position = 'relative';
    element.style.overflow = 'hidden';

    element.addEventListener('click', (e) => {
      const rect = element.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const ripple = document.createElement('div');
      ripple.style.cssText = `
        position: absolute;
        left: ${x}px;
        top: ${y}px;
        width: 0;
        height: 0;
        background: radial-gradient(circle, ${color}, transparent);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        animation: rippleEffect ${duration}ms ease-out;
        pointer-events: none;
      `;

      element.appendChild(ripple);

      setTimeout(() => ripple.remove(), duration);
    });

    // 添加波纹动画
    if (!document.getElementById('ripple-animations')) {
      const style = document.createElement('style');
      style.id = 'ripple-animations';
      style.textContent = `
        @keyframes rippleEffect {
          0% { width: 0; height: 0; opacity: 1; }
          100% { width: 200px; height: 200px; opacity: 0; }
        }
      `;
      document.head.appendChild(style);
    }
  }

  /**
   * 矩阵雨效果（背景）
   */
  applyMatrixRain(container, options = {}) {
    const {
      color = '#0f0',
      fontSize = 14,
      density = 0.1
    } = options;

    const canvas = document.createElement('canvas');
    canvas.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    `;
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let columns;
    let drops = [];

    const resize = () => {
      canvas.width = container.offsetWidth;
      canvas.height = container.offsetHeight;
      columns = Math.floor(canvas.width / fontSize);
      drops = Array(columns).fill(1);
    };

    const draw = () => {
      ctx.fillStyle = 'rgba(10, 14, 26, 0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = color;
      ctx.font = `${fontSize}px monospace`;

      for (let i = 0; i < drops.length; i++) {
        if (Math.random() > density) continue;

        const text = String.fromCharCode(0x30A0 + Math.random() * 96);
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }

      requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener('resize', resize);
    draw();

    this.effects.push({
      type: 'matrix',
      stop: () => {
        window.removeEventListener('resize', resize);
        container.removeChild(canvas);
      }
    });
  }

  /**
   * 清除所有效果
   */
  clearAll() {
    this.effects.forEach(effect => effect.stop());
    this.effects = [];
  }
}

// 自动应用效果到指定元素
function applyEffectsToSelectors(selectors) {
  const effects = new VisualEffects();

  selectors.forEach(({ selector, effect, options }) => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(element => {
      switch (effect) {
        case 'neon':
          effects.applyNeonGlow(element, options);
          break;
        case 'hologram':
          effects.applyHologramEffect(element);
          break;
        case 'glass':
          effects.applyGlassmorphism(element, options);
          break;
        case 'cyber':
          effects.applyCyberBorder(element, options);
          break;
        case '3d':
          effects.apply3DCardTilt(element, options);
          break;
        case 'ripple':
          effects.applyRippleEffect(element, options);
          break;
      }
    });
  });

  return effects;
}

// 导出
window.VisualEffects = VisualEffects;
window.applyEffectsToSelectors = applyEffectsToSelectors;
