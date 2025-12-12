/**
 * Quantum Antigravity Navigator - Main Entry Point
 * 
 * A WebGL game where you fly through an E8 lattice with antigravity propulsion
 * and quantum superposition effects.
 */

import * as THREE from 'three';
import { generateE8Vertices, createE8LatticeMesh, createGravityWell } from './e8lattice';
import { Player } from './player';
import { QuantumParticles, createGodRays, createStarfield, createWavefunctionCollapse } from './quantum';

// Game state
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let player: Player;
let quantumParticles: QuantumParticles;
let wavefunctionMesh: THREE.Mesh;
let clock: THREE.Clock;

// FPS tracking
let frameCount = 0;
let lastFpsUpdate = 0;
let currentFps = 0;

// E8 lattice data
let e8Vertices: THREE.Vector3[];
let gravityWellPositions: THREE.Vector3[] = [];

/**
 * Initialize the game.
 */
function init(): void {
    console.log('🚀 Quantum Antigravity Navigator initializing...');

    // Scene
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000011, 0.01);

    // Camera
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 15);

    // Renderer
    renderer = new THREE.WebGLRenderer({
        antialias: true,
        powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    const container = document.getElementById('game-container');
    container?.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x111122, 0.5);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00ffff, 2, 100);
    pointLight.position.set(0, 10, 0);
    scene.add(pointLight);

    const pointLight2 = new THREE.PointLight(0xff00ff, 1, 80);
    pointLight2.position.set(-20, -5, 10);
    scene.add(pointLight2);

    // E8 Lattice
    e8Vertices = generateE8Vertices();
    const latticeMesh = createE8LatticeMesh(e8Vertices);
    scene.add(latticeMesh);

    // Create gravity wells at some E8 vertices
    for (let i = 0; i < 10; i++) {
        const idx = Math.floor(Math.random() * e8Vertices.length);
        const well = createGravityWell(e8Vertices[idx]);
        scene.add(well);
        gravityWellPositions.push(e8Vertices[idx]);
    }

    // Quantum particles
    quantumParticles = new QuantumParticles(3000);
    scene.add(quantumParticles.mesh);

    // God rays
    createGodRays(scene);

    // Starfield
    scene.add(createStarfield());

    // Wavefunction collapse effect (for quantum tunneling)
    wavefunctionMesh = createWavefunctionCollapse();
    scene.add(wavefunctionMesh);

    // Player
    player = new Player(camera);

    // Clock
    clock = new THREE.Clock();

    // Handle resize
    window.addEventListener('resize', onResize);

    // Update node count in HUD
    const nodesEl = document.getElementById('nodes');
    if (nodesEl) nodesEl.textContent = e8Vertices.length.toString();

    console.log('✅ Quantum Navigator ready!');
    console.log(`   E8 Lattice: ${e8Vertices.length} vertices`);
    console.log(`   Gravity Wells: ${gravityWellPositions.length}`);
    console.log(`   Quantum Particles: 3000`);

    // Start game loop
    animate();
}

/**
 * Main animation loop.
 */
function animate(): void {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();
    const elapsed = clock.getElapsedTime();

    // Update player
    player.update(delta, gravityWellPositions);

    // Update quantum particles
    quantumParticles.update(delta);

    // Update shader uniforms
    scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh && obj.material instanceof THREE.ShaderMaterial) {
            if (obj.material.uniforms.time) {
                obj.material.uniforms.time.value = elapsed;
            }
            if (obj.material.uniforms.uTime) {
                obj.material.uniforms.uTime.value = elapsed;
            }
        }
    });

    // Update wavefunction effect (follows player, visible during tunneling)
    wavefunctionMesh.position.copy(player.position);
    wavefunctionMesh.visible = player.isQuantumTunneling;
    if (player.isQuantumTunneling && wavefunctionMesh.material instanceof THREE.ShaderMaterial) {
        wavefunctionMesh.material.uniforms.uIntensity.value = 1.0;
        wavefunctionMesh.material.uniforms.uWellPos.value.copy(player.position);
    }

    // Render
    renderer.render(scene, camera);

    // FPS tracking
    frameCount++;
    if (elapsed - lastFpsUpdate >= 1) {
        currentFps = frameCount;
        frameCount = 0;
        lastFpsUpdate = elapsed;

        const fpsEl = document.getElementById('fps');
        if (fpsEl) fpsEl.textContent = currentFps.toString();
    }
}

/**
 * Handle window resize.
 */
function onResize(): void {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

// Start the game
init();
