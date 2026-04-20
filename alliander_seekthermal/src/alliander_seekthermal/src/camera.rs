use crate::error::{CameraError, Result};

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

pub struct CameraResponse {
    status_code: usize,
    body: Option<String>,
    image: Option<Vec<u8>>,
}

impl CameraResponse {
    pub fn new(status_code: usize) -> Self {
        Self {
            status_code,
            body: None,
            image: None,
        }
    }

    pub fn body(mut self, body_bytes: &[u8]) -> Self {
        self.body = Some(String::from_utf8_lossy(body_bytes).into_owned());
        self
    }

    pub fn image(mut self, image_bytes: &[u8]) -> Self {
        self.image = Some(image_bytes.to_vec());
        self
    }
}

pub struct CameraClient {
    ip_address: String,
    token: Option<String>,
    stream: TcpStream,
}

impl CameraClient {
    pub async fn new(ip_addr: &str) -> Result<Self> {
        let stream = TcpStream::connect(ip_addr).await?;
        Ok(Self {
            ip_address: ip_addr.to_string(),
            token: None,
            stream,
        })
    }

    pub async fn login(&mut self) -> Result<bool> {
        let body = "{\n  \"username\": \"admin\",\n  \"password\": \"admin\"\n}";
        let response = self.post(body).await?;
        println!("{}", String::from_utf8_lossy(&response));

        Ok(true)
    }

    fn extract_response(&self, response: Vec<u8>) -> Result<CameraResponse> {
        // Split headers and body on the blank line
        let header_end = response
            .windows(4)
            .position(|w| w == b"\r\n\r\n")
            .ok_or(CameraError::InvalidResponse)?;

        let header_section = std::str::from_utf8(&response[..header_end])
            .map_err(|_| CameraError::InvalidResponse)?;

        let body_bytes = &response[header_end + 4..];

        // Parse status code from first line e.g. "HTTP/1.1 200"
        let status_code = header_section
            .lines()
            .next()
            .and_then(|line| line.split_whitespace().nth(1))
            .and_then(|code| code.parse::<usize>().ok())
            .ok_or(CameraError::InvalidResponse)?;

        // Check Content-Type to decide how to interpret body
        let content_type = header_section
            .lines()
            .skip(1)
            .find(|line| line.to_lowercase().starts_with("content-type:"))
            .and_then(|line| line.splitn(2, ':').nth(1))
            .map(|v| v.trim());

        let mut cam_response = CameraResponse::new(status_code);
        cam_response = match content_type {
            Some(ct) if ct.contains("image/jpeg") => cam_response.image(body_bytes),
            Some(ct) if ct.contains("application/json") => cam_response.body(body_bytes),
            _ => cam_response.body(body_bytes), // fallback
        };

        Ok(cam_response)
    }

    pub async fn post(&mut self, body: &str) -> Result<Vec<u8>> {
        let request = format!(
            "POST /session/login HTTP/1.1\r\n\
             Host: {}\r\n\
             User-Agent: curl/8.18.0\r\n\
             accept: application/json\r\n\
             Content-Type: application/json\r\n\
             Content-Length: {}\r\n\
             \r\n\
             {}",
            self.ip_address,
            body.len(),
            body
        );
        self.stream.write_all(request.as_bytes()).await?;

        let mut response = Vec::new();
        self.stream.read_to_end(&mut response).await?;

        Ok(response)
    }
}
