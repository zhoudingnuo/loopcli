/**
 * 增强型粒子系统 - LoopCLI WebUI
 * 特性：动态粒子网络、鼠标交互、3D透视效果
 */

class EnhancedParticleSystem {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.particles = [];
    this.mouse = { x: null, y: null, radius: 150 };
    this.options = {
      particleCount: 80,
      connectionDistance: 120,
      mouseInteractionDistance: 150,
      particleSpeed: 0.5,
      particleSize: { min: 1, max: 3 },
      colors: ['#a78bfa', '#f472b6', '#38bdf8', '#00e676'],
      enableConnections: true,
      enableMouseInteraction: true,
      enable3DEffect: true,
      ...options
    };

    this.init();
    this.bindEvents();
    this.animate();
  }

  init() {
    this.resize();
    this.createParticles();
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  createParticles() {
    this.particles = [];
    for (let i = 0; i < this.options.particleCount; i++) {
      this.particles.push(this.createParticle());
    }
  }

  createParticle() {
    const size = this.random(
      this.options.particleSize.min,
      this.options.particleSize.max
    );
    const x = Math.random() * this.canvas.width;
    const y = Math.random() * this.canvas.height;
    const color = this.options.colors[
      Math.floor(Math.random() * this.options.colors.length)
    ];

    return {
      x,
      y,
      baseX: x,
      baseY: y,
      size,
      color,
      speedX: (Math.random() - 0.5) * this.options.particleSpeed,
      speedY: (Math.random() - 0.5) * this.options.particleSpeed,
      density: Math.random() * 30 + 1,
      angle: Math.random() * Math.PI * 2,
      angleSpeed: (Math.random() - 0.5) * 0.02,
      amplitude: Math.random() * 2
    };
  }

  random(min, max) {
    return Math.random() * (max - min) + min;
  }

  bindEvents() {
    window.addEventListener('resize', () => this.resize());

    if (this.options.enableMouseInteraction) {
      window.addEventListener('mousemove', (e) => {
        this.mouse.x = e.x;
        this.mouse.y = e.y;
      });

      window.addEventListener('mouseout', () => {
        this.mouse.x = null;
        this.mouse.y = null;
      });
    }
  }

  update() {
    this.particles.forEach(particle => {
      // 基础运动
      particle.angle += particle.angleSpeed;

      if (this.options.enable3DEffect) {
        // 3D 波动效果
        particle.x = particle.baseX + Math.sin(particle.angle) * particle.amplitude;
        particle.y = particle.baseY + Math.cos(particle.angle) * particle.amplitude;
      } else {
        // 传统线性运动
        particle.baseX += particle.speedX;
        particle.baseY += particle.speedY;
      }

      // 鼠标交互
      if (this.options.enableMouseInteraction && this.mouse.x !== null) {
        const dx = this.mouse.x - particle.x;
        const dy = this.mouse.y - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < this.options.mouseInteractionDistance) {
          const forceDirectionX = dx / distance;
          const forceDirectionY = dy / distance;
          const force = (this.options.mouseInteractionDistance - distance) /
                       this.options.mouseInteractionDistance;
          const directionX = forceDirectionX * force * particle.density;
          const directionY = forceDirectionY * force * particle.density;

          particle.x -= directionX;
          particle.y -= directionY;
        }
      }

      // 边界检测
      if (particle.x < 0 || particle.x > this.canvas.width) {
        particle.speedX *= -1;
        particle.baseX = Math.max(0, Math.min(this.canvas.width, particle.baseX));
      }
      if (particle.y < 0 || particle.y > this.canvas.height) {
        particle.speedY *= -1;
        particle.baseY = Math.max(0, Math.min(this.canvas.height, particle.baseY));
      }
    });
  }

  draw() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // 绘制连接线
    if (this.options.enableConnections) {
      this.drawConnections();
    }

    // 绘制粒子
    this.particles.forEach(particle => {
      this.ctx.beginPath();
      this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
      this.ctx.fillStyle = particle.color;
      this.ctx.shadowBlur = 15;
      this.ctx.shadowColor = particle.color;
      this.ctx.fill();
      this.ctx.shadowBlur = 0;
    });
  }

  drawConnections() {
    for (let i = 0; i < this.particles.length; i++) {
      for (let j = i + 1; j < this.particles.length; j++) {
        const dx = this.particles[i].x - this.particles[j].x;
        const dy = this.particles[i].y - this.particles[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < this.options.connectionDistance) {
          const opacity = 1 - distance / this.options.connectionDistance;
          this.ctx.strokeStyle = `rgba(167, 139, 250, ${opacity * 0.3})`;
          this.ctx.lineWidth = 1;
          this.ctx.beginPath();
          this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
          this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
          this.ctx.stroke();
        }
      }
    }
  }

  animate() {
    this.update();
    this.draw();
    requestAnimationFrame(() => this.animate());
  }

  // 公共方法：更新配置
  updateOptions(newOptions) {
    this.options = { ...this.options, ...newOptions };
    if (newOptions.particleCount) {
      this.createParticles();
    }
  }

  // 公共方法：添加粒子爆发效果
  burst(x, y, count = 10) {
    for (let i = 0; i < count; i++) {
      const particle = this.createParticle();
      particle.x = x;
      particle.y = y;
      particle.baseX = x;
      particle.baseY = y;
      particle.speedX = (Math.random() - 0.5) * 3;
      particle.speedY = (Math.random() - 0.5) * 3;
      this.particles.push(particle);
    }

    // 移除多余粒子
    while (this.particles.length > this.options.particleCount + count) {
      this.particles.shift();
    }
  }

  // 公共方法：重置系统
  reset() {
    this.createParticles();
  }
}

// 导出
window.EnhancedParticleSystem = EnhancedParticleSystem;
