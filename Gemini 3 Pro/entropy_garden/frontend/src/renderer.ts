/**
 * Three.js Renderer for Entropy_Garden E8 Lattice Visualization.
 * Production version with lightweight Points and throttled animation.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { computeE8Lattice, E8LatticeData } from './e8lattice';
import { EntropyEvent } from './websocket';

export class E8Renderer {
    private scene: THREE.Scene;
    private camera: THREE.PerspectiveCamera;
    private renderer: THREE.WebGLRenderer;
    private controls: OrbitControls;
    private latticeData: E8LatticeData;
    private points!: THREE.Points;
    private positions!: Float32Array;
    private colors!: Float32Array;

    private time = 0;
    private currentEntropy = 0;
    private targetEntropy = 0;
    private intensity = 1.0;
    private lastAnimTime = 0;

    constructor(container: HTMLElement) {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0f);

        // Add fog for depth
        this.scene.fog = new THREE.FogExp2(0x0a0a0f, 0.3);

        // Camera
        this.camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
        this.camera.position.set(0, 0, 3);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            powerPreference: 'high-performance',
        });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.autoRotate = true;
        this.controls.autoRotateSpeed = 0.5;

        // Compute E8 lattice
        this.latticeData = computeE8Lattice();

        // Create point cloud
        this.createPointCloud();

        // Resize
        window.addEventListener('resize', () => this.onResize());

        console.log('🌿 E8 Renderer: 240 vertices initialized');
    }

    private createPointCloud(): void {
        const count = this.latticeData.vertexCount;
        this.positions = new Float32Array(count * 3);
        this.colors = new Float32Array(count * 3);

        for (let i = 0; i < count; i++) {
            const v = this.latticeData.vertices3D[i];
            this.positions[i * 3] = v[0];
            this.positions[i * 3 + 1] = v[1];
            this.positions[i * 3 + 2] = v[2];

            // Initial green color
            this.colors[i * 3] = 0.3;
            this.colors[i * 3 + 1] = 0.8;
            this.colors[i * 3 + 2] = 0.5;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(this.colors, 3));

        const material = new THREE.PointsMaterial({
            size: 0.04,
            vertexColors: true,
            sizeAttenuation: true,
            transparent: true,
            opacity: 0.9,
        });

        this.points = new THREE.Points(geometry, material);
        this.scene.add(this.points);
    }

    updateFromEntropy(event: EntropyEvent): void {
        this.targetEntropy = event.entropy_score;
        this.intensity = event.intensity;
    }

    private animatePoints(): void {
        const now = performance.now();

        // Throttle to 30Hz
        if (now - this.lastAnimTime < 33) return;
        this.lastAnimTime = now;

        // Smooth transition
        this.currentEntropy += (this.targetEntropy - this.currentEntropy) * 0.1;
        const effect = this.currentEntropy * this.intensity;

        const count = this.latticeData.vertexCount;

        for (let i = 0; i < count; i++) {
            const base = this.latticeData.vertices3D[i];

            // Wobble animation
            const wobble = effect > 0.01
                ? Math.sin(this.time * 2 + i * 0.05) * 0.03 * effect
                : 0;

            this.positions[i * 3] = base[0] * (1 + wobble);
            this.positions[i * 3 + 1] = base[1] * (1 + wobble);
            this.positions[i * 3 + 2] = base[2] * (1 + wobble);

            // Color: green to red based on entropy
            this.colors[i * 3] = Math.min(1, effect * 2);
            this.colors[i * 3 + 1] = Math.max(0, 0.8 - effect);
            this.colors[i * 3 + 2] = 0.3;
        }

        this.points.geometry.attributes.position.needsUpdate = true;
        this.points.geometry.attributes.color.needsUpdate = true;
    }

    render(deltaTime: number): void {
        this.time += deltaTime;
        this.animatePoints();
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    private onResize(): void {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    getInfo(): { triangles: number; calls: number } {
        return {
            triangles: this.renderer.info.render.triangles,
            calls: this.renderer.info.render.calls
        };
    }

    dispose(): void {
        this.renderer.dispose();
        this.points.geometry.dispose();
        (this.points.material as THREE.Material).dispose();
    }
}
