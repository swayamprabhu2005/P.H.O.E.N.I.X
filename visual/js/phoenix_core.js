/**
 * P.H.O.E.N.I.X. Holographic 3D Dyson Core Engine (v3.0 JARVIS / Ultron Aesthetic)
 * High-tech procedural WebGL recreation of the holographic Arc Reactor / Dyson Sphere.
 * Features 20 multi-axis technological segmented rings, digital HUD tick-marks,
 * 3,200+ holographic particle embers, nested solar plasma core,
 * 360-degree spherical coverage enclosing the central energy nucleus,
 * and gradual top-to-bottom Ultron Blue sleep state transition.
 */

class PhoenixCore {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.state = 'standby'; // 'standby', 'listening', 'processing', 'success'
        this.audioLevel = 0.0;
        this.clock = new THREE.Clock();

        // Sleep state transition progress (0.0 = Awake Orange, 1.0 = Ultron Blue Sleep)
        this.sleepProgress = 1.0; // starts in standby (sleep)
        this.targetSleep = 1.0;

        // Shockwave effect
        this.shockwaveTime = 0.0;
        this.isShockwaving = false;

        this.initScene();
        this.buildNebulaBackdrop();
        this.buildSolarCore();
        this.buildDysonRings();
        this.buildDigitalTicks();
        this.buildParticleSwarm();
        this.setupLighting();
        this.setupEvents();
        this.animate();
    }

    initScene() {
        const width = this.container.clientWidth || 340;
        const height = this.container.clientHeight || 340;

        this.scene = new THREE.Scene();

        // 3D Perspective Camera for depth (FOV 45, distance 13.8 ensures 0 clipping)
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(0, 0, 13.8);

        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setClearColor(0x000000, 0); // 100% Transparent background
        this.container.appendChild(this.renderer.domElement);

        this.dysonGroup = new THREE.Group();
        this.scene.add(this.dysonGroup);
    }

    setupLighting() {
        this.ambientLight = new THREE.AmbientLight(0x0a0400, 1.0);
        this.scene.add(this.ambientLight);

        // Core central solar point light
        this.coreLight = new THREE.PointLight(0xff7700, 4.5, 35);
        this.coreLight.position.set(0, 0, 0);
        this.dysonGroup.add(this.coreLight);

        // Secondary rim point light
        this.accentLight = new THREE.PointLight(0xffaa00, 2.2, 25);
        this.accentLight.position.set(0, 0, 2);
        this.dysonGroup.add(this.accentLight);
    }

    buildNebulaBackdrop() {
        const canvas = document.createElement('canvas');
        canvas.width = 256; canvas.height = 256;
        const ctx = canvas.getContext('2d');
        const grad = ctx.createRadialGradient(128, 128, 4, 128, 128, 128);
        grad.addColorStop(0, 'rgba(180, 50, 0, 0.28)');
        grad.addColorStop(0.4, 'rgba(80, 20, 110, 0.18)');
        grad.addColorStop(0.75, 'rgba(10, 5, 30, 0.05)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 256, 256);

        this.nebulaCanvas = canvas;
        this.nebulaCtx = ctx;
        this.nebulaTexture = new THREE.CanvasTexture(canvas);

        const geo = new THREE.PlaneGeometry(12, 12);
        const mat = new THREE.MeshBasicMaterial({
            map: this.nebulaTexture,
            transparent: true,
            depthWrite: false,
            blending: THREE.AdditiveBlending
        });
        this.nebulaMesh = new THREE.Mesh(geo, mat);
        this.nebulaMesh.position.z = -1.2;
        this.dysonGroup.add(this.nebulaMesh);
    }

    buildSolarCore() {
        // 1. Central White-Hot / Cyan-White Nuclear Sphere
        const innerGeo = new THREE.SphereGeometry(0.85, 32, 32);
        const innerMat = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.98
        });
        this.innerCore = new THREE.Mesh(innerGeo, innerMat);
        this.dysonGroup.add(this.innerCore);

        // 2. Molten Filament Plasma Shell
        const plasmaGeo = new THREE.SphereGeometry(1.22, 24, 24);
        const plasmaMat = new THREE.MeshBasicMaterial({
            color: 0xff8800,
            wireframe: true,
            transparent: true,
            opacity: 0.70,
            blending: THREE.AdditiveBlending
        });
        this.plasmaShell = new THREE.Mesh(plasmaGeo, plasmaMat);
        this.dysonGroup.add(this.plasmaShell);

        // 3. Corona Cloud
        const coronaGeo = new THREE.SphereGeometry(1.55, 20, 20);
        const coronaMat = new THREE.MeshBasicMaterial({
            color: 0xff4400,
            transparent: true,
            opacity: 0.28,
            blending: THREE.AdditiveBlending
        });
        this.corona = new THREE.Mesh(coronaGeo, coronaMat);
        this.dysonGroup.add(this.corona);
    }

    buildDysonRings() {
        this.rings = [];

        // 20 Multi-Axis Concentric & Interlocking Toroids forming a complete 360-degree Dyson Sphere
        // Radii kept between 1.8 and 3.5 to prevent any viewport clipping
        const ringConfigs = [
            // r, tube, rx, ry, rz, sx, sy, sz, awakeCol, sleepCol, normY (1=top, 0=bottom)
            { r: 1.85, t: 0.055, rx: 0.5, ry: 0.2, rz: 0.1, sx: 0.016, sy: 0.024, sz: -0.012, ac: 0xff7700, sc: 0x00d4ff, ny: 0.95 },
            { r: 2.00, t: 0.050, rx: -0.6, ry: 0.5, rz: 0.4, sx: -0.020, sy: 0.015, sz: 0.018, ac: 0xff8800, sc: 0x00b4d8, ny: 0.90 },
            { r: 2.15, t: 0.060, rx: 0.9, ry: -0.3, rz: 0.6, sx: 0.014, sy: -0.022, sz: 0.015, ac: 0xff6600, sc: 0x0096c7, ny: 0.85 },
            { r: 2.30, t: 0.055, rx: -0.4, ry: 0.8, rz: -0.5, sx: -0.015, sy: 0.020, sz: -0.016, ac: 0xff9900, sc: 0x0077b6, ny: 0.80 },
            { r: 2.45, t: 0.065, rx: 0.3, ry: -0.7, rz: 0.8, sx: 0.012, sy: -0.016, sz: 0.022, ac: 0xff5500, sc: 0x0055ff, ny: 0.75 },
            { r: 2.60, t: 0.055, rx: -0.7, ry: -0.4, rz: 0.2, sx: -0.018, sy: -0.012, sz: 0.015, ac: 0xff7700, sc: 0x00a8ff, ny: 0.70 },
            { r: 2.75, t: 0.060, rx: 0.6, ry: 0.7, rz: -0.3, sx: 0.015, sy: 0.018, sz: -0.014, ac: 0xff8800, sc: 0x00d4ff, ny: 0.65 },
            { r: 2.85, t: 0.050, rx: -0.5, ry: 0.4, rz: 0.7, sx: -0.014, sy: 0.016, sz: 0.020, ac: 0xff6600, sc: 0x0096c7, ny: 0.60 },
            { r: 2.95, t: 0.065, rx: 0.8, ry: 0.2, rz: -0.6, sx: 0.011, sy: -0.018, sz: 0.014, ac: 0xffaa00, sc: 0x0077b6, ny: 0.55 },
            { r: 3.05, t: 0.055, rx: -0.3, ry: -0.8, rz: 0.4, sx: -0.016, sy: -0.015, sz: -0.018, ac: 0xff7700, sc: 0x0055ff, ny: 0.50 },
            { r: 3.15, t: 0.060, rx: 0.4, ry: 0.9, rz: 0.1, sx: 0.013, sy: 0.022, sz: 0.011, ac: 0xff5500, sc: 0x00a8ff, ny: 0.45 },
            { r: 3.25, t: 0.050, rx: -0.8, ry: -0.3, rz: -0.4, sx: -0.015, sy: -0.012, sz: 0.017, ac: 0xff8800, sc: 0x00d4ff, ny: 0.40 },
            { r: 3.35, t: 0.065, rx: 0.7, ry: -0.5, rz: 0.5, sx: 0.012, sy: -0.019, sz: 0.013, ac: 0xff6600, sc: 0x0096c7, ny: 0.35 },
            { r: 3.42, t: 0.055, rx: -0.2, ry: 0.6, rz: -0.7, sx: -0.017, sy: 0.014, sz: -0.021, ac: 0xff9900, sc: 0x0077b6, ny: 0.30 },
            { r: 3.48, t: 0.060, rx: 0.5, ry: -0.6, rz: 0.3, sx: 0.014, sy: -0.017, sz: 0.016, ac: 0xff7700, sc: 0x0055ff, ny: 0.25 },
            { r: 3.52, t: 0.050, rx: -0.6, ry: -0.7, rz: 0.8, sx: -0.013, sy: -0.015, sz: 0.019, ac: 0xff8800, sc: 0x00a8ff, ny: 0.20 },
            { r: 3.56, t: 0.065, rx: 0.2, ry: 0.8, rz: -0.2, sx: 0.016, sy: 0.021, sz: -0.012, ac: 0xff5500, sc: 0x00d4ff, ny: 0.15 },
            { r: 3.60, t: 0.055, rx: -0.7, ry: 0.3, rz: -0.5, sx: -0.014, sy: 0.013, sz: -0.017, ac: 0xffaa00, sc: 0x0096c7, ny: 0.10 },
            { r: 3.64, t: 0.060, rx: 0.8, ry: -0.2, rz: 0.7, sx: 0.011, sy: -0.018, sz: 0.015, ac: 0xff7700, sc: 0x0077b6, ny: 0.05 },
            { r: 3.68, t: 0.050, rx: -0.4, ry: 0.7, rz: 0.2, sx: -0.016, sy: 0.017, sz: 0.014, ac: 0xff6600, sc: 0x0055ff, ny: 0.00 }
        ];

        ringConfigs.forEach((cfg) => {
            const geo = new THREE.TorusGeometry(cfg.r, cfg.t, 16, 72);
            const mat = new THREE.MeshStandardMaterial({
                color: cfg.ac,
                emissive: cfg.ac,
                emissiveIntensity: 2.0,
                roughness: 0.25,
                metalness: 0.85
            });
            const mesh = new THREE.Mesh(geo, mat);
            mesh.rotation.set(cfg.rx, cfg.ry, cfg.rz);

            this.rings.push({
                mesh,
                mat,
                spX: cfg.sx,
                spY: cfg.sy,
                spZ: cfg.sz,
                awakeColor: new THREE.Color(cfg.ac),
                sleepColor: new THREE.Color(cfg.sc),
                normY: cfg.ny // 1.0 = top, 0.0 = bottom for wave progression
            });
            this.dysonGroup.add(mesh);
        });
    }

    buildDigitalTicks() {
        this.tickGroup = new THREE.Group();
        this.dysonGroup.add(this.tickGroup);

        const tickConfigs = [
            { count: 32, radius: 2.7, tiltX: 0.5, tiltY: 0.3, awakeCol: 0xff9900, sleepCol: 0x00e5ff },
            { count: 44, radius: 3.3, tiltX: -0.6, tiltY: 0.7, awakeCol: 0xff7700, sleepCol: 0x00a8ff },
            { count: 56, radius: 3.7, tiltX: 0.8, tiltY: -0.4, awakeCol: 0xffaa00, sleepCol: 0x0055ff }
        ];

        this.tickPlanes = [];

        tickConfigs.forEach((cfg) => {
            const planeGroup = new THREE.Group();
            planeGroup.rotation.set(cfg.tiltX, cfg.tiltY, 0);

            const ticksInPlane = [];
            for (let i = 0; i < cfg.count; i++) {
                const angle = (i / cfg.count) * Math.PI * 2;
                const tickGeo = new THREE.BoxGeometry(0.06, 0.22, 0.09);
                const tickMat = new THREE.MeshStandardMaterial({
                    color: cfg.awakeCol,
                    emissive: cfg.awakeCol,
                    emissiveIntensity: 2.2,
                    metalness: 0.9,
                    roughness: 0.2
                });
                const tickMesh = new THREE.Mesh(tickGeo, tickMat);
                tickMesh.position.set(Math.cos(angle) * cfg.radius, Math.sin(angle) * cfg.radius, 0);
                tickMesh.rotation.z = angle + Math.PI / 2;
                planeGroup.add(tickMesh);

                ticksInPlane.push({
                    mat: tickMat,
                    awakeColor: new THREE.Color(cfg.awakeCol),
                    sleepColor: new THREE.Color(cfg.sleepCol)
                });
            }

            this.tickGroup.add(planeGroup);
            this.tickPlanes.push({ planeGroup, ticks: ticksInPlane });
        });
    }

    buildParticleSwarm() {
        const pCount = 3200;
        const positions = new Float32Array(pCount * 3);
        const colors = new Float32Array(pCount * 3);
        const velocities = [];

        this.particleAwakeColors = [];
        this.particleSleepColors = [];

        const colCoreGold = new THREE.Color(0xfff0cc);
        const colBrightAmber = new THREE.Color(0xff8800);
        const colDeepFlame = new THREE.Color(0xcc3300);

        const colSleepCore = new THREE.Color(0xd0f4ff);
        const colSleepCyan = new THREE.Color(0x00d4ff);
        const colSleepBlue = new THREE.Color(0x0044cc);

        for (let i = 0; i < pCount; i++) {
            // Full 360-degree spherical shell distribution (radius 1.4 to 4.2)
            const r = 1.4 + Math.random() * 2.8;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);

            positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = r * Math.cos(phi);

            const t = (r - 1.4) / 2.8;

            // Awake Amber Palette
            const colA = new THREE.Color();
            if (t < 0.35) colA.lerpColors(colCoreGold, colBrightAmber, t / 0.35);
            else colA.lerpColors(colBrightAmber, colDeepFlame, (t - 0.35) / 0.65);
            this.particleAwakeColors.push(colA);

            // Sleep Ultron Blue Palette
            const colS = new THREE.Color();
            if (t < 0.35) colS.lerpColors(colSleepCore, colSleepCyan, t / 0.35);
            else colS.lerpColors(colSleepCyan, colSleepBlue, (t - 0.35) / 0.65);
            this.particleSleepColors.push(colS);

            // Initial color (starts in sleep)
            colors[i * 3] = colS.r;
            colors[i * 3 + 1] = colS.g;
            colors[i * 3 + 2] = colS.b;

            velocities.push({
                speedTheta: 0.012 + Math.random() * 0.022,
                speedPhi: 0.006 + Math.random() * 0.014,
                radius: r,
                theta,
                phi
            });
        }

        const pGeo = new THREE.BufferGeometry();
        pGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        pGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const pCanvas = document.createElement('canvas');
        pCanvas.width = 64; pCanvas.height = 64;
        const pCtx = pCanvas.getContext('2d');
        const pGrad = pCtx.createRadialGradient(32, 32, 2, 32, 32, 32);
        pGrad.addColorStop(0, 'rgba(255, 255, 255, 1)');
        pGrad.addColorStop(0.35, 'rgba(0, 210, 255, 0.85)');
        pGrad.addColorStop(0.75, 'rgba(0, 80, 220, 0.20)');
        pGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        pCtx.fillStyle = pGrad;
        pCtx.fillRect(0, 0, 64, 64);

        const pMat = new THREE.PointsMaterial({
            size: 0.20,
            map: new THREE.CanvasTexture(pCanvas),
            vertexColors: true,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        this.particles = new THREE.Points(pGeo, pMat);
        this.particleVelocities = velocities;
        this.dysonGroup.add(this.particles);
    }

    setupEvents() {
        window.addEventListener('resize', () => {
            const width = this.container.clientWidth || 340;
            const height = this.container.clientHeight || 340;
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        });

        window.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth - 0.5) * 0.3;
            const y = (e.clientY / window.innerHeight - 0.5) * 0.3;
            this.camera.position.x = x * 2.5;
            this.camera.position.y = -y * 2.5;
            this.camera.lookAt(0, 0, 0);
        });
    }

    setState(newState) {
        this.state = newState;
        if (newState === 'standby') {
            this.targetSleep = 1.0; // Transition to Ultron Blue
        } else {
            this.targetSleep = 0.0; // Transition to Vibrant Amber/Orange
        }
    }

    setAudioLevel(level) {
        this.audioLevel = Math.min(Math.max(level, 0.0), 1.0);
    }

    triggerSuccessShockwave() {
        this.shockwaveTime = 0.0;
        this.isShockwaving = true;
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const delta = Math.min(this.clock.getDelta(), 0.1);
        const time = this.clock.getElapsedTime();

        // Smoothly interpolate sleep progress (slow gradual wave)
        const transitionSpeed = 0.85; // ~1.5 - 2 seconds gradual transition
        if (this.sleepProgress < this.targetSleep) {
            this.sleepProgress = Math.min(this.sleepProgress + delta * transitionSpeed, 1.0);
        } else if (this.sleepProgress > this.targetSleep) {
            this.sleepProgress = Math.max(this.sleepProgress - delta * (transitionSpeed * 1.8), 0.0);
        }

        // Active speed multiplier based on awake state vs sleep
        let baseSpeed = 1.8; // High-speed energetic default awake rotation
        let lightInt = 4.5;

        if (this.state === 'standby') {
            baseSpeed = 0.45; // Calm, slow dormant sleep idle
            lightInt = 1.6;
        } else if (this.state === 'listening') {
            baseSpeed = 3.2; // Fast responsive rotation
            lightInt = 5.2 + this.audioLevel * 3.0;
        } else if (this.state === 'processing') {
            baseSpeed = 5.0; // Hyperspeed processing
            lightInt = 6.5;
        } else if (this.state === 'success') {
            baseSpeed = 2.4;
            lightInt = 5.5;
        }

        const effectiveSpeed = baseSpeed;

        // Central Core Breathing Pulsation
        const pulse = 1.0 + Math.sin(time * 3.5) * 0.07 + (this.state !== 'standby' ? this.audioLevel * 0.20 : 0);
        this.innerCore.scale.set(pulse, pulse, pulse);
        this.plasmaShell.scale.set(pulse * 1.05, pulse * 1.05, pulse * 1.05);
        this.plasmaShell.rotation.y += 0.020 * effectiveSpeed;
        this.plasmaShell.rotation.x -= 0.012 * effectiveSpeed;

        // Color transitions for Core & Lights
        const colAwakeCore = new THREE.Color(0xffffff);
        const colSleepCore = new THREE.Color(0xd0f5ff);
        const curCoreCol = new THREE.Color().lerpColors(colAwakeCore, colSleepCore, this.sleepProgress);
        this.innerCore.material.color.copy(curCoreCol);

        const colAwakePlasma = new THREE.Color(0xff8800);
        const colSleepPlasma = new THREE.Color(0x00b4d8);
        const curPlasmaCol = new THREE.Color().lerpColors(colAwakePlasma, colSleepPlasma, this.sleepProgress);
        this.plasmaShell.material.color.copy(curPlasmaCol);

        const colAwakeCorona = new THREE.Color(0xff3300);
        const colSleepCorona = new THREE.Color(0x0033aa);
        const curCoronaCol = new THREE.Color().lerpColors(colAwakeCorona, colSleepCorona, this.sleepProgress);
        this.corona.material.color.copy(curCoronaCol);

        const colAwakeLight = new THREE.Color(0xff7700);
        const colSleepLight = new THREE.Color(0x0088ff);
        const curLightCol = new THREE.Color().lerpColors(colAwakeLight, colSleepLight, this.sleepProgress);
        this.coreLight.color.copy(curLightCol);
        this.coreLight.intensity = lightInt + Math.sin(time * 4.0) * 0.3;

        // 360-degree rotation of the entire Dyson sphere assembly
        this.dysonGroup.rotation.y += 0.008 * effectiveSpeed;
        this.dysonGroup.rotation.x = Math.sin(time * 0.40) * 0.20;
        this.dysonGroup.rotation.z = Math.cos(time * 0.35) * 0.15;

        // Animate Rings with Gradual TOP-TO-BOTTOM Ultron Blue Wave Transition
        this.rings.forEach((ring) => {
            ring.mesh.rotation.x += ring.spX * effectiveSpeed;
            ring.mesh.rotation.y += ring.spY * effectiveSpeed;
            ring.mesh.rotation.z += ring.spZ * effectiveSpeed;

            // Top-to-bottom wave calculation:
            // ring.normY goes from 1.0 (top) down to 0.0 (bottom)
            // As sleepProgress goes from 0.0 to 1.0:
            // Top rings (normY ~ 1.0) transition first; bottom rings transition last.
            let localT = 0.0;
            if (this.targetSleep === 1.0) {
                // Entering sleep: top to bottom cascade
                // Normalized wave front:
                const delay = (1.0 - ring.normY) * 0.55;
                localT = Math.min(Math.max((this.sleepProgress - delay) / 0.45, 0.0), 1.0);
            } else {
                // Waking up: fast bottom-to-top or uniform re-ignition
                localT = this.sleepProgress;
            }

            const ringCol = new THREE.Color().lerpColors(ring.awakeColor, ring.sleepColor, localT);
            ring.mat.color.copy(ringCol);
            ring.mat.emissive.copy(ringCol);
            ring.mat.emissiveIntensity = THREE.MathUtils.lerp(2.0, 1.2, localT);
        });

        // Rotate HUD Digital Ticks
        if (this.tickPlanes) {
            this.tickPlanes.forEach((tp, idx) => {
                const dir = idx % 2 === 0 ? 1 : -1;
                tp.planeGroup.rotation.z += dir * (0.012 + idx * 0.006) * effectiveSpeed;

                tp.ticks.forEach((tick) => {
                    const tickCol = new THREE.Color().lerpColors(tick.awakeColor, tick.sleepColor, this.sleepProgress);
                    tick.mat.color.copy(tickCol);
                    tick.mat.emissive.copy(tickCol);
                });
            });
        }

        // Nebula slow swirl
        if (this.nebulaMesh) {
            this.nebulaMesh.rotation.z -= 0.003 * effectiveSpeed;
        }

        // Particle Swarm Animation & Color Blend
        const positions = this.particles.geometry.attributes.position.array;
        const colors = this.particles.geometry.attributes.color.array;
        const pLen = this.particleVelocities.length;

        for (let i = 0; i < pLen; i++) {
            const v = this.particleVelocities[i];
            v.theta += v.speedTheta * effectiveSpeed;
            v.phi += v.speedPhi * effectiveSpeed;

            const r = v.radius + Math.sin(time * 2.5 + i) * 0.10;
            const idx = i * 3;

            positions[idx] = r * Math.sin(v.phi) * Math.cos(v.theta);
            positions[idx + 1] = r * Math.sin(v.phi) * Math.sin(v.theta);
            positions[idx + 2] = r * Math.cos(v.phi);

            // Particle color wave: particles near top (Y > 0) transition sooner
            const pNormY = Math.min(Math.max((positions[idx + 1] / 3.0 + 1.0) / 2.0, 0.0), 1.0);
            const pDelay = (1.0 - pNormY) * 0.45;
            const pT = Math.min(Math.max((this.sleepProgress - pDelay) / 0.55, 0.0), 1.0);

            const pColA = this.particleAwakeColors[i];
            const pColS = this.particleSleepColors[i];
            colors[idx] = THREE.MathUtils.lerp(pColA.r, pColS.r, pT);
            colors[idx + 1] = THREE.MathUtils.lerp(pColA.g, pColS.g, pT);
            colors[idx + 2] = THREE.MathUtils.lerp(pColA.b, pColS.b, pT);
        }

        this.particles.geometry.attributes.position.needsUpdate = true;
        this.particles.geometry.attributes.color.needsUpdate = true;
        this.particles.rotation.y += 0.005 * effectiveSpeed;

        this.renderer.render(this.scene, this.camera);
    }
}

window.PhoenixCore = PhoenixCore;
