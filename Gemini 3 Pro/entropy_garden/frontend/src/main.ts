/**
 * Entropy Garden - Main Entry Point
 * 
 * Real-time E8 lattice visualization driven by system telemetry.
 */

import { E8Renderer } from './renderer';
import { EntropyWebSocket, EntropyEvent } from './websocket';
import { PerfMonitor } from './perf';

// Global state
let renderer: E8Renderer;
let ws: EntropyWebSocket;
let perf: PerfMonitor;
let lastTime = 0;
let latestEvent: EntropyEvent | null = null;

// HUD elements
const elements = {
    entropyScore: document.getElementById('entropy-score'),
    entropyFill: document.getElementById('entropy-fill'),
    cpuUsage: document.getElementById('cpu-usage'),
    gpuUsage: document.getElementById('gpu-usage'),
    ramUsage: document.getElementById('ram-usage'),
    vramUsage: document.getElementById('vram-usage'),
    mappingMode: document.getElementById('mapping-mode') as HTMLSelectElement,
    intensity: document.getElementById('intensity') as HTMLInputElement,
    intensityValue: document.getElementById('intensity-value'),
};

/**
 * Update HUD with latest entropy event.
 */
function updateHUD(event: EntropyEvent): void {
    if (elements.entropyScore) {
        elements.entropyScore.textContent = event.entropy_score.toFixed(2);
    }

    if (elements.entropyFill) {
        elements.entropyFill.style.width = `${event.entropy_score * 100}%`;
    }

    if (elements.cpuUsage && event.cpu_percent_per_core.length > 0) {
        const avg = event.cpu_percent_per_core.reduce((a, b) => a + b, 0) / event.cpu_percent_per_core.length;
        elements.cpuUsage.textContent = `${avg.toFixed(0)}%`;
    }

    if (elements.gpuUsage) {
        elements.gpuUsage.textContent = `${event.gpu_util_percent.toFixed(0)}%`;
    }

    if (elements.ramUsage) {
        elements.ramUsage.textContent = `${event.ram_used_gb.toFixed(1)} / ${event.ram_total_gb.toFixed(0)} GB`;
    }

    if (elements.vramUsage) {
        elements.vramUsage.textContent = `${event.vram_used_gb.toFixed(1)} / ${event.vram_total_gb.toFixed(1)} GB`;
    }
}

/**
 * Main animation loop.
 * OPTIMIZED: Throttle HUD updates to 10Hz to avoid DOM thrashing.
 */
let lastHudUpdate = 0;

function animate(currentTime: number): void {
    const deltaTime = (currentTime - lastTime) / 1000;
    lastTime = currentTime;

    // Track performance
    perf.tick();

    // Update renderer with latest entropy data (cheap)
    if (latestEvent) {
        renderer.updateFromEntropy(latestEvent);
    }

    // Render 3D scene
    renderer.render(deltaTime);

    // Throttle HUD updates to 10Hz (DOM ops are expensive)
    if (currentTime - lastHudUpdate > 100) {
        if (latestEvent) {
            updateHUD(latestEvent);
        }
        perf.updateHUD();
        lastHudUpdate = currentTime;
    }

    requestAnimationFrame(animate);
}

/**
 * Setup control event listeners.
 */
function setupControls(): void {
    // Mapping mode selector
    if (elements.mappingMode) {
        elements.mappingMode.addEventListener('change', async (e) => {
            const mode = (e.target as HTMLSelectElement).value;
            try {
                await fetch(`/config/mapping?mode=${mode}&intensity=${elements.intensity?.value || 1}`, {
                    method: 'POST',
                });
                console.log(`Mapping mode changed to: ${mode}`);
            } catch (error) {
                console.error('Failed to update mapping mode:', error);
            }
        });
    }

    // Intensity slider
    if (elements.intensity && elements.intensityValue) {
        elements.intensity.addEventListener('input', async (e) => {
            const value = (e.target as HTMLInputElement).value;
            elements.intensityValue!.textContent = value;

            try {
                await fetch(`/config/mapping?mode=${elements.mappingMode?.value || 'balanced'}&intensity=${value}`, {
                    method: 'POST',
                });
            } catch (error) {
                console.error('Failed to update intensity:', error);
            }
        });
    }
}

/**
 * Initialize the application.
 */
async function init(): Promise<void> {
    console.log('🌿 Entropy Garden Initializing...');

    // Create renderer
    const container = document.getElementById('canvas-container');
    if (!container) {
        throw new Error('Canvas container not found');
    }
    renderer = new E8Renderer(container);
    console.log('✅ E8 Lattice rendered with 240 vertices');

    // Create performance monitor
    perf = new PerfMonitor(10, 144);

    // Create WebSocket connection
    ws = new EntropyWebSocket('ws://localhost:8080/ws/entropy');
    ws.onEvent((event) => {
        latestEvent = event;
    });
    ws.connect();

    // Setup UI controls
    setupControls();

    // Start animation loop
    lastTime = performance.now();
    requestAnimationFrame(animate);

    console.log('✅ Entropy Garden ready!');
}

// Start application
init().catch(console.error);
