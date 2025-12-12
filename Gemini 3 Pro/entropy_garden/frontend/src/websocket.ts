/**
 * WebSocket client for Entropy_Garden telemetry stream.
 */

export interface EntropyEvent {
    timestamp: number;
    entropy_score: number;
    dominant_metric: string;
    intensity: number;
    cpu_percent_per_core: number[];
    load_average: number[];
    context_switches_per_sec: number;
    ram_used_gb: number;
    ram_total_gb: number;
    gpu_util_percent: number;
    vram_used_gb: number;
    vram_total_gb: number;
    gpu_temp_celsius: number;
}

export type EventCallback = (event: EntropyEvent) => void;

export class EntropyWebSocket {
    private ws: WebSocket | null = null;
    private url: string;
    private reconnectDelay = 1000;
    private maxReconnectDelay = 10000;
    private callbacks: EventCallback[] = [];
    private _connected = false;

    constructor(url: string = 'ws://localhost:8080/ws/entropy') {
        this.url = url;
    }

    get connected(): boolean {
        return this._connected;
    }

    connect(): void {
        if (this.ws) {
            this.ws.close();
        }

        console.log(`🔌 Connecting to ${this.url}...`);
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('✅ WebSocket connected');
            this._connected = true;
            this.reconnectDelay = 1000;
            this.updateStatus(true);
        };

        this.ws.onmessage = (event) => {
            try {
                const data: EntropyEvent = JSON.parse(event.data);
                this.callbacks.forEach(cb => cb(data));
            } catch (e) {
                console.error('Failed to parse entropy event:', e);
            }
        };

        this.ws.onclose = () => {
            console.log('❌ WebSocket disconnected');
            this._connected = false;
            this.updateStatus(false);
            this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    private scheduleReconnect(): void {
        console.log(`🔄 Reconnecting in ${this.reconnectDelay}ms...`);
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
    }

    private updateStatus(connected: boolean): void {
        const indicator = document.getElementById('connection-status');
        const text = document.getElementById('status-text');

        if (indicator) {
            indicator.className = connected ? 'connected' : 'disconnected';
        }
        if (text) {
            text.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }

    onEvent(callback: EventCallback): void {
        this.callbacks.push(callback);
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
