use thiserror::Error;

#[derive(Debug, Error)]
pub enum CameraError {
    #[error("Network error: {0}")]
    Network(#[from] std::io::Error),

    #[error("Login failed: {0}")]
    LoginFailed(String),

    #[error("Invalid response from camera")]
    InvalidResponse,

    #[error("Not authenticated")]
    NotAuthenticated,
}

pub type Result<T> = std::result::Result<T, CameraError>;
