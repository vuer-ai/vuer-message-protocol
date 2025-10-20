/**
 * TypedArray conversion examples for VMP
 *
 * Demonstrates encoding/decoding of various binary array types
 * for efficient geometry and point cloud transmission.
 */

import { serialize, deserialize, registerZDataType } from '../src/index.js';

// ============================================================================
// Example 1: Basic TypedArray Encoding
// ============================================================================

console.log('=== Example 1: Basic TypedArray Encoding ===\n');

// Float32Array - Standard precision for most geometry
const vertices = new Float32Array([
  0, 0, 0,    // vertex 1
  1, 0, 0,    // vertex 2
  0, 1, 0,    // vertex 3
]);

// Uint32Array - For mesh indices
const faces = new Uint32Array([0, 1, 2]);  // Triangle

// Uint8Array - For RGB colors
const colors = new Uint8Array([
  255, 0, 0,    // red
  0, 255, 0,    // green
  0, 0, 255,    // blue
]);

const meshData = {
  vertices,
  faces,
  colors,
};

const binary = serialize(meshData);
console.log('Serialized mesh:', binary.length, 'bytes');

const decoded = deserialize(binary);
console.log('Decoded vertices:', decoded.vertices);
console.log('Decoded faces:', decoded.faces);
console.log('Decoded colors:', decoded.colors);
console.log();

// ============================================================================
// Example 2: Point Cloud Data
// ============================================================================

console.log('=== Example 2: Point Cloud Data ===\n');

interface PointCloud {
  positions: Float32Array;
  colors?: Uint8Array;
  sizes?: Float32Array;
}

// Register custom PointCloud type
registerZDataType({
  ztype: 'pointcloud',
  encode: (value: unknown) => {
    if (
      typeof value === 'object' &&
      value !== null &&
      'positions' in value &&
      value.positions instanceof Float32Array
    ) {
      const pc = value as PointCloud;
      return {
        ztype: 'pointcloud',
        positions: pc.positions,
        colors: pc.colors,
        sizes: pc.sizes,
        count: pc.positions.length / 3,
      };
    }
    return null;
  },
  decode: (zdata) => {
    if (zdata.ztype !== 'pointcloud') return null;

    return {
      positions: new Float32Array(zdata.positions as ArrayBuffer),
      colors: zdata.colors ? new Uint8Array(zdata.colors as ArrayBuffer) : undefined,
      sizes: zdata.sizes ? new Float32Array(zdata.sizes as ArrayBuffer) : undefined,
    } as PointCloud;
  },
});

const pointCloud: PointCloud = {
  positions: new Float32Array([
    1.0, 2.0, 3.0,
    4.0, 5.0, 6.0,
    7.0, 8.0, 9.0,
  ]),
  colors: new Uint8Array([
    255, 0, 0,
    0, 255, 0,
    0, 0, 255,
  ]),
  sizes: new Float32Array([0.1, 0.2, 0.3]),
};

const pcBinary = serialize({ cloud: pointCloud });
console.log('Serialized point cloud:', pcBinary.length, 'bytes');

const decodedPC = deserialize(pcBinary);
console.log('Decoded point cloud positions:', decodedPC.cloud.positions);
console.log('Decoded point cloud colors:', decodedPC.cloud.colors);
console.log();

// ============================================================================
// Example 3: Compressed Mesh with Half-Precision (Uint16)
// ============================================================================

console.log('=== Example 3: Compressed Mesh (Half-Precision) ===\n');

interface CompressedMesh {
  vertices: Uint16Array;   // Half-precision positions
  faces: Uint16Array;      // Indices
  colors?: Uint8Array;     // Vertex colors
  bounds: {                // For decompression
    min: [number, number, number];
    range: [number, number, number];
  };
}

// Helper function to compress vertices to Uint16
function compressVertices(vertices: Float32Array): {
  compressed: Uint16Array;
  bounds: { min: [number, number, number]; range: [number, number, number] };
} {
  // Find bounding box
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];

  for (let i = 0; i < vertices.length; i += 3) {
    for (let j = 0; j < 3; j++) {
      min[j] = Math.min(min[j], vertices[i + j]);
      max[j] = Math.max(max[j], vertices[i + j]);
    }
  }

  const range = [
    max[0] - min[0],
    max[1] - min[1],
    max[2] - min[2],
  ];

  // Quantize to Uint16
  const compressed = new Uint16Array(vertices.length);
  for (let i = 0; i < vertices.length; i++) {
    const axis = i % 3;
    const normalized = (vertices[i] - min[axis]) / range[axis];
    compressed[i] = Math.floor(normalized * 65535);
  }

  return {
    compressed,
    bounds: {
      min: min as [number, number, number],
      range: range as [number, number, number],
    },
  };
}

// Helper function to decompress Uint16 to Float32Array
function decompressVertices(
  compressed: Uint16Array,
  bounds: { min: [number, number, number]; range: [number, number, number] }
): Float32Array {
  const vertices = new Float32Array(compressed.length);
  for (let i = 0; i < compressed.length; i++) {
    const axis = i % 3;
    const normalized = compressed[i] / 65535;
    vertices[i] = normalized * bounds.range[axis] + bounds.min[axis];
  }
  return vertices;
}

// Register compressed mesh type
registerZDataType({
  ztype: 'compressed.mesh',
  encode: (value: unknown) => {
    if (
      typeof value === 'object' &&
      value !== null &&
      'vertices' in value &&
      value.vertices instanceof Uint16Array
    ) {
      const mesh = value as CompressedMesh;
      return {
        ztype: 'compressed.mesh',
        vertices: mesh.vertices,
        faces: mesh.faces,
        colors: mesh.colors,
        bounds: mesh.bounds,
      };
    }
    return null;
  },
  decode: (zdata) => {
    if (zdata.ztype !== 'compressed.mesh') return null;

    return {
      vertices: new Uint16Array(zdata.vertices as ArrayBuffer),
      faces: new Uint16Array(zdata.faces as ArrayBuffer),
      colors: zdata.colors ? new Uint8Array(zdata.colors as ArrayBuffer) : undefined,
      bounds: zdata.bounds as CompressedMesh['bounds'],
    } as CompressedMesh;
  },
});

// Original full-precision mesh
const originalVertices = new Float32Array([
  -5.5, 10.2, 3.8,
  12.3, -4.7, 9.1,
  8.9, 6.4, -2.3,
]);

// Compress it
const { compressed, bounds } = compressVertices(originalVertices);

const compressedMesh: CompressedMesh = {
  vertices: compressed,
  faces: new Uint16Array([0, 1, 2]),
  colors: new Uint8Array([255, 0, 0, 0, 255, 0, 0, 0, 255]),
  bounds,
};

console.log('Original size:', originalVertices.byteLength, 'bytes');
console.log('Compressed size:', compressed.byteLength, 'bytes');
console.log('Compression ratio:', (compressed.byteLength / originalVertices.byteLength * 100).toFixed(1) + '%');

const meshBinary = serialize({ mesh: compressedMesh });
const decodedMesh = deserialize(meshBinary) as { mesh: CompressedMesh };

// Decompress and compare
const decompressed = decompressVertices(decodedMesh.mesh.vertices, decodedMesh.mesh.bounds);
console.log('Original vertices:', originalVertices);
console.log('Decompressed vertices:', decompressed);
console.log('Max error:', Math.max(...Array.from(decompressed).map((v, i) => Math.abs(v - originalVertices[i]))));
console.log();

// ============================================================================
// Example 4: Color Encoding (Uint8 vs Float32)
// ============================================================================

console.log('=== Example 4: Color Encoding Comparison ===\n');

// Inefficient: Float32 colors
const colorsFloat32 = new Float32Array([
  1.0, 0.0, 0.0,    // red
  0.0, 1.0, 0.0,    // green
  0.0, 0.0, 1.0,    // blue
]);

// Efficient: Uint8 colors
const colorsUint8 = new Uint8Array([
  255, 0, 0,        // red
  0, 255, 0,        // green
  0, 0, 255,        // blue
]);

// Convert Uint8 to Float32 for rendering
const colorsNormalized = Float32Array.from(colorsUint8, (val) => val / 255);

console.log('Float32 colors size:', colorsFloat32.byteLength, 'bytes');
console.log('Uint8 colors size:', colorsUint8.byteLength, 'bytes');
console.log('Savings:', (1 - colorsUint8.byteLength / colorsFloat32.byteLength) * 100 + '%');
console.log('Normalized colors:', colorsNormalized);
console.log();

// ============================================================================
// Example 5: Index Buffer Optimization
// ============================================================================

console.log('=== Example 5: Index Buffer Optimization ===\n');

function chooseIndexType(vertexCount: number): 'Uint8Array' | 'Uint16Array' | 'Uint32Array' {
  if (vertexCount < 256) return 'Uint8Array';
  if (vertexCount < 65536) return 'Uint16Array';
  return 'Uint32Array';
}

const scenarios = [
  { vertices: 100, type: chooseIndexType(100) },
  { vertices: 10000, type: chooseIndexType(10000) },
  { vertices: 100000, type: chooseIndexType(100000) },
];

console.log('Optimal index types:');
scenarios.forEach(({ vertices, type }) => {
  const bytesPerIndex = type === 'Uint8Array' ? 1 : type === 'Uint16Array' ? 2 : 4;
  console.log(`  ${vertices.toLocaleString()} vertices → ${type} (${bytesPerIndex} byte/index)`);
});
console.log();

// ============================================================================
// Summary
// ============================================================================

console.log('=== Summary ===\n');
console.log('Type               | Bytes | Use Case');
console.log('-------------------+-------+---------------------------');
console.log('Float32Array       | 4     | Vertices, positions, normals');
console.log('Float64Array       | 8     | High precision (rarely needed)');
console.log('Uint16Array        | 2     | Compressed positions, indices');
console.log('Uint32Array        | 4     | Large mesh indices');
console.log('Uint8Array         | 1     | Colors (RGB), small indices');
console.log('Int8Array          | 1     | Normalized normals');
console.log();
