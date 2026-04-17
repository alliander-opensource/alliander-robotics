const CAMERA_IP: &str = "192.168.68.69";
const BEARER_TOKEN: &str = "AAAdgfskgnslg";

async fn get_camera_info() -> Result<reqwest::Response, reqwest::Error> {
    let client = reqwest::Client::new();
    client
        .get(format!("http://{CAMERA_IP}/camera/info"))
        .send()
        .await
}

#[tokio::main]
async fn main() -> Result<(), reqwest::Error> {
    let resp = get_camera_info().await;
    match resp {
        Ok(r) => println!("Response: {}", r.text().await?),
        Err(e) => eprintln!("Error: {e}"),
    }

    Ok(())
}
