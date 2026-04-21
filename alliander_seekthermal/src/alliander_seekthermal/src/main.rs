use alliander_seekthermal::camera::CameraClient;
use alliander_seekthermal::error::{CameraError, Result};
const CAMERA_IP: &str = "192.168.68.65:80";

#[tokio::main]
async fn main() -> Result<()> {
    let mut camera_client = CameraClient::new(CAMERA_IP).await?;
    let success = camera_client.login().await?;
    println!("Login success: {}", success);

    if let Ok(resp) = camera_client.get("camera/info").await {
        let status = resp.status();
        let body = resp
            .text()
            .await
            .map_err(|_| CameraError::InvalidResponse)?;
        println!("Response for endpoint camera/info: [{}] {:?}", status, body,);
    }
    if let Ok(resp) = camera_client.get("image/minmax").await {
        let status = resp.status();
        let body = resp
            .text()
            .await
            .map_err(|_| CameraError::InvalidResponse)?;
        println!(
            "Response for endpoint image/minmax: [{}] {:?}",
            status, body,
        );
    }

    Ok(())
}
