use alliander_seekthermal::error::Result;
use alliander_seekthermal::stream::CameraClient;
const CAMERA_IP: &str = "192.168.68.65:80";

#[tokio::main]
async fn main() -> Result<()> {
    let mut camera_client = CameraClient::new(CAMERA_IP).await?;
    let success = camera_client.login().await?;
    println!("Login success: {}", success);

    Ok(())
}
