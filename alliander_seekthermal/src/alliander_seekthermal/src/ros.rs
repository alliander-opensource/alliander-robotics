use r2r::{QosProfile, sensor_msgs::msg::CompressedImage, std_msgs::msg::Header};

use crate::error::Result;

pub fn jpeg_to_ros_image(jpeg_bytes: &[u8], frame_id: &str) -> CompressedImage {
    CompressedImage {
        header: Header {
            frame_id: frame_id.to_string(),
            ..Default::default()
        },
        format: "jpeg".to_string(),
        data: jpeg_bytes.to_vec(),
    }
}

struct RosCameraBridge {}

impl RosCameraBridge {}
