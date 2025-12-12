/**
 * LZ77 Parallel Compression - CUDA Implementation
 * Sliding window parallelization with hash-based matching
 * Optimized for RTX 4070 (SM 8.9)
 */

#include "common.cuh"
#include <cooperative_groups.h>

namespace cg = cooperative_groups;

#define WINDOW_SIZE 32768      // 32KB sliding window
#define MIN_MATCH 3
#define MAX_MATCH 258
#define HASH_BITS 15
#define HASH_SIZE (1 << HASH_BITS)

/**
 * Hash function for 3-byte sequences
 */
__device__ __forceinline__ unsigned int hashFunc(
    unsigned char a, unsigned char b, unsigned char c
) {
    return ((a << 10) ^ (b << 5) ^ c) & (HASH_SIZE - 1);
}

/**
 * Kernel: Build hash table for match finding
 * Each thread processes one position
 */
__global__ void buildHashTable(
    const unsigned char* __restrict__ input,
    int* __restrict__ hashHead,
    int* __restrict__ hashPrev,
    size_t size
) {
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Initialize hash table
    if (idx < HASH_SIZE) {
        hashHead[idx] = -1;
    }
    
    __syncthreads();
    
    // Build hash chains (sequential per warp for correctness)
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        for (size_t i = 0; i + 2 < size; i++) {
            unsigned int h = hashFunc(input[i], input[i+1], input[i+2]);
            hashPrev[i] = hashHead[h];
            hashHead[h] = i;
        }
    }
}

/**
 * Kernel: Find best match at each position
 */
__global__ void findMatches(
    const unsigned char* __restrict__ input,
    const int* __restrict__ hashHead,
    const int* __restrict__ hashPrev,
    int* __restrict__ matchOffset,
    int* __restrict__ matchLength,
    size_t size
) {
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx + 2 >= size) {
        if (idx < size) {
            matchOffset[idx] = 0;
            matchLength[idx] = 0;
        }
        return;
    }
    
    unsigned int h = hashFunc(input[idx], input[idx+1], input[idx+2]);
    int bestLen = 0;
    int bestOff = 0;
    
    int pos = hashHead[h];
    int searchLimit = 64;  // Limit chain traversal
    
    while (pos >= 0 && idx - pos <= WINDOW_SIZE && searchLimit-- > 0) {
        // Check match length
        int len = 0;
        while (len < MAX_MATCH && idx + len < size && input[pos + len] == input[idx + len]) {
            len++;
        }
        
        if (len >= MIN_MATCH && len > bestLen) {
            bestLen = len;
            bestOff = idx - pos;
        }
        
        pos = hashPrev[pos];
    }
    
    matchOffset[idx] = bestOff;
    matchLength[idx] = bestLen;
}

/**
 * Kernel: Encode LZ77 tokens
 * Format: [0|literal] or [1|length|offset]
 */
__global__ void encodeTokens(
    const unsigned char* __restrict__ input,
    const int* __restrict__ matchOffset,
    const int* __restrict__ matchLength,
    unsigned int* __restrict__ output,
    unsigned int* __restrict__ outputPos,
    size_t size
) {
    // Single-threaded encoding for simplicity
    // In production, use parallel prefix sum for output positions
    if (threadIdx.x != 0 || blockIdx.x != 0) return;
    
    size_t outIdx = 0;
    size_t i = 0;
    
    while (i < size) {
        int len = matchLength[i];
        int off = matchOffset[i];
        
        if (len >= MIN_MATCH) {
            // Match token: [1][length-3][offset]
            output[outIdx++] = 0x80000000 | ((len - 3) << 16) | off;
            i += len;
        } else {
            // Literal byte
            output[outIdx++] = input[i];
            i++;
        }
    }
    
    *outputPos = outIdx;
}

/**
 * Host function: LZ77 compression
 */
extern "C" CompressionResult lz77Compress(
    const unsigned char* h_input,
    size_t inputSize,
    unsigned char* h_output,
    size_t* outputSize
) {
    CompressionResult result = initResult(inputSize);
    CudaTimer timer;
    timer.init();
    
    // Device allocations
    unsigned char* d_input;
    int* d_hashHead;
    int* d_hashPrev;
    int* d_matchOffset;
    int* d_matchLength;
    unsigned int* d_output;
    unsigned int* d_outputPos;
    
    CUDA_CHECK(cudaMalloc(&d_input, inputSize));
    CUDA_CHECK(cudaMalloc(&d_hashHead, HASH_SIZE * sizeof(int)));
    CUDA_CHECK(cudaMalloc(&d_hashPrev, inputSize * sizeof(int)));
    CUDA_CHECK(cudaMalloc(&d_matchOffset, inputSize * sizeof(int)));
    CUDA_CHECK(cudaMalloc(&d_matchLength, inputSize * sizeof(int)));
    CUDA_CHECK(cudaMalloc(&d_output, inputSize * sizeof(unsigned int)));
    CUDA_CHECK(cudaMalloc(&d_outputPos, sizeof(unsigned int)));
    
    // Copy input
    CUDA_CHECK(cudaMemcpy(d_input, h_input, inputSize, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemset(d_hashHead, 0xFF, HASH_SIZE * sizeof(int)));  // -1
    
    timer.startTimer();
    
    // Build hash table
    int blocks = (HASH_SIZE + BLOCK_SIZE - 1) / BLOCK_SIZE;
    buildHashTable<<<blocks, BLOCK_SIZE>>>(d_input, d_hashHead, d_hashPrev, inputSize);
    
    // Find matches
    blocks = (inputSize + BLOCK_SIZE - 1) / BLOCK_SIZE;
    findMatches<<<blocks, BLOCK_SIZE>>>(
        d_input, d_hashHead, d_hashPrev,
        d_matchOffset, d_matchLength, inputSize
    );
    
    // Encode tokens
    encodeTokens<<<1, 1>>>(
        d_input, d_matchOffset, d_matchLength,
        d_output, d_outputPos, inputSize
    );
    
    CUDA_CHECK(cudaDeviceSynchronize());
    result.timeMs = timer.stopTimer();
    
    // Get output size
    unsigned int numTokens;
    CUDA_CHECK(cudaMemcpy(&numTokens, d_outputPos, sizeof(unsigned int), cudaMemcpyDeviceToHost));
    
    size_t compressedBytes = numTokens * sizeof(unsigned int);
    if (compressedBytes <= *outputSize) {
        CUDA_CHECK(cudaMemcpy(h_output, d_output, compressedBytes, cudaMemcpyDeviceToHost));
    }
    
    *outputSize = compressedBytes;
    result.compressedSize = compressedBytes;
    finalizeResult(&result);
    
    // Cleanup
    cudaFree(d_input);
    cudaFree(d_hashHead);
    cudaFree(d_hashPrev);
    cudaFree(d_matchOffset);
    cudaFree(d_matchLength);
    cudaFree(d_output);
    cudaFree(d_outputPos);
    timer.cleanup();
    
    return result;
}
