use crate::error::Result;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

pub struct CameraClient {
    token: Option<String>,
    stream: TcpStream,
}

impl CameraClient {
    pub async fn new(ip_addr: &str) -> Result<Self> {
        let stream = TcpStream::connect(ip_addr).await?;
        Ok(Self {
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

    pub async fn post(&mut self, body: &str) -> Result<Vec<u8>> {
        let request = format!(
            "POST /session/login HTTP/1.1\r\n\
             Host: 192.168.68.65\r\n\
             User-Agent: curl/8.18.0\r\n\
             accept: application/json\r\n\
             Content-Type: application/json\r\n\
             Content-Length: {}\r\n\
             \r\n\
             {}",
            body.len(),
            body
        );
        self.stream.write_all(request.as_bytes()).await?;

        let mut response = Vec::new();
        self.stream.read_to_end(&mut response).await?;

        Ok(response)
    }
}
