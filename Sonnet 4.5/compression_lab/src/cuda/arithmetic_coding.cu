/**
 * Arithmetic Coding - CUDA Implementation
 * Parallel entropy estimation and range encoding
 * Optimized for RTX 4070 (SM 8.9)
 */

#include "common.cuh"
#include <cooperative_groups.h>

namespace cg = cooperative_groups;

#define ALPHABET_SIZE 256
#define PRECISION_BITS 32
#define MAX_RANGE ((1ULL << 32) - 1)

/**
 * Kernel: Parallel frequency counting
 * Each block counts frequencies for a chunk, then atomically merges
 */
__global__ void countFrequencies(
    const unsigned char* __restrict__ input,
    unsigned int* __restrict__ globalFreq,
    size_t size
) {
    __shared__ unsigned int localFreq[ALPHABET_SIZE];
    
    // Initialize shared memory
    for (int i = threadIdx.x; i < ALPHABET_SIZE; i += blockDim.x) {
        localFreq[i] = 0;
    }
    __syncthreads();
    
    // Count frequencies in this block's range
    size_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    size_t stride = blockDim.x * gridDim.x;
    
    for (size_t i = idx; i < size; i += stride) {
        atomicAdd(&localFreq[input[i]], 1);
    }
    __syncthreads();
    
    // Merge to global
    for (int i = threadIdx.x; i < ALPHABET_SIZE; i += blockDim.x) {
        if (localFreq[i] > 0) {
            atomicAdd(&globalFreq[i], localFreq[i]);
        }
    }
}

/**
 * Kernel: Build cumulative distribution (prefix sum)
 */
__global__ void buildCDF(
    const unsigned int* __restrict__ freq,
    unsigned int* __restrict__ cdf,
    unsigned int total
) {
    __shared__ unsigned int temp[ALPHABET_SIZE];
    
    int tid = threadIdx.x;
    
    // Load
    if (tid < ALPHABET_SIZE) {
        temp[tid] = freq[tid];
    }
    __syncthreads();
    
    // Prefix sum (Blelloch scan)
    for (int offset = 1; offset < ALPHABET_SIZE; offset *= 2) {
        int val = 0;
        if (tid >= offset && tid < ALPHABET_SIZE) {
            val = temp[tid - offset];
        }
        __syncthreads();
        if (tid >= offset && tid < ALPHABET_SIZE) {
            temp[tid] += val;
        }
        __syncthreads();
    }
    
    // Exclusive scan adjustment
    if (tid < ALPHABET_SIZE) {
        cdf[tid] = (tid == 0) ? 0 : temp[tid - 1];
    }
}

/**
 * Kernel: Parallel arithmetic encoding (block-wise)
 * Each block encodes a chunk independently
 */
__global__ void encodeBlocks(
    const unsigned char* __restrict__ input,
    const unsigned int* __restrict__ cdf,
    unsigned int total,
    unsigned int* __restrict__ output,
    unsigned int* __restrict__ outputLengths,
    size_t chunkSize,
    size_t numChunks
) {
    int blockId = blockIdx.x;
    if (blockId >= numChunks) return;
    
    // Each block processes one chunk
    size_t start = blockId * chunkSize;
    size_t end = min(start + chunkSize, (size_t)(numChunks * chunkSize));
    
    // Thread 0 does encoding for this block (serial within block)
    if (threadIdx.x == 0) {
        unsigned long long low = 0;
        unsigned long long range = MAX_RANGE;
        
        unsigned int outputWord = 0;
        int bitsInWord = 0;
        int outputIdx = 0;
        
        for (size_t i = start; i < end; i++) {
            unsigned char symbol = input[i];
            unsigned int symLow = cdf[symbol];
            unsigned int symHigh = (symbol < 255) ? cdf[symbol + 1] : total;
            unsigned int symRange = symHigh - symLow;
            
            // Update range
            low = low + (range * symLow) / total;
            range = (range * symRange) / total;
            
            // Renormalization
            while (range < (1ULL << 24)) {
                // Output bits
                outputWord = (outputWord << 8) | ((low >> 24) & 0xFF);
                bitsInWord += 8;
                
                if (bitsInWord >= 32) {
                    output[blockId * (chunkSize / 4 + 64) + outputIdx++] = outputWord;
                    outputWord = 0;
                    bitsInWord = 0;
                }
                
                low <<= 8;
                range <<= 8;
            }
        }
        
        // Flush remaining
        if (bitsInWord > 0) {
            output[blockId * (chunkSize / 4 + 64) + outputIdx++] = outputWord << (32 - bitsInWord);
        }
        
        outputLengths[blockId] = outputIdx * 4;
    }
}

/**
 * Host function: Arithmetic coding compression
 */
extern "C" CompressionResult arithmeticCompress(
    const unsigned char* h_input,
    size_t inputSize,
    unsigned char* h_output,
    size_t* outputSize
) {
    CompressionResult result = initResult(inputSize);
    CudaTimer timer;
    timer.init();
    
    // Allocate device memory
    unsigned char* d_input;
    unsigned int* d_freq;
    unsigned int* d_cdf;
    unsigned int* d_output;
    unsigned int* d_outputLengths;
    
    CUDA_CHECK(cudaMalloc(&d_input, inputSize));
    CUDA_CHECK(cudaMalloc(&d_freq, ALPHABET_SIZE * sizeof(unsigned int)));
    CUDA_CHECK(cudaMalloc(&d_cdf, ALPHABET_SIZE * sizeof(unsigned int)));
    
    // Chunk parameters
    size_t chunkSize = 4096;
    size_t numChunks = (inputSize + chunkSize - 1) / chunkSize;
    size_t maxOutputPerChunk = chunkSize / 4 + 64;
    
    CUDA_CHECK(cudaMalloc(&d_output, numChunks * maxOutputPerChunk * sizeof(unsigned int)));
    CUDA_CHECK(cudaMalloc(&d_outputLengths, numChunks * sizeof(unsigned int)));
    
    // Copy input
    CUDA_CHECK(cudaMemcpy(d_input, h_input, inputSize, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemset(d_freq, 0, ALPHABET_SIZE * sizeof(unsigned int)));
    
    timer.startTimer();
    
    // Count frequencies
    int freqBlocks = (inputSize + BLOCK_SIZE - 1) / BLOCK_SIZE;
    countFrequencies<<<freqBlocks, BLOCK_SIZE>>>(d_input, d_freq, inputSize);
    
    // Build CDF
    buildCDF<<<1, ALPHABET_SIZE>>>(d_freq, d_cdf, inputSize);
    
    // Encode blocks
    encodeBlocks<<<numChunks, 32>>>(
        d_input, d_cdf, inputSize,
        d_output, d_outputLengths,
        chunkSize, numChunks
    );
    
    CUDA_CHECK(cudaDeviceSynchronize());
    result.timeMs = timer.stopTimer();
    
    // Copy output lengths and calculate total
    unsigned int* h_outputLengths = new unsigned int[numChunks];
    CUDA_CHECK(cudaMemcpy(h_outputLengths, d_outputLengths, 
                          numChunks * sizeof(unsigned int), cudaMemcpyDeviceToHost));
    
    size_t totalOutput = 0;
    for (size_t i = 0; i < numChunks; i++) {
        totalOutput += h_outputLengths[i];
    }
    
    // Copy compressed data (simplified - just copy first chunk for demo)
    if (totalOutput > 0 && totalOutput <= *outputSize) {
        CUDA_CHECK(cudaMemcpy(h_output, d_output, totalOutput, cudaMemcpyDeviceToHost));
        *outputSize = totalOutput;
    } else {
        *outputSize = totalOutput;
    }
    
    result.compressedSize = totalOutput;
    finalizeResult(&result);
    
    // Cleanup
    delete[] h_outputLengths;
    cudaFree(d_input);
    cudaFree(d_freq);
    cudaFree(d_cdf);
    cudaFree(d_output);
    cudaFree(d_outputLengths);
    timer.cleanup();
    
    return result;
}
