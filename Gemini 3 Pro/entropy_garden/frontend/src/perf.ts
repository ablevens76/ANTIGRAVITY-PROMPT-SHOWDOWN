/**
 * Performance monitoring for Entropy_Garden.
 * Tracks FPS with 10-second rolling window.
 */

export class PerfMonitor {
    private frameTimes: number[] = [];
    private lastFrameTime = 0;
    private readonly windowSize: number;

    // DOM elements
    private fpsElement: HTMLElement | null;
    private frameTimeElement: HTMLElement | null;

    constructor(windowSeconds: number = 10, targetFps: number = 60) {
        this.windowSize = windowSeconds * targetFps;
        this.fpsElement = document.getElementById('fps');
        this.frameTimeElement = document.getElementById('frame-time');
    }

    /**
     * Call this every frame to record timing.
     */
    tick(): void {
        const now = performance.now();

        if (this.lastFrameTime > 0) {
            const frameTime = now - this.lastFrameTime;
            this.frameTimes.push(frameTime);

            // Keep only windowSize samples
            while (this.frameTimes.length > this.windowSize) {
                this.frameTimes.shift();
            }
        }

        this.lastFrameTime = now;
    }

    /**
     * Get current performance statistics.
     */
    getStats(): { fps: number; avgFrameTime: number; variance: number; jitter: boolean } {
        if (this.frameTimes.length < 10) {
            return { fps: 0, avgFrameTime: 0, variance: 0, jitter: false };
        }

        const sum = this.frameTimes.reduce((a, b) => a + b, 0);
        const avgFrameTime = sum / this.frameTimes.length;
        const fps = 1000 / avgFrameTime;

        // Calculate variance
        const squaredDiffs = this.frameTimes.map(t => Math.pow(t - avgFrameTime, 2));
        const variance = squaredDiffs.reduce((a, b) => a + b, 0) / this.frameTimes.length;

        // Jitter if variance is high relative to frame time
        const jitter = Math.sqrt(variance) > avgFrameTime * 0.3;

        return { fps, avgFrameTime, variance, jitter };
    }

    /**
     * Update the HUD display.
     */
    updateHUD(): void {
        const stats = this.getStats();

        // Log to console for debugging
        console.log(`FPS: ${stats.fps.toFixed(0)}, Frame: ${stats.avgFrameTime.toFixed(1)}ms`);

        if (this.fpsElement) {
            const fpsText = stats.fps.toFixed(0);
            this.fpsElement.textContent = fpsText;

            // Color based on performance
            if (stats.fps >= 120) {
                this.fpsElement.className = 'fps-good';
            } else if (stats.fps >= 60) {
                this.fpsElement.className = 'fps-warn';
            } else {
                this.fpsElement.className = 'fps-bad';
            }
        }

        if (this.frameTimeElement) {
            this.frameTimeElement.textContent = stats.avgFrameTime.toFixed(1);
        }
    }

    /**
     * Check if performance is below target.
     */
    isBelowTarget(targetFps: number = 144): boolean {
        const stats = this.getStats();
        return stats.fps < targetFps || stats.jitter;
    }

    /**
     * Get optimization recommendations based on current performance.
     */
    getOptimizationHints(): string[] {
        const stats = this.getStats();
        const hints: string[] = [];

        if (stats.fps < 60) {
            hints.push('Critical: FPS below 60 - reduce geometry or disable effects');
        } else if (stats.fps < 120) {
            hints.push('Consider reducing sphere segments or using LOD');
        }

        if (stats.jitter) {
            hints.push('High frame time variance detected - check for GC or async issues');
        }

        return hints;
    }
}
