use std::error::Error;

use crate::sandbox_rpc::SandboxRpc;

mod sandbox_rpc;
mod domain;
mod methods;

type SandboxError = Box<dyn Error>;
type SandboxResult<T> = Result<T, SandboxError>;

#[tokio::main]
async fn main() -> SandboxResult<()> {
    let sandbox = SandboxRpc::default();
    sandbox.serve_async().await?;

    loop {
        tokio::time::sleep(std::time::Duration::from_secs(10)).await;
    }
}
