/**
 * E8 Lattice Geometry for Quantum Navigator
 * 
 * Generates the authentic 240 roots of the E8 lattice.
 * Uses even coordinate lattice: all coordinates ±1 or ±½ with even sum.
 * Stereographically projected to 3D.
 */

import * as THREE from 'three';

const SCALE = 5;  // World scale

/**
 * Generate the authentic 240 roots of E8.
 * 
 * E8 roots consist of:
 * - 112 roots: all permutations of (±1, ±1, 0, 0, 0, 0, 0, 0) - Type A
 * - 128 roots: all (±½)^8 with even number of minus signs - Type B
 */
export function generateE8Vertices(): THREE.Vector3[] {
    const roots8D: number[][] = [];

    // Type A: 112 roots - permutations of (±1, ±1, 0, 0, 0, 0, 0, 0)
    for (let i = 0; i < 8; i++) {
        for (let j = i + 1; j < 8; j++) {
            for (const s1 of [-1, 1]) {
                for (const s2 of [-1, 1]) {
                    const root = [0, 0, 0, 0, 0, 0, 0, 0];
                    root[i] = s1;
                    root[j] = s2;
                    roots8D.push(root);
                }
            }
        }
    }

    // Type B: 128 roots - (±½)^8 with even number of minus signs
    for (let mask = 0; mask < 256; mask++) {
        let minusCount = 0;
        for (let b = 0; b < 8; b++) {
            if (mask & (1 << b)) minusCount++;
        }

        if (minusCount % 2 === 0) {
            const root: number[] = [];
            for (let b = 0; b < 8; b++) {
                root.push((mask & (1 << b)) ? -0.5 : 0.5);
            }
            roots8D.push(root);
        }
    }

    console.log(`E8: Generated ${roots8D.length} roots in 8D`);

    // Stereographic projection from 8D to 3D
    // Using projection onto first 3 coordinates with depth scaling
    const vertices3D: THREE.Vector3[] = [];

    for (const r of roots8D) {
        // Use first 3 coords, scaled by higher-dimensional depth
        const depthFactor = 1 + (r[3] + r[4] + r[5] + r[6] + r[7]) * 0.1;

        vertices3D.push(new THREE.Vector3(
            r[0] * SCALE * depthFactor,
            r[1] * SCALE * depthFactor,
            r[2] * SCALE * depthFactor
        ));
    }

    // Normalize to consistent sphere radius
    let maxDist = 0;
    for (const v of vertices3D) {
        const d = v.length();
        if (d > maxDist) maxDist = d;
    }

    for (const v of vertices3D) {
        v.multiplyScalar(SCALE * 1.5 / maxDist);
    }

    console.log(`E8: Projected to ${vertices3D.length} 3D vertices`);
    return vertices3D;
}

/**
 * Create instanced E8 lattice mesh for high performance.
 */
export function createE8LatticeMesh(vertices: THREE.Vector3[]): THREE.Group {
    const group = new THREE.Group();

    // Instanced node spheres (much faster than individual meshes)
    const nodeGeometry = new THREE.SphereGeometry(0.12, 12, 12);
    const nodeMaterial = new THREE.MeshPhongMaterial({
        color: 0x00ffff,
        emissive: 0x002222,
        shininess: 80,
    });

    const nodesMesh = new THREE.InstancedMesh(nodeGeometry, nodeMaterial, vertices.length);
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();

    for (let i = 0; i < vertices.length; i++) {
        dummy.position.copy(vertices[i]);
        dummy.updateMatrix();
        nodesMesh.setMatrixAt(i, dummy.matrix);

        // Color gradient based on position
        const hue = 0.5 + vertices[i].y / 20;
        color.setHSL(hue, 0.8, 0.5);
        nodesMesh.setColorAt(i, color);
    }

    nodesMesh.instanceMatrix.needsUpdate = true;
    if (nodesMesh.instanceColor) nodesMesh.instanceColor.needsUpdate = true;
    group.add(nodesMesh);

    // Edges connecting nearby vertices (using BufferGeometry for efficiency)
    const edgeMaterial = new THREE.LineBasicMaterial({
        color: 0x0066aa,
        transparent: true,
        opacity: 0.25,
    });

    const edgePositions: number[] = [];
    const threshold = 3.5;  // Connect vertices within this distance

    for (let i = 0; i < vertices.length; i++) {
        for (let j = i + 1; j < vertices.length; j++) {
            if (vertices[i].distanceTo(vertices[j]) < threshold) {
                edgePositions.push(
                    vertices[i].x, vertices[i].y, vertices[i].z,
                    vertices[j].x, vertices[j].y, vertices[j].z
                );
            }
        }
    }

    const edgeGeometry = new THREE.BufferGeometry();
    edgeGeometry.setAttribute('position', new THREE.Float32BufferAttribute(edgePositions, 3));
    const edges = new THREE.LineSegments(edgeGeometry, edgeMaterial);
    group.add(edges);

    console.log(`E8 Mesh: ${vertices.length} nodes, ${edgePositions.length / 6} edges`);

    return group;
}

/**
 * Create gravity well effect with advanced dispersion shader.
 */
export function createGravityWell(position: THREE.Vector3): THREE.Mesh {
    const geometry = new THREE.SphereGeometry(1.2, 32, 32);
    const material = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            color: { value: new THREE.Color(0xff00ff) },
            intensity: { value: 1.0 },
        },
        vertexShader: `
            varying vec3 vNormal;
            varying vec3 vPosition;
            varying vec3 vWorldPosition;
            
            void main() {
                vNormal = normalize(normalMatrix * normal);
                vPosition = position;
                vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform float time;
            uniform vec3 color;
            uniform float intensity;
            varying vec3 vNormal;
            varying vec3 vPosition;
            varying vec3 vWorldPosition;
            
            // Chromatic aberration via offset refraction
            vec3 chromaticAberration(vec3 viewDir, float amount) {
                vec3 result;
                result.r = refract(viewDir, vNormal, 1.0 / (1.52 + amount)).x;
                result.g = refract(viewDir, vNormal, 1.0 / 1.52).y;
                result.b = refract(viewDir, vNormal, 1.0 / (1.52 - amount)).z;
                return result;
            }
            
            void main() {
                vec3 viewDir = normalize(cameraPosition - vWorldPosition);
                
                // Fresnel
                float fresnel = pow(1.0 - abs(dot(vNormal, viewDir)), 4.0);
                
                // Chromatic dispersion
                vec3 aberration = chromaticAberration(viewDir, 0.03);
                vec3 dispersionColor = vec3(
                    0.5 + 0.5 * sin(aberration.r * 10.0 + time * 2.0),
                    0.5 + 0.5 * sin(aberration.g * 10.0 + time * 2.5 + 2.0),
                    0.5 + 0.5 * sin(aberration.b * 10.0 + time * 1.5 + 4.0)
                );
                
                // Pulsing
                float pulse = sin(time * 4.0) * 0.3 + 0.7;
                
                vec3 finalColor = mix(color * pulse, dispersionColor, fresnel * 0.6);
                float alpha = fresnel * intensity * 0.8;
                
                gl_FragColor = vec4(finalColor, alpha);
            }
        `,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.copy(position);
    return mesh;
}
