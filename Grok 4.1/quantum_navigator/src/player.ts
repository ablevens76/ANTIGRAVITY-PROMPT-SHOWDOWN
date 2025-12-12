/**
 * Player controls for Quantum Navigator.
 * First-person flight with antigravity physics.
 */

import * as THREE from 'three';

export class Player {
    public position: THREE.Vector3;
    public velocity: THREE.Vector3;
    public rotation: THREE.Euler;

    private camera: THREE.PerspectiveCamera;
    private moveSpeed = 0.5;
    private boostMultiplier = 3;
    private friction = 0.98;
    private maxSpeed = 2;

    // Input state
    private keys: { [key: string]: boolean } = {};
    private mouseX = 0;
    private mouseY = 0;
    private mouseSensitivity = 0.002;
    private isPointerLocked = false;

    // Quantum state
    public isQuantumTunneling = false;
    public quantumCharge = 1.0;

    constructor(camera: THREE.PerspectiveCamera) {
        this.camera = camera;
        this.position = new THREE.Vector3(0, 0, 15);
        this.velocity = new THREE.Vector3();
        this.rotation = new THREE.Euler(0, 0, 0, 'YXZ');

        this.setupControls();
    }

    private setupControls(): void {
        // Keyboard
        document.addEventListener('keydown', (e) => {
            this.keys[e.code] = true;

            if (e.code === 'Space') {
                this.triggerQuantumTunnel();
            }
        });

        document.addEventListener('keyup', (e) => {
            this.keys[e.code] = false;
        });

        // Mouse look
        document.addEventListener('mousemove', (e) => {
            if (this.isPointerLocked) {
                this.mouseX += e.movementX * this.mouseSensitivity;
                this.mouseY += e.movementY * this.mouseSensitivity;
                this.mouseY = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.mouseY));
            }
        });

        // Pointer lock
        document.addEventListener('click', () => {
            document.body.requestPointerLock();
        });

        document.addEventListener('pointerlockchange', () => {
            this.isPointerLocked = document.pointerLockElement === document.body;
        });
    }

    triggerQuantumTunnel(): void {
        if (this.quantumCharge >= 0.5 && !this.isQuantumTunneling) {
            this.isQuantumTunneling = true;
            this.quantumCharge -= 0.3;

            // Teleport forward
            const forward = new THREE.Vector3(0, 0, -10);
            forward.applyEuler(this.rotation);
            this.position.add(forward);

            // Visual effect
            const overlay = document.getElementById('quantum-overlay');
            overlay?.classList.add('active');

            const stateEl = document.getElementById('quantum-state');
            if (stateEl) stateEl.textContent = 'SUPERPOSITION';

            setTimeout(() => {
                this.isQuantumTunneling = false;
                overlay?.classList.remove('active');
                if (stateEl) stateEl.textContent = 'COHERENT';
            }, 500);
        }
    }

    update(deltaTime: number, gravityWells: THREE.Vector3[] = []): void {
        // Calculate movement direction
        const forward = new THREE.Vector3(0, 0, -1).applyEuler(this.rotation);
        const right = new THREE.Vector3(1, 0, 0).applyEuler(this.rotation);
        const up = new THREE.Vector3(0, 1, 0);

        // Get speed multiplier
        const speed = this.keys['ShiftLeft'] ? this.moveSpeed * this.boostMultiplier : this.moveSpeed;

        // Apply input
        if (this.keys['KeyW']) this.velocity.addScaledVector(forward, speed * deltaTime * 60);
        if (this.keys['KeyS']) this.velocity.addScaledVector(forward, -speed * deltaTime * 60);
        if (this.keys['KeyA']) this.velocity.addScaledVector(right, -speed * deltaTime * 60);
        if (this.keys['KeyD']) this.velocity.addScaledVector(right, speed * deltaTime * 60);
        if (this.keys['KeyQ']) this.velocity.addScaledVector(up, -speed * deltaTime * 60);
        if (this.keys['KeyE']) this.velocity.addScaledVector(up, speed * deltaTime * 60);

        // Antigravity from wells (inverse square repulsion)
        for (const well of gravityWells) {
            const toWell = well.clone().sub(this.position);
            const dist = toWell.length();
            if (dist < 20 && dist > 0.1) {
                const force = toWell.normalize().multiplyScalar(-5 / (dist * dist));
                this.velocity.add(force);
            }
        }

        // Apply friction
        this.velocity.multiplyScalar(this.friction);

        // Clamp speed
        if (this.velocity.length() > this.maxSpeed) {
            this.velocity.normalize().multiplyScalar(this.maxSpeed);
        }

        // Update position
        this.position.addScaledVector(this.velocity, deltaTime * 60);

        // Apply mouse look
        this.rotation.y = -this.mouseX;
        this.rotation.x = -this.mouseY;

        // Update camera
        this.camera.position.copy(this.position);
        this.camera.rotation.copy(this.rotation);

        // Recharge quantum
        this.quantumCharge = Math.min(1, this.quantumCharge + deltaTime * 0.1);

        // Update HUD
        const velocityEl = document.getElementById('velocity');
        if (velocityEl) {
            velocityEl.textContent = (this.velocity.length() * 100).toFixed(0);
        }
    }

    getSpeed(): number {
        return this.velocity.length();
    }
}
