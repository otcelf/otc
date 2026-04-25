// Канвасы
const starsCanvas = document.getElementById('stars');
const starsCtx = starsCanvas.getContext('2d');
const shapesCanvas = document.getElementById('shapes');
const shapesCtx = shapesCanvas.getContext('2d');

function resizeCanvas() {
    starsCanvas.width = window.innerWidth;
    starsCanvas.height = window.innerHeight;
    shapesCanvas.width = window.innerWidth;
    shapesCanvas.height = window.innerHeight;
}

resizeCanvas();
window.addEventListener('resize', resizeCanvas);

// Маленькие звёзды
class Star {
    constructor() {
        this.x = Math.random() * starsCanvas.width;
        this.y = Math.random() * starsCanvas.height;
        this.size = Math.random() * 0.8 + 0.3; // Совсем малюсенькие
        this.opacity = Math.random() * 0.4 + 0.2;
        this.fadeSpeed = (Math.random() - 0.5) * 0.005; // Медленное мерцание
    }

    update() {
        this.opacity += this.fadeSpeed;
        if (this.opacity <= 0.1 || this.opacity >= 0.6) {
            this.fadeSpeed *= -1;
        }
    }

    draw() {
        starsCtx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
        starsCtx.beginPath();
        starsCtx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        starsCtx.fill();
    }
}

const stars = [];
for (let i = 0; i < 200; i++) {
    stars.push(new Star());
}

// 3D Wireframe фигуры (низкополигональные)
class WireframeShape {
    constructor() {
        this.x = Math.random() * shapesCanvas.width;
        this.y = Math.random() * shapesCanvas.height;
        this.size = Math.random() * 100 + 70; // Уменьшил на 15%
        this.rotationX = Math.random() * Math.PI * 2;
        this.rotationY = Math.random() * Math.PI * 2;
        this.rotationZ = Math.random() * Math.PI * 2;
        this.rotationSpeedX = (Math.random() - 0.5) * 0.008;
        this.rotationSpeedY = (Math.random() - 0.5) * 0.008;
        this.rotationSpeedZ = (Math.random() - 0.5) * 0.008;
        this.speedX = (Math.random() - 0.5) * 0.2;
        this.speedY = (Math.random() - 0.5) * 0.2;
        const types = ['sphere', 'polyhedron', 'torus'];
        this.type = types[Math.floor(Math.random() * types.length)];
    }

    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.rotationX += this.rotationSpeedX;
        this.rotationY += this.rotationSpeedY;
        this.rotationZ += this.rotationSpeedZ;

        if (this.x < -this.size) this.x = shapesCanvas.width + this.size;
        if (this.x > shapesCanvas.width + this.size) this.x = -this.size;
        if (this.y < -this.size) this.y = shapesCanvas.height + this.size;
        if (this.y > shapesCanvas.height + this.size) this.y = -this.size;
    }

    project3D(x, y, z) {
        // Простая 3D проекция
        const scale = 200 / (200 + z);
        return {
            x: x * scale,
            y: y * scale
        };
    }

    rotate3D(x, y, z) {
        // Поворот вокруг X
        let y1 = y * Math.cos(this.rotationX) - z * Math.sin(this.rotationX);
        let z1 = y * Math.sin(this.rotationX) + z * Math.cos(this.rotationX);
        
        // Поворот вокруг Y
        let x1 = x * Math.cos(this.rotationY) + z1 * Math.sin(this.rotationY);
        let z2 = -x * Math.sin(this.rotationY) + z1 * Math.cos(this.rotationY);
        
        // Поворот вокруг Z
        let x2 = x1 * Math.cos(this.rotationZ) - y1 * Math.sin(this.rotationZ);
        let y2 = x1 * Math.sin(this.rotationZ) + y1 * Math.cos(this.rotationZ);
        
        return { x: x2, y: y2, z: z2 };
    }

    draw() {
        shapesCtx.save();
        shapesCtx.translate(this.x, this.y);
        shapesCtx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
        shapesCtx.lineWidth = 1;

        if (this.type === 'sphere') {
            this.drawWireframeSphere();
        } else if (this.type === 'torus') {
            this.drawTorus();
        } else {
            this.drawPolyhedron();
        }

        shapesCtx.restore();
    }

    drawWireframeSphere() {
        const segments = 32; // Ещё больше сегментов для очень плотной сетки
        const rings = 20;

        for (let i = 0; i < rings; i++) {
            shapesCtx.beginPath();
            for (let j = 0; j <= segments; j++) {
                const theta = (j / segments) * Math.PI * 2;
                const phi = (i / rings) * Math.PI;
                
                const x = this.size * Math.sin(phi) * Math.cos(theta);
                const y = this.size * Math.cos(phi);
                const z = this.size * Math.sin(phi) * Math.sin(theta);
                
                const rotated = this.rotate3D(x, y, z);
                const projected = this.project3D(rotated.x, rotated.y, rotated.z);
                
                if (j === 0) {
                    shapesCtx.moveTo(projected.x, projected.y);
                } else {
                    shapesCtx.lineTo(projected.x, projected.y);
                }
            }
            shapesCtx.stroke();
        }

        for (let j = 0; j < segments; j++) {
            shapesCtx.beginPath();
            for (let i = 0; i <= rings; i++) {
                const theta = (j / segments) * Math.PI * 2;
                const phi = (i / rings) * Math.PI;
                
                const x = this.size * Math.sin(phi) * Math.cos(theta);
                const y = this.size * Math.cos(phi);
                const z = this.size * Math.sin(phi) * Math.sin(theta);
                
                const rotated = this.rotate3D(x, y, z);
                const projected = this.project3D(rotated.x, rotated.y, rotated.z);
                
                if (i === 0) {
                    shapesCtx.moveTo(projected.x, projected.y);
                } else {
                    shapesCtx.lineTo(projected.x, projected.y);
                }
            }
            shapesCtx.stroke();
        }
    }

    drawPolyhedron() {
        // Геодезическая сфера (более плотная сетка)
        const segments = 16;
        const rings = 12;

        // Рисуем как сферу, но с плоскими гранями для полигонального вида
        for (let i = 0; i < rings; i++) {
            shapesCtx.beginPath();
            for (let j = 0; j <= segments; j++) {
                const theta = (j / segments) * Math.PI * 2;
                const phi = (i / rings) * Math.PI;
                
                const x = this.size * Math.sin(phi) * Math.cos(theta);
                const y = this.size * Math.cos(phi);
                const z = this.size * Math.sin(phi) * Math.sin(theta);
                
                const rotated = this.rotate3D(x, y, z);
                const projected = this.project3D(rotated.x, rotated.y, rotated.z);
                
                if (j === 0) {
                    shapesCtx.moveTo(projected.x, projected.y);
                } else {
                    shapesCtx.lineTo(projected.x, projected.y);
                }
            }
            shapesCtx.stroke();
        }

        for (let j = 0; j < segments; j++) {
            shapesCtx.beginPath();
            for (let i = 0; i <= rings; i++) {
                const theta = (j / segments) * Math.PI * 2;
                const phi = (i / rings) * Math.PI;
                
                const x = this.size * Math.sin(phi) * Math.cos(theta);
                const y = this.size * Math.cos(phi);
                const z = this.size * Math.sin(phi) * Math.sin(theta);
                
                const rotated = this.rotate3D(x, y, z);
                const projected = this.project3D(rotated.x, rotated.y, rotated.z);
                
                if (i === 0) {
                    shapesCtx.moveTo(projected.x, projected.y);
                } else {
                    shapesCtx.lineTo(projected.x, projected.y);
                }
            }
            shapesCtx.stroke();
        }

        // Добавляем диагональные линии для более плотной сетки
        for (let i = 0; i < rings - 1; i++) {
            for (let j = 0; j < segments; j++) {
                shapesCtx.beginPath();
                
                const theta1 = (j / segments) * Math.PI * 2;
                const phi1 = (i / rings) * Math.PI;
                const x1 = this.size * Math.sin(phi1) * Math.cos(theta1);
                const y1 = this.size * Math.cos(phi1);
                const z1 = this.size * Math.sin(phi1) * Math.sin(theta1);
                
                const theta2 = ((j + 1) / segments) * Math.PI * 2;
                const phi2 = ((i + 1) / rings) * Math.PI;
                const x2 = this.size * Math.sin(phi2) * Math.cos(theta2);
                const y2 = this.size * Math.cos(phi2);
                const z2 = this.size * Math.sin(phi2) * Math.sin(theta2);
                
                const rotated1 = this.rotate3D(x1, y1, z1);
                const projected1 = this.project3D(rotated1.x, rotated1.y, rotated1.z);
                
                const rotated2 = this.rotate3D(x2, y2, z2);
                const projected2 = this.project3D(rotated2.x, rotated2.y, rotated2.z);
                
                shapesCtx.moveTo(projected1.x, projected1.y);
                shapesCtx.lineTo(projected2.x, projected2.y);
                shapesCtx.stroke();
            }
        }
    }

    drawTorus() {
        const majorRadius = this.size * 0.8;
        const minorRadius = this.size * 0.3;
        const majorSegments = 36; // Ещё больше сегментов для очень плотной сетки
        const minorSegments = 24;

        // Рисуем кольцо (тор)
        for (let i = 0; i < majorSegments; i++) {
            shapesCtx.beginPath();
            for (let j = 0; j <= minorSegments; j++) {
                const u = (i / majorSegments) * Math.PI * 2;
                const v = (j / minorSegments) * Math.PI * 2;
                
                const x = (majorRadius + minorRadius * Math.cos(v)) * Math.cos(u);
                const y = (majorRadius + minorRadius * Math.cos(v)) * Math.sin(u);
                const z = minorRadius * Math.sin(v);
                
                const rotated = this.rotate3D(x, y, z);
                const projected = this.project3D(rotated.x, rotated.y, rotated.z);
                
                if (j === 0) {
                    shapesCtx.moveTo(projected.x, projected.y);
                } else {
                    shapesCtx.lineTo(projected.x, projected.y);
                }
            }
            shapesCtx.stroke();
        }

        for (let j = 0; j < minorSegments; j++) {
            shapesCtx.beginPath();
            for (let i = 0; i <= majorSegments; i++) {
                const u = (i / majorSegments) * Math.PI * 2;
                const v = (j / minorSegments) * Math.PI * 2;
                
                const x = (majorRadius + minorRadius * Math.cos(v)) * Math.cos(u);
                const y = (majorRadius + minorRadius * Math.cos(v)) * Math.sin(u);
                const z = minorRadius * Math.sin(v);
                
                const rotated = this.rotate3D(x, y, z);
                const projected = this.project3D(rotated.x, rotated.y, rotated.z);
                
                if (i === 0) {
                    shapesCtx.moveTo(projected.x, projected.y);
                } else {
                    shapesCtx.lineTo(projected.x, projected.y);
                }
            }
            shapesCtx.stroke();
        }
    }
}

const shapes = [];
for (let i = 0; i < 10; i++) {
    shapes.push(new WireframeShape());
}

// Анимация
let scrollY = 0;
let lastScrollY = 0;

window.addEventListener('scroll', () => {
    scrollY = window.scrollY;
});

function animate() {
    starsCtx.clearRect(0, 0, starsCanvas.width, starsCanvas.height);
    shapesCtx.clearRect(0, 0, shapesCanvas.width, shapesCanvas.height);

    stars.forEach(star => {
        star.update();
        star.draw();
    });

    shapes.forEach((shape, index) => {
        // Плавное изменение размера при скролле
        const scrollProgress = (scrollY / 1000) % 2;
        const sizeFactor = 1 + Math.sin(scrollProgress * Math.PI + index) * 0.3;
        const originalSize = shape.baseSize || shape.size;
        if (!shape.baseSize) shape.baseSize = shape.size;
        shape.size = originalSize * sizeFactor;
        
        shape.update();
        shape.draw();
    });

    lastScrollY = scrollY;
    requestAnimationFrame(animate);
}

animate();
