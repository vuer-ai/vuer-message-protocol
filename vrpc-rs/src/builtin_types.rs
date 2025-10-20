//! Built-in type support for common data types
//!
//! Author: Ge Yang

use crate::error::{Result, VmpError};
use crate::zdata::{ZData, ZDataConversion};

#[cfg(feature = "ndarray")]
use ndarray::{Array, ArrayD, IxDyn};

#[cfg(feature = "image")]
use image::{DynamicImage, ImageFormat};

/// NumPy-compatible ndarray support
#[cfg(feature = "ndarray")]
pub struct NumpyArray<T> {
    pub array: ArrayD<T>,
}

#[cfg(feature = "ndarray")]
impl<T: Clone> NumpyArray<T> {
    pub fn new(array: ArrayD<T>) -> Self {
        Self { array }
    }
}

#[cfg(feature = "ndarray")]
impl ZDataConversion for NumpyArray<f32> {
    fn ztype() -> &'static str {
        "numpy.ndarray"
    }

    fn to_zdata(&self) -> Result<ZData> {
        // Convert array to bytes
        let bytes = self.array.as_slice().ok_or_else(|| {
            VmpError::TypeConversion("Array is not contiguous".to_string())
        })?;

        let byte_vec: Vec<u8> = bytes
            .iter()
            .flat_map(|&f| f.to_le_bytes())
            .collect();

        let shape: Vec<usize> = self.array.shape().to_vec();

        Ok(ZData::new("numpy.ndarray")
            .with_binary(byte_vec)
            .with_dtype("float32")
            .with_shape(shape))
    }

    fn from_zdata(zdata: &ZData) -> Result<Self> {
        if !zdata.is_type("numpy.ndarray") {
            return Err(VmpError::TypeConversion(format!(
                "Expected numpy.ndarray, got {}",
                zdata.ztype
            )));
        }

        let bytes = zdata.b.as_ref().ok_or_else(|| {
            VmpError::MissingField("Binary data missing from ZData".to_string())
        })?;

        let shape = zdata.shape.as_ref().ok_or_else(|| {
            VmpError::MissingField("Shape missing from ZData".to_string())
        })?;

        let dtype = zdata.dtype.as_ref().ok_or_else(|| {
            VmpError::MissingField("Dtype missing from ZData".to_string())
        })?;

        if dtype != "float32" {
            return Err(VmpError::TypeConversion(format!(
                "Expected dtype float32, got {}",
                dtype
            )));
        }

        // Convert bytes back to f32 array
        let floats: Vec<f32> = bytes
            .chunks_exact(4)
            .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
            .collect();

        let array = Array::from_shape_vec(IxDyn(shape), floats)
            .map_err(|e| VmpError::TypeConversion(e.to_string()))?;

        Ok(Self::new(array))
    }

    fn is_available() -> bool {
        true
    }
}

/// Image support using the image crate
#[cfg(feature = "image")]
pub struct ImageData {
    pub image: DynamicImage,
    pub format: ImageFormat,
}

#[cfg(feature = "image")]
impl ImageData {
    pub fn new(image: DynamicImage, format: ImageFormat) -> Self {
        Self { image, format }
    }
}

#[cfg(feature = "image")]
impl ZDataConversion for ImageData {
    fn ztype() -> &'static str {
        "image"
    }

    fn to_zdata(&self) -> Result<ZData> {
        let mut bytes = Vec::new();
        let mut cursor = std::io::Cursor::new(&mut bytes);

        self.image
            .write_to(&mut cursor, self.format)
            .map_err(|e| VmpError::TypeConversion(e.to_string()))?;

        let format_str = match self.format {
            ImageFormat::Png => "png",
            ImageFormat::Jpeg => "jpeg",
            ImageFormat::WebP => "webp",
            _ => "unknown",
        };

        Ok(ZData::new("image")
            .with_binary(bytes)
            .with_field("format", serde_json::json!(format_str)))
    }

    fn from_zdata(zdata: &ZData) -> Result<Self> {
        if !zdata.is_type("image") {
            return Err(VmpError::TypeConversion(format!(
                "Expected image, got {}",
                zdata.ztype
            )));
        }

        let bytes = zdata.b.as_ref().ok_or_else(|| {
            VmpError::MissingField("Binary data missing from ZData".to_string())
        })?;

        let format_str = zdata
            .get_field("format")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                VmpError::MissingField("Format missing from ZData".to_string())
            })?;

        let format = match format_str {
            "png" => ImageFormat::Png,
            "jpeg" => ImageFormat::Jpeg,
            "webp" => ImageFormat::WebP,
            _ => {
                return Err(VmpError::TypeConversion(format!(
                    "Unsupported image format: {}",
                    format_str
                )))
            }
        };

        let image = image::load_from_memory_with_format(bytes, format)
            .map_err(|e| VmpError::TypeConversion(e.to_string()))?;

        Ok(Self::new(image, format))
    }

    fn is_available() -> bool {
        true
    }
}

/// Type conversion fallback for unavailable types
///
/// This provides helpful error messages when a type is not available
/// due to missing feature flags or dependencies.
pub struct TypeConversionFallback;

impl TypeConversionFallback {
    /// Check if ndarray support is available
    pub fn is_ndarray_available() -> bool {
        cfg!(feature = "ndarray")
    }

    /// Check if image support is available
    pub fn is_image_available() -> bool {
        cfg!(feature = "image")
    }

    /// Get a helpful error message for a missing type
    pub fn missing_type_error(ztype: &str) -> VmpError {
        match ztype {
            "numpy.ndarray" if !Self::is_ndarray_available() => {
                VmpError::TypeConversion(
                    "NumPy array support requires the 'ndarray' feature. \
                     Add 'features = [\"ndarray\"]' to your Cargo.toml dependency."
                        .to_string(),
                )
            }
            "image" if !Self::is_image_available() => {
                VmpError::TypeConversion(
                    "Image support requires the 'image' feature. \
                     Add 'features = [\"image\"]' to your Cargo.toml dependency."
                        .to_string(),
                )
            }
            _ => VmpError::TypeNotRegistered(format!(
                "Type '{}' is not available. It may require a feature flag or external dependency.",
                ztype
            )),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    #[cfg(feature = "ndarray")]
    fn test_numpy_array_conversion() {
        let data = vec![1.0f32, 2.0, 3.0, 4.0, 5.0, 6.0];
        let array = Array::from_shape_vec(IxDyn(&[2, 3]), data.clone()).unwrap();
        let numpy_array = NumpyArray::new(array);

        let zdata = numpy_array.to_zdata().unwrap();
        assert_eq!(zdata.ztype, "numpy.ndarray");
        assert_eq!(zdata.dtype, Some("float32".to_string()));
        assert_eq!(zdata.shape, Some(vec![2, 3]));

        let restored = NumpyArray::from_zdata(&zdata).unwrap();
        assert_eq!(restored.array.shape(), &[2, 3]);
    }

    #[test]
    #[cfg(feature = "image")]
    fn test_image_conversion() {
        use image::{ImageBuffer, Rgb};

        let img = DynamicImage::ImageRgb8(ImageBuffer::from_fn(100, 100, |x, y| {
            Rgb([((x + y) % 256) as u8, 0, 0])
        }));

        let image_data = ImageData::new(img, ImageFormat::Png);
        let zdata = image_data.to_zdata().unwrap();

        assert_eq!(zdata.ztype, "image");
        assert!(zdata.b.is_some());
        assert_eq!(zdata.get_field("format").unwrap().as_str().unwrap(), "png");

        let restored = ImageData::from_zdata(&zdata).unwrap();
        assert_eq!(restored.format, ImageFormat::Png);
    }

    #[test]
    fn test_type_conversion_fallback() {
        assert!(TypeConversionFallback::is_ndarray_available() == cfg!(feature = "ndarray"));
        assert!(TypeConversionFallback::is_image_available() == cfg!(feature = "image"));
    }
}
