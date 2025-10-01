// Beams Background Animation
// Adapted from React component to vanilla JavaScript

class BeamsBackground {
  constructor(options = {}) {
    this.intensity = options.intensity || "strong";
    this.canvas = null;
    this.ctx = null;
    this.beams = [];
    this.animationFrameId = null;
    this.MINIMUM_BEAMS = 20;

    this.opacityMap = {
      subtle: 0.7,
      medium: 0.85,
      strong: 1,
    };
  }

  createBeam(width, height) {
    const angle = -35 + Math.random() * 10;
    return {
      x: Math.random() * width * 1.5 - width * 0.25,
      y: Math.random() * height * 1.5 - height * 0.25,
      width: 30 + Math.random() * 60,
      length: height * 2.5,
      angle: angle,
      speed: 0.6 + Math.random() * 1.2,
      opacity: 0.12 + Math.random() * 0.16,
      hue: 190 + Math.random() * 70,
      pulse: Math.random() * Math.PI * 2,
      pulseSpeed: 0.02 + Math.random() * 0.03,
    };
  }

  resetBeam(beam, index, totalBeams) {
    if (!this.canvas) return beam;

    const column = index % 3;
    const spacing = this.canvas.width / 3;

    beam.y = this.canvas.height + 100;
    beam.x = column * spacing + spacing / 2 + (Math.random() - 0.5) * spacing * 0.5;
    beam.width = 100 + Math.random() * 100;
    beam.speed = 0.5 + Math.random() * 0.4;
    beam.hue = 190 + (index * 70) / totalBeams;
    beam.opacity = 0.2 + Math.random() * 0.1;
    return beam;
  }

  drawBeam(beam) {
    if (!this.ctx) return;

    this.ctx.save();
    this.ctx.translate(beam.x, beam.y);
    this.ctx.rotate((beam.angle * Math.PI) / 180);

    // Calculate pulsing opacity
    const pulsingOpacity =
      beam.opacity *
      (0.8 + Math.sin(beam.pulse) * 0.2) *
      this.opacityMap[this.intensity];

    const gradient = this.ctx.createLinearGradient(0, 0, 0, beam.length);

    // Enhanced gradient with multiple color stops
    gradient.addColorStop(0, `hsla(${beam.hue}, 85%, 65%, 0)`);
    gradient.addColorStop(0.1, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity * 0.5})`);
    gradient.addColorStop(0.4, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity})`);
    gradient.addColorStop(0.6, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity})`);
    gradient.addColorStop(0.9, `hsla(${beam.hue}, 85%, 65%, ${pulsingOpacity * 0.5})`);
    gradient.addColorStop(1, `hsla(${beam.hue}, 85%, 65%, 0)`);

    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(-beam.width / 2, 0, beam.width, beam.length);
    this.ctx.restore();
  }

  updateCanvasSize() {
    if (!this.canvas || !this.ctx) return;

    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = window.innerWidth * dpr;
    this.canvas.height = window.innerHeight * dpr;
    this.canvas.style.width = `${window.innerWidth}px`;
    this.canvas.style.height = `${window.innerHeight}px`;
    this.ctx.scale(dpr, dpr);

    const totalBeams = this.MINIMUM_BEAMS * 1.5;
    this.beams = Array.from({ length: totalBeams }, () =>
      this.createBeam(this.canvas.width, this.canvas.height)
    );
  }

  animate() {
    if (!this.canvas || !this.ctx) return;

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.filter = "blur(35px)";

    const totalBeams = this.beams.length;
    this.beams.forEach((beam, index) => {
      beam.y -= beam.speed;
      beam.pulse += beam.pulseSpeed;

      // Reset beam when it goes off screen
      if (beam.y + beam.length < -100) {
        this.resetBeam(beam, index, totalBeams);
      }

      this.drawBeam(beam);
    });

    this.animationFrameId = requestAnimationFrame(() => this.animate());
  }

  init(containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`Container with id '${containerId}' not found`);
      return;
    }

    // Create canvas element
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'absolute inset-0';
    this.canvas.style.cssText = 'position: absolute; top: 0; left: 0; filter: blur(15px); pointer-events: none;';

    this.ctx = this.canvas.getContext('2d');
    if (!this.ctx) {
      console.error('Failed to get canvas context');
      return;
    }

    container.appendChild(this.canvas);

    // Set up resize handler
    this.resizeHandler = () => this.updateCanvasSize();
    window.addEventListener('resize', this.resizeHandler);

    // Initialize
    this.updateCanvasSize();
    this.animate();
  }

  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler);
    }
    if (this.canvas && this.canvas.parentNode) {
      this.canvas.parentNode.removeChild(this.canvas);
    }
  }
}

// Auto-initialize if beams-background-container exists
document.addEventListener('DOMContentLoaded', function() {
  const container = document.getElementById('beams-background-container');
  if (container) {
    const beamsBackground = new BeamsBackground({
      intensity: "strong"
    });
    beamsBackground.init('beams-background-container');
  }
});
