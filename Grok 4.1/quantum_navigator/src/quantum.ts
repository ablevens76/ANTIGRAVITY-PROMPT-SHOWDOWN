/**
 * Quantum visual effects for Quantum Navigator.
 * Particle superposition, tunneling effects, and ray-marched god rays.
 * Enhanced with Perlin noise and wavefunction collapse shaders.
 */

import * as THREE from 'three';

// GLSL Simplex Noise implementation (adapted from Ashima Arts)
const NOISE_GLSL = `
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    
    i = mod289(i);
    vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
        + i.y + vec4(0.0, i1.y, i2.y, 1.0))
        + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    
    vec4 x = x_ *ns.x + ns.yyyy;
    vec4 y = y_ *ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x;
    p1 *= norm.y;
    p2 *= norm.z;
    p3 *= norm.w;
    
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
`;

/**
 * Quantum particle system showing superposition/collapse.
 */
export class QuantumParticles {
    public mesh: THREE.Points;
    private positions: Float32Array;
    private velocities: Float32Array;
    private count: number;
    private time = 0;

    constructor(count: number = 2000) {
        this.count = count;
        this.positions = new Float32Array(count * 3);
        this.velocities = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const r = 20 + Math.random() * 30;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);

            this.positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            this.positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            this.positions[i * 3 + 2] = r * Math.cos(phi);

            this.velocities[i * 3] = (Math.random() - 0.5) * 0.05;
            this.velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.05;
            this.velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.05;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));

        const material = new THREE.PointsMaterial({
            color: 0x00ffff,
            size: 0.1,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending,
        });

        this.mesh = new THREE.Points(geometry, material);
    }

    update(deltaTime: number): void {
        this.time += deltaTime;

        for (let i = 0; i < this.count; i++) {
            const jitter = Math.sin(this.time * 10 + i) * 0.02;

            this.positions[i * 3] += this.velocities[i * 3] + jitter;
            this.positions[i * 3 + 1] += this.velocities[i * 3 + 1] + jitter;
            this.positions[i * 3 + 2] += this.velocities[i * 3 + 2];

            const dist = Math.sqrt(
                this.positions[i * 3] ** 2 +
                this.positions[i * 3 + 1] ** 2 +
                this.positions[i * 3 + 2] ** 2
            );

            if (dist > 60) {
                const scale = 20 / dist;
                this.positions[i * 3] *= scale;
                this.positions[i * 3 + 1] *= scale;
                this.positions[i * 3 + 2] *= scale;
            }
        }

        this.mesh.geometry.attributes.position.needsUpdate = true;
    }
}

/**
 * Wavefunction collapse effect for quantum tunneling.
 * Uses Schrödinger-like probability waves with Perlin noise.
 */
export function createWavefunctionCollapse(): THREE.Mesh {
    const geometry = new THREE.SphereGeometry(3, 64, 64);
    const material = new THREE.ShaderMaterial({
        uniforms: {
            uTime: { value: 0 },
            uIntensity: { value: 0 },
            uWellPos: { value: new THREE.Vector3(0, 0, 0) },
        },
        vertexShader: `
            varying vec3 vPosition;
            varying vec3 vNormal;
            varying vec3 vWorldPos;
            
            void main() {
                vPosition = position;
                vNormal = normalize(normalMatrix * normal);
                vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            ${NOISE_GLSL}
            
            uniform float uTime;
            uniform float uIntensity;
            uniform vec3 uWellPos;
            varying vec3 vPosition;
            varying vec3 vNormal;
            varying vec3 vWorldPos;
            
            float probabilityWave(vec3 pos, vec3 well, float chromaShift) {
                vec3 dir = pos - well;
                float dist = length(dir) * 0.1;
                float phase = uTime * 2.0 + dist * 5.0 + chromaShift;
                float noise = snoise(vec3(dir.xz * 0.5, phase * 0.3));
                return (sin(phase * 3.0) + 1.0) * 0.5 * (1.0 - smoothstep(0.0, 1.0, dist)) * (0.5 + noise * 0.5);
            }
            
            void main() {
                // RGB chromatic dispersion - different IOR per channel
                float waveR = probabilityWave(vPosition, uWellPos * vec3(1.0, 0.95, 1.05), 0.0);
                float waveG = probabilityWave(vPosition, uWellPos, 0.5);
                float waveB = probabilityWave(vPosition, uWellPos * vec3(0.95, 1.0, 1.05), 1.0);
                
                // Fresnel rim
                vec3 viewDir = normalize(cameraPosition - vWorldPos);
                float fresnel = pow(1.0 - abs(dot(vNormal, viewDir)), 3.0);
                
                // Final color with intensity
                vec3 waveColor = vec3(waveR, waveG, waveB) * uIntensity;
                waveColor += fresnel * vec3(0.3, 0.8, 1.0) * uIntensity;
                
                float alpha = (waveR + waveG + waveB) / 3.0 * uIntensity * 0.8;
                
                gl_FragColor = vec4(waveColor, alpha);
            }
        `,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.visible = false;
    return mesh;
}

/**
 * Volumetric god rays with ray marching.
 */
export function createGodRays(scene: THREE.Scene): THREE.Mesh {
    const geometry = new THREE.CylinderGeometry(0.5, 60, 120, 64, 1, true);
    const material = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            density: { value: 0.5 },
        },
        vertexShader: `
            varying vec2 vUv;
            varying vec3 vWorldPos;
            void main() {
                vUv = uv;
                vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            ${NOISE_GLSL}
            
            uniform float time;
            uniform float density;
            varying vec2 vUv;
            varying vec3 vWorldPos;
            
            float volumetricRay(vec2 uv, float t) {
                float rays = 0.0;
                for (int i = 0; i < 8; i++) {
                    float offset = float(i) * 0.125;
                    float angle = uv.x * 40.0 + t * 0.5 + offset * 6.28;
                    rays += sin(angle) * 0.5 + 0.5;
                    rays += snoise(vec3(uv * 10.0, t * 0.1)) * 0.2;
                }
                return rays / 8.0;
            }
            
            void main() {
                float heightFade = pow(1.0 - vUv.y, 2.5);
                float rays = volumetricRay(vUv, time);
                
                vec3 color1 = vec3(0.0, 0.8, 1.0);
                vec3 color2 = vec3(1.0, 0.0, 0.8);
                vec3 rayColor = mix(color1, color2, vUv.y + sin(time * 0.5) * 0.2);
                
                float alpha = rays * heightFade * density * 0.4;
                gl_FragColor = vec4(rayColor, alpha);
            }
        `,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(0, -40, 0);
    mesh.rotation.x = Math.PI;
    scene.add(mesh);

    return mesh;
}

/**
 * Starfield background.
 */
export function createStarfield(): THREE.Points {
    const count = 5000;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
        const r = 100 + Math.random() * 400;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);

        positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = r * Math.cos(phi);

        const temp = Math.random();
        colors[i * 3] = 0.8 + temp * 0.2;
        colors[i * 3 + 1] = 0.8 + temp * 0.1;
        colors[i * 3 + 2] = 1;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 0.5,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
    });

    return new THREE.Points(geometry, material);
}
