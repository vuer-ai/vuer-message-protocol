# Type Conversion and Compression Schemes

This document explains the type conversion and compression schemes used in VMP (Vuer Message Protocol) for efficient data transmission between Python and TypeScript/JavaScript.

## Overview

VMP handles binary data serialization with special support for:
1. **NumPy arrays** (Python) → **TypedArrays** (JavaScript)
2. **Compressed mesh data** using half-precision floats
3. **Point cloud data** with color information
4. **STL/PCD** file formats

## Core Type Conversions

### Python → JavaScript Type Mapping

| Python Type | ZData Type | JavaScript Type | Notes |
|------------|-----------|----------------|-------|
| `np.ndarray` | `numpy.ndarray` | `TypedArray` (Float32Array, etc.) | Full precision preserved |
| `torch.Tensor` | `torch.Tensor` | Not supported in TS | Use numpy arrays instead |
| `PIL.Image` | `image` | Blob / ImageData | Encoded as PNG/JPEG |
| Custom types | `custom.*` | User-defined | Via registry |

### JavaScript TypedArray Support

JavaScript provides several typed array types for binary data:

```typescript
// Standard precision (recommended for most use cases)
Float32Array    // 32-bit float (equivalent to np.float32)
Float64Array    // 64-bit float (equivalent to np.float64)

// Integer types
Int8Array       // 8-bit signed int
Uint8Array      // 8-bit unsigned int (for colors, images)
Int16Array      // 16-bit signed int
Uint16Array     // 16-bit unsigned int (for compressed data)
Int32Array      // 32-bit signed int
Uint32Array     // 32-bit unsigned int (for indices)

// Half precision (requires polyfill)
Float16Array    // 16-bit float (@petamoriken/float16 library)
```

## Compression Schemes

### 1. TriMesh Half-Precision Compression

**Source**: `vuer-ts/src/three_components/primitives/trimesh.tsx`

TriMesh uses half-precision (16-bit) floats for vertex coordinates and UV maps to reduce bandwidth by 50%.

#### Encoding (Python → Binary)

```python
# Python side: Convert float32 vertices to float16
import numpy as np

vertices_f32 = np.array([...], dtype=np.float32)  # Shape: (N, 3)
vertices_f16 = vertices_f32.astype(np.float16)     # Convert to half precision

# Serialize as Uint16Array for transport
vertices_bytes = vertices_f16.view(np.uint16).tobytes()

# For faces (always use Uint16 or Uint32 for indices)
faces = np.array([...], dtype=np.uint16)  # Triangle indices
faces_bytes = faces.tobytes()

# For colors (8-bit per channel, 0-255)
colors = np.array([...], dtype=np.uint8)  # RGB values
colors_bytes = colors.tobytes()
```

#### Decoding (Binary → JavaScript)

```typescript
// TypeScript side: Decode from msgpack binary
import { Float16Array } from '@petamoriken/float16';

// Vertices: Uint16Array → Float16Array → Float32Array
const verticesUint16 = new Uint16Array(binary.vertices);
const verticesFloat16 = new Float16Array(
  verticesUint16.buffer.slice(verticesUint16.byteOffset),
  0,
  verticesUint16.length / 2
);
const vertices = Float32Array.from(verticesFloat16); // Convert to Float32

// Faces: Uint16Array → Uint32Array
const facesUint16 = new Uint16Array(binary.faces);
const faces = new Uint32Array(
  facesUint16.buffer.slice(facesUint16.byteOffset),
  0,
  facesUint16.byteLength / Uint8Array.BYTES_PER_ELEMENT
);

// Colors: Uint8Array → Float32Array (normalized to 0-1)
const colorsUint8 = new Uint8Array(binary.colors);
const colors = Float32Array.from(colorsUint8, (val) => val / 255);
```

#### Data Structure

```typescript
interface TriMeshData {
  vertices: Uint16Array;  // Half-precision vertex positions (x, y, z)
  faces: Uint16Array;     // Triangle face indices
  colors?: Uint8Array;    // Vertex colors (r, g, b) in 0-255 range
  uv?: Uint16Array;       // Half-precision UV coordinates (u, v)
}
```

### 2. STL File Format

**Source**: `vuer-ts/src/three_components/file_loaders/Stl.tsx`

STL files can be transmitted as either text (ASCII) or binary:

#### ASCII STL
```
solid name
  facet normal 0 0 0
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 1 1 0
    endloop
  endfacet
endsolid name
```

#### Binary STL Structure
- Header: 80 bytes (comment/metadata)
- Number of triangles: 4 bytes (uint32)
- For each triangle:
  - Normal vector: 3 × float32 (12 bytes)
  - Vertex 1: 3 × float32 (12 bytes)
  - Vertex 2: 3 × float32 (12 bytes)
  - Vertex 3: 3 × float32 (12 bytes)
  - Attribute byte count: uint16 (2 bytes)

Total: 80 + 4 + (num_triangles × 50) bytes

#### Transport Options

```typescript
// Option 1: Send as base64-encoded binary
const stlBinary = new Uint8Array([...]); // Binary STL data
const base64 = btoa(String.fromCharCode(...stlBinary));

// Option 2: Send as text (ASCII STL)
const stlText = "solid name\nfacet normal...";

// Option 3: Send as BufferGeometry (pre-parsed, most efficient)
// In VMP, we'd encode this as:
{
  ztype: "three.BufferGeometry",
  vertices: Float32Array,  // or Uint16Array for compression
  normals: Float32Array,
  indices: Uint32Array
}
```

### 3. PCD (Point Cloud Data)

**Source**: `vuer-ts/src/three_components/file_loaders/Pcd.tsx`

PCD format stores 3D point clouds with optional color and normal data.

#### ASCII PCD Format
```
VERSION .7
FIELDS x y z rgb
SIZE 4 4 4 4
TYPE F F F U
COUNT 1 1 1 1
WIDTH 1000
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS 1000
DATA ascii
0.1 0.2 0.3 4278190080
...
```

#### Binary PCD Encoding (Recommended)

```python
# Python side: Create PCD data
import numpy as np

points = np.array([...], dtype=np.float32)    # Shape: (N, 3) - xyz
colors = np.array([...], dtype=np.uint8)      # Shape: (N, 3) - rgb

# Pack RGB into single uint32 (RGBA format)
# RGB = (r << 16) | (g << 8) | b
rgb_packed = (colors[:, 0].astype(np.uint32) << 16) | \
             (colors[:, 1].astype(np.uint32) << 8) | \
             (colors[:, 2].astype(np.uint32))

# Combine into structured array
pcd_data = np.zeros(len(points), dtype=[
    ('x', 'f4'), ('y', 'f4'), ('z', 'f4'), ('rgb', 'u4')
])
pcd_data['x'] = points[:, 0]
pcd_data['y'] = points[:, 1]
pcd_data['z'] = points[:, 2]
pcd_data['rgb'] = rgb_packed
```

#### VMP Point Cloud Encoding

For maximum efficiency, encode as separate typed arrays:

```typescript
interface PointCloudData {
  ztype: "pointcloud";
  positions: Float32Array;  // xyz coordinates (N×3)
  colors?: Uint8Array;      // rgb colors (N×3), 0-255
  normals?: Float32Array;   // xyz normals (N×3), optional
  sizes?: Float32Array;     // point sizes, optional
}
```

```python
# Python encoding
{
  "ztype": "pointcloud",
  "positions": points.astype(np.float32).tobytes(),
  "colors": colors.astype(np.uint8).tobytes(),
  "shape": points.shape
}
```

## Bandwidth Optimization Strategies

### 1. Precision Reduction

| Data Type | Full Precision | Half Precision | Savings |
|-----------|---------------|----------------|---------|
| Vertices | Float32 (4 bytes) | Float16 (2 bytes) | 50% |
| Normals | Float32 (4 bytes) | Int8 normalized (1 byte) | 75% |
| Colors | Float32 (4 bytes) | Uint8 (1 byte) | 75% |
| UV coords | Float32 (4 bytes) | Float16 (2 bytes) | 50% |

### 2. Index Optimization

```python
# Use smallest index type that can represent all vertices
num_vertices = len(vertices)

if num_vertices < 256:
    indices = np.array([...], dtype=np.uint8)    # 1 byte
elif num_vertices < 65536:
    indices = np.array([...], dtype=np.uint16)   # 2 bytes
else:
    indices = np.array([...], dtype=np.uint32)   # 4 bytes
```

### 3. Quantization

For mesh data, quantize to a bounding box:

```python
# Python: Quantize to 16-bit integer range
vertices_min = vertices.min(axis=0)
vertices_max = vertices.max(axis=0)
vertices_range = vertices_max - vertices_min

# Map to 0-65535 range
vertices_quantized = ((vertices - vertices_min) / vertices_range * 65535).astype(np.uint16)

# Transmit: quantized vertices + min + range
data = {
    "vertices": vertices_quantized,
    "bounds_min": vertices_min,
    "bounds_range": vertices_range
}

# JavaScript: Dequantize
const vertices = new Float32Array(verticesQuantized.length);
for (let i = 0; i < verticesQuantized.length; i++) {
    vertices[i] = (verticesQuantized[i] / 65535) * boundsRange[i % 3] + boundsMin[i % 3];
}
```

## ZData Type Registration Examples

### Example 1: Float16Array (Half-Precision)

```typescript
import { Float16Array } from '@petamoriken/float16';
import { ZData } from '@vuer-ai/vmp-ts';

// Register Float16Array support
ZData.register_type({
  ztype: 'float16array',
  encode: (value: Float16Array) => ({
    ztype: 'float16array',
    b: new Uint8Array(value.buffer),
    length: value.length,
  }),
  decode: (zdata) => {
    return new Float16Array(
      zdata.b.buffer,
      0,
      zdata.length
    );
  },
  type_class: Float16Array,
});
```

### Example 2: Point Cloud

```typescript
interface PointCloud {
  positions: Float32Array;
  colors?: Uint8Array;
}

ZData.register_type({
  ztype: 'pointcloud',
  encode: (value: PointCloud) => ({
    ztype: 'pointcloud',
    positions: value.positions,
    colors: value.colors,
    count: value.positions.length / 3,
  }),
  decode: (zdata) => ({
    positions: new Float32Array(zdata.positions),
    colors: zdata.colors ? new Uint8Array(zdata.colors) : undefined,
  }),
  type_checker: (value) =>
    typeof value === 'object' &&
    value !== null &&
    'positions' in value &&
    value.positions instanceof Float32Array,
});
```

### Example 3: Compressed Mesh

```typescript
interface CompressedMesh {
  vertices: Uint16Array;  // Half-precision
  faces: Uint16Array | Uint32Array;
  colors?: Uint8Array;
}

ZData.register_type({
  ztype: 'compressed.mesh',
  encode: (value: CompressedMesh) => ({
    ztype: 'compressed.mesh',
    vertices: value.vertices,
    faces: value.faces,
    colors: value.colors,
  }),
  decode: (zdata) => ({
    vertices: new Uint16Array(zdata.vertices),
    faces: new Uint32Array(zdata.faces),
    colors: zdata.colors ? new Uint8Array(zdata.colors) : undefined,
  }),
  type_checker: (value) =>
    typeof value === 'object' &&
    value !== null &&
    'vertices' in value &&
    value.vertices instanceof Uint16Array,
});
```

## Best Practices

### 1. Choose Appropriate Precision

```typescript
// ✅ Good: Use Float32 for most geometry
const positions = new Float32Array([x, y, z, ...]);

// ✅ Good: Use Uint8 for colors
const colors = new Uint8Array([r, g, b, ...]);

// ⚠️ Acceptable: Use Float16 for bandwidth-constrained scenarios
const compressedPositions = convertToFloat16(positions);

// ❌ Avoid: Float64 for rendering data (unnecessary precision)
const positions64 = new Float64Array([...]); // Wastes bandwidth
```

### 2. Batch Similar Data

```python
# ✅ Good: Send all meshes in one message
{
  "meshes": [
    {"vertices": [...], "faces": [...]},
    {"vertices": [...], "faces": [...]},
  ]
}

# ❌ Avoid: Sending individual messages per mesh
# (More overhead, slower)
```

### 3. Use Indices for Meshes

```python
# ✅ Good: Indexed geometry (shared vertices)
vertices = np.array([[0,0,0], [1,0,0], [0,1,0]])  # 3 unique
faces = np.array([[0,1,2]])  # Reference by index

# ❌ Avoid: Non-indexed (duplicate vertices)
triangles = np.array([
  [[0,0,0], [1,0,0], [0,1,0]],  # Redundant data
])
```

## Summary Table

| Use Case | Python Type | Binary Format | JS Type | Compression Ratio |
|----------|------------|---------------|---------|-------------------|
| Mesh vertices | `np.float32` | Float16 (2 bytes) | `Float32Array` | 50% |
| Mesh indices | `np.uint16/32` | Uint16/32 | `Uint32Array` | N/A |
| Colors | `np.uint8` | Uint8 (1 byte) | `Uint8Array` | 75% vs Float32 |
| Point clouds | `np.float32` | Float32 (4 bytes) | `Float32Array` | None |
| UV coordinates | `np.float32` | Float16 (2 bytes) | `Float32Array` | 50% |
| Normals | `np.float32` | Int8 normalized | `Float32Array` | 75% |

## References

- [MDN TypedArray](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/TypedArray)
- [Float16Array polyfill](https://www.npmjs.com/package/@petamoriken/float16)
- [Three.js BufferGeometry](https://threejs.org/docs/#api/en/core/BufferGeometry)
- [PCD File Format](https://pointclouds.org/documentation/tutorials/pcd_file_format.html)
- [STL Format](https://en.wikipedia.org/wiki/STL_(file_format))
