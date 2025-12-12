/**
 * E8 Lattice Mathematics for Entropy_Garden
 * 
 * Computes the 240 roots of the E8 lattice and projects them to 3D.
 * 
 * E8 roots consist of:
 * - 112 roots: all permutations of (±1, ±1, 0, 0, 0, 0, 0, 0)
 * - 128 roots: all (±½, ±½, ±½, ±½, ±½, ±½, ±½, ±½) with even number of minus signs
 */

/** 8D vector type */
export type Vec8 = [number, number, number, number, number, number, number, number];

/** 3D vector type */
export type Vec3 = [number, number, number];

/**
 * Generate all E8 root vectors (240 total).
 */
export function generateE8Roots(): Vec8[] {
    const roots: Vec8[] = [];

    // Type 1: 112 roots - all permutations of (±1, ±1, 0, 0, 0, 0, 0, 0)
    for (let i = 0; i < 8; i++) {
        for (let j = i + 1; j < 8; j++) {
            for (const s1 of [-1, 1]) {
                for (const s2 of [-1, 1]) {
                    const root: Vec8 = [0, 0, 0, 0, 0, 0, 0, 0];
                    root[i] = s1;
                    root[j] = s2;
                    roots.push(root);
                }
            }
        }
    }

    // Type 2: 128 roots - (±½, ±½, ±½, ±½, ±½, ±½, ±½, ±½) with even minus signs
    for (let mask = 0; mask < 256; mask++) {
        // Count number of 1 bits (minus signs)
        let minusCount = 0;
        for (let b = 0; b < 8; b++) {
            if (mask & (1 << b)) minusCount++;
        }

        // Only include if even number of minus signs
        if (minusCount % 2 === 0) {
            const root: Vec8 = [0, 0, 0, 0, 0, 0, 0, 0];
            for (let b = 0; b < 8; b++) {
                root[b] = (mask & (1 << b)) ? -0.5 : 0.5;
            }
            roots.push(root);
        }
    }

    return roots;
}

/**
 * Create a random orthogonal projection matrix from 8D to 3D.
 * Uses Gram-Schmidt orthogonalization for aesthetic viewing angles.
 */
export function createProjectionMatrix(): number[][] {
    // Start with random 8D vectors
    const randomVec = (): number[] => {
        const v = [];
        for (let i = 0; i < 8; i++) {
            v.push(Math.random() * 2 - 1);
        }
        return v;
    };

    const normalize = (v: number[]): number[] => {
        const len = Math.sqrt(v.reduce((sum, x) => sum + x * x, 0));
        return v.map(x => x / len);
    };

    const dot = (a: number[], b: number[]): number => {
        return a.reduce((sum, x, i) => sum + x * b[i], 0);
    };

    const subtract = (a: number[], b: number[]): number[] => {
        return a.map((x, i) => x - b[i]);
    };

    const scale = (v: number[], s: number): number[] => {
        return v.map(x => x * s);
    };

    // Gram-Schmidt orthogonalization
    const v1 = normalize(randomVec());

    let v2 = randomVec();
    v2 = subtract(v2, scale(v1, dot(v2, v1)));
    v2 = normalize(v2);

    let v3 = randomVec();
    v3 = subtract(v3, scale(v1, dot(v3, v1)));
    v3 = subtract(v3, scale(v2, dot(v3, v2)));
    v3 = normalize(v3);

    return [v1, v2, v3];
}

/**
 * Project an 8D vector to 3D using the projection matrix.
 */
export function projectTo3D(v8: Vec8, projMatrix: number[][]): Vec3 {
    const result: Vec3 = [0, 0, 0];

    for (let row = 0; row < 3; row++) {
        let sum = 0;
        for (let col = 0; col < 8; col++) {
            sum += projMatrix[row][col] * v8[col];
        }
        result[row] = sum;
    }

    return result;
}

/**
 * Project all E8 roots to 3D.
 */
export function projectE8ToThreeD(roots: Vec8[], projMatrix: number[][]): Vec3[] {
    return roots.map(r => projectTo3D(r, projMatrix));
}

/**
 * Create a deterministic but visually pleasing projection matrix.
 * Uses golden ratio based angles for rotation.
 */
export function createDeterministicProjection(): number[][] {
    const phi = (1 + Math.sqrt(5)) / 2; // Golden ratio

    // Use phi-based angles for rotations
    const angles = [
        Math.PI / phi,
        Math.PI / (phi * phi),
        Math.PI / (phi * phi * phi),
    ];

    // Create rotation matrices and compose them
    const createRotationPlane = (i: number, j: number, angle: number): number[][] => {
        const mat: number[][] = [];
        for (let r = 0; r < 8; r++) {
            mat[r] = [];
            for (let c = 0; c < 8; c++) {
                if (r === c) mat[r][c] = 1;
                else mat[r][c] = 0;
            }
        }
        mat[i][i] = Math.cos(angle);
        mat[i][j] = -Math.sin(angle);
        mat[j][i] = Math.sin(angle);
        mat[j][j] = Math.cos(angle);
        return mat;
    };

    // Apply rotations in different planes
    const rot1 = createRotationPlane(0, 4, angles[0]);
    const rot2 = createRotationPlane(1, 5, angles[1]);
    const rot3 = createRotationPlane(2, 6, angles[2]);

    // Extract first 3 rows as projection
    const proj: number[][] = [
        [rot1[0][0], rot1[0][1], rot1[0][2], rot1[0][3], rot1[0][4], rot1[0][5], rot1[0][6], rot1[0][7]],
        [rot2[1][0], rot2[1][1], rot2[1][2], rot2[1][3], rot2[1][4], rot2[1][5], rot2[1][6], rot2[1][7]],
        [rot3[2][0], rot3[2][1], rot3[2][2], rot3[2][3], rot3[2][4], rot3[2][5], rot3[2][6], rot3[2][7]],
    ];

    return proj;
}

/**
 * Compute the full E8 lattice data with precomputed 3D positions.
 */
export interface E8LatticeData {
    roots8D: Vec8[];
    vertices3D: Vec3[];
    projectionMatrix: number[][];
    vertexCount: number;
}

export function computeE8Lattice(): E8LatticeData {
    const roots8D = generateE8Roots();
    const projectionMatrix = createDeterministicProjection();
    const vertices3D = projectE8ToThreeD(roots8D, projectionMatrix);

    // Normalize to unit sphere for consistent scale
    let maxDist = 0;
    for (const v of vertices3D) {
        const dist = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
        if (dist > maxDist) maxDist = dist;
    }

    const normalizedVertices = vertices3D.map(v =>
        [v[0] / maxDist, v[1] / maxDist, v[2] / maxDist] as Vec3
    );

    console.log(`E8 Lattice computed: ${roots8D.length} roots → ${normalizedVertices.length} 3D vertices`);

    return {
        roots8D,
        vertices3D: normalizedVertices,
        projectionMatrix,
        vertexCount: 240,
    };
}
