/**
 * Common CUDA utilities for Compression Lab
 * Optimized for RTX 4070 (SM 8.9, Ada Lovelace)
 */

#ifndef COMPRESSION_COMMON_CUH
#define COMPRESSION_COMMON_CUH

#include <cuda_runtime.h>
#include <stdio.h>

// GPU specs for RTX 4070
#define WARP_SIZE 32
#define BLOCK_SIZE 256
#define MAX_SHARED_MEM 49152  // 48KB per block
#define VRAM_SIZE (12ULL * 1024 * 1024 * 1024)  // 12GB

// Error checking macro
#define CUDA_CHECK(call) do { \
    cudaError_t err = call; \
    if (err != cudaSuccess) { \
        fprintf(stderr, "CUDA error at %s:%d: %s\n", \
                __FILE__, __LINE__, cudaGetErrorString(err)); \
        exit(EXIT_FAILURE); \
    } \
} while(0)

// Timing utilities
struct CudaTimer {
    cudaEvent_t start, stop;
    
    void init() {
        cudaEventCreate(&start);
        cudaEventCreate(&stop);
    }
    
    void startTimer() {
        cudaEventRecord(start, 0);
    }
    
    float stopTimer() {
        cudaEventRecord(stop, 0);
        cudaEventSynchronize(stop);
        float ms;
        cudaEventElapsedTime(&ms, start, stop);
        return ms;
    }
    
    void cleanup() {
        cudaEventDestroy(start);
        cudaEventDestroy(stop);
    }
};

// Memory info
inline void printMemInfo(const char* tag) {
    size_t free, total;
    cudaMemGetInfo(&free, &total);
    printf("[%s] VRAM: %.2f GB / %.2f GB (%.1f%% used)\n",
           tag,
           (total - free) / 1e9,
           total / 1e9,
           100.0 * (total - free) / total);
}

// Result structure
struct CompressionResult {
    size_t originalSize;
    size_t compressedSize;
    float timeMs;
    float throughputGBps;
    float ratio;
    int errorCode;
};

// Initialize result
inline CompressionResult initResult(size_t originalSize) {
    CompressionResult r;
    r.originalSize = originalSize;
    r.compressedSize = 0;
    r.timeMs = 0;
    r.throughputGBps = 0;
    r.ratio = 0;
    r.errorCode = 0;
    return r;
}

// Calculate metrics
inline void finalizeResult(CompressionResult* r) {
    if (r->compressedSize > 0) {
        r->ratio = (float)r->originalSize / r->compressedSize;
    }
    if (r->timeMs > 0) {
        r->throughputGBps = (r->originalSize / 1e9) / (r->timeMs / 1000.0);
    }
}

#endif // COMPRESSION_COMMON_CUH
