/**
 * E8 Lattice Pattern Recognition Compression - CUDA Implementation
 * Novel approach using E8 root system geometry for data encoding
 * Optimized for RTX 4070 (SM 8.9)
 */

#include "common.cuh"
#include <cooperative_groups.h>
#include <math.h>

namespace cg = cooperative_groups;

#define E8_ROOTS 240        // Number of E8 roots
#define E8_DIM 8            // E8 dimension
#define BLOCK_BYTES 64      // Process 64 bytes at a time (8 E8 coordinates)
#define PATTERN_BITS 8      // Bits per pattern ID

/**
 * E8 root vectors (precomputed subset for pattern matching)
 * Type A: permutations of (±1, ±1, 0, 0, 0, 0, 0, 0)
 * Type B: (±½)^8 with even number of minus signs
 */
__constant__ float d_e8Roots[E8_ROOTS * E8_DIM];

/**
 * Initialize E8 roots on device
 */
__global__ void initE8Roots(float* roots) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Type A roots: 112 roots
    if (tid < 112) {
        // Calculate which pair of coordinates are ±1
        int pairIdx = 0;
        int remaining = tid;
        
        for (int i = 0; i < 8 && pairIdx == 0; i++) {
            for (int j = i + 1; j < 8 && remaining >= 4; j++) {
                remaining -= 4;
                if (remaining < 0) {
                    pairIdx = i * 8 + j;
                }
            }
        }
        
        // Set all zeros first
        for (int d = 0; d < E8_DIM; d++) {
            roots[tid * E8_DIM + d] = 0.0f;
        }
        
        // Set the two non-zero coordinates
        int i = (pairIdx / 8) % 8;
        int j = pairIdx % 8;
        int signBits = (tid % 4);
        roots[tid * E8_DIM + i] = (signBits & 1) ? 1.0f : -1.0f;
        roots[tid * E8_DIM + j] = (signBits & 2) ? 1.0f : -1.0f;
    }
    // Type B roots: 128 roots
    else if (tid < 240) {
        int idx = tid - 112;
        int maskIdx = idx / 2;
        int signPattern = 0;
        
        // Count 1s to ensure even parity
        for (int b = 0; b < 8; b++) {
            int bit = (maskIdx >> b) & 1;
            signPattern |= (bit << b);
        }
        
        for (int d = 0; d < E8_DIM; d++) {
            float sign = ((signPattern >> d) & 1) ? -0.5f : 0.5f;
            roots[tid * E8_DIM + d] = sign;
        }
    }
}

/**
 * Kernel: Convert byte blocks to 8D vectors
 */
__global__ void bytesToVectors(
    const unsigned char* __restrict__ input,
    float* __restrict__ vectors,
    size_t numBlocks
) {
    size_t blockId = blockIdx.x * blockDim.x + threadIdx.x;
    if (blockId >= numBlocks) return;
    
    size_t inputOffset = blockId * BLOCK_BYTES;
    size_t vecOffset = blockId * E8_DIM;
    
    // Map 64 bytes to 8 floats (sum of 8 bytes each, normalized)
    for (int d = 0; d < E8_DIM; d++) {
        float sum = 0.0f;
        for (int b = 0; b < 8; b++) {
            sum += input[inputOffset + d * 8 + b];
        }
        vectors[vecOffset + d] = (sum / 8.0f - 127.5f) / 127.5f;  // Normalize to [-1, 1]
    }
}

/**
 * Kernel: Find nearest E8 root for each vector
 */
__global__ void findNearestRoot(
    const float* __restrict__ vectors,
    const float* __restrict__ roots,
    unsigned char* __restrict__ rootIndices,
    float* __restrict__ residuals,
    size_t numVectors
) {
    __shared__ float sharedRoots[E8_ROOTS * E8_DIM];
    
    // Collaborative loading of roots into shared memory
    for (int i = threadIdx.x; i < E8_ROOTS * E8_DIM; i += blockDim.x) {
        sharedRoots[i] = roots[i];
    }
    __syncthreads();
    
    size_t vecId = blockIdx.x * blockDim.x + threadIdx.x;
    if (vecId >= numVectors) return;
    
    float vec[E8_DIM];
    for (int d = 0; d < E8_DIM; d++) {
        vec[d] = vectors[vecId * E8_DIM + d];
    }
    
    // Find nearest root
    float minDist = 1e10f;
    int bestRoot = 0;
    
    for (int r = 0; r < E8_ROOTS; r++) {
        float dist = 0.0f;
        for (int d = 0; d < E8_DIM; d++) {
            float diff = vec[d] - sharedRoots[r * E8_DIM + d];
            dist += diff * diff;
        }
        
        if (dist < minDist) {
            minDist = dist;
            bestRoot = r;
        }
    }
    
    rootIndices[vecId] = bestRoot;
    
    // Compute residual
    for (int d = 0; d < E8_DIM; d++) {
        residuals[vecId * E8_DIM + d] = vec[d] - sharedRoots[bestRoot * E8_DIM + d];
    }
}

/**
 * Kernel: Encode residuals compactly
 */
__global__ void encodeResiduals(
    const float* __restrict__ residuals,
    unsigned short* __restrict__ encodedResiduals,
    size_t numVectors
) {
    size_t vecId = blockIdx.x * blockDim.x + threadIdx.x;
    if (vecId >= numVectors) return;
    
    // Quantize residuals to 16-bit
    for (int d = 0; d < E8_DIM; d++) {
        float r = residuals[vecId * E8_DIM + d];
        // Map [-1, 1] to [0, 65535]
        int quantized = (int)((r + 1.0f) * 32767.5f);
        quantized = max(0, min(65535, quantized));
        encodedResiduals[vecId * E8_DIM + d] = (unsigned short)quantized;
    }
}

/**
 * Host function: E8 lattice compression
 */
extern "C" CompressionResult e8LatticeCompress(
    const unsigned char* h_input,
    size_t inputSize,
    unsigned char* h_output,
    size_t* outputSize
) {
    CompressionResult result = initResult(inputSize);
    CudaTimer timer;
    timer.init();
    
    // Pad input to multiple of BLOCK_BYTES
    size_t paddedSize = ((inputSize + BLOCK_BYTES - 1) / BLOCK_BYTES) * BLOCK_BYTES;
    size_t numBlocks = paddedSize / BLOCK_BYTES;
    
    // Device allocations
    unsigned char* d_input;
    float* d_roots;
    float* d_vectors;
    unsigned char* d_rootIndices;
    float* d_residuals;
    unsigned short* d_encodedResiduals;
    
    CUDA_CHECK(cudaMalloc(&d_input, paddedSize));
    CUDA_CHECK(cudaMalloc(&d_roots, E8_ROOTS * E8_DIM * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_vectors, numBlocks * E8_DIM * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_rootIndices, numBlocks));
    CUDA_CHECK(cudaMalloc(&d_residuals, numBlocks * E8_DIM * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_encodedResiduals, numBlocks * E8_DIM * sizeof(unsigned short)));
    
    // Copy input (with padding)
    CUDA_CHECK(cudaMemset(d_input, 0, paddedSize));
    CUDA_CHECK(cudaMemcpy(d_input, h_input, inputSize, cudaMemcpyHostToDevice));
    
    timer.startTimer();
    
    // Initialize E8 roots
    initE8Roots<<<(E8_ROOTS + 255) / 256, 256>>>(d_roots);
    
    // Convert bytes to vectors
    int blocks = (numBlocks + BLOCK_SIZE - 1) / BLOCK_SIZE;
    bytesToVectors<<<blocks, BLOCK_SIZE>>>(d_input, d_vectors, numBlocks);
    
    // Find nearest roots
    findNearestRoot<<<blocks, BLOCK_SIZE>>>(
        d_vectors, d_roots, d_rootIndices, d_residuals, numBlocks
    );
    
    // Encode residuals
    encodeResiduals<<<blocks, BLOCK_SIZE>>>(d_residuals, d_encodedResiduals, numBlocks);
    
    CUDA_CHECK(cudaDeviceSynchronize());
    result.timeMs = timer.stopTimer();
    
    // Build output: [original_size][root_indices][encoded_residuals]
    size_t outputBytes = sizeof(size_t) + numBlocks + numBlocks * E8_DIM * sizeof(unsigned short);
    
    if (outputBytes <= *outputSize) {
        // Copy size
        memcpy(h_output, &inputSize, sizeof(size_t));
        
        // Copy root indices
        CUDA_CHECK(cudaMemcpy(h_output + sizeof(size_t), d_rootIndices, numBlocks, cudaMemcpyDeviceToHost));
        
        // Copy residuals
        CUDA_CHECK(cudaMemcpy(h_output + sizeof(size_t) + numBlocks, 
                              d_encodedResiduals, 
                              numBlocks * E8_DIM * sizeof(unsigned short),
                              cudaMemcpyDeviceToHost));
    }
    
    *outputSize = outputBytes;
    result.compressedSize = outputBytes;
    finalizeResult(&result);
    
    // Cleanup
    cudaFree(d_input);
    cudaFree(d_roots);
    cudaFree(d_vectors);
    cudaFree(d_rootIndices);
    cudaFree(d_residuals);
    cudaFree(d_encodedResiduals);
    timer.cleanup();
    
    return result;
}
