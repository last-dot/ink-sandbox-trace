mod domain;
mod methods;
pub mod sandbox_rpc;
pub use sandbox_rpc::SandboxRpc;

// #[tokio::main]
// async fn main() -> SandboxResult<()> {
//     let sandbox = SandboxRpc::default();
//     sandbox.serve_async().await?;

//     loop {
//         tokio::time::sleep(std::time::Duration::from_secs(10)).await;
//     }
// }
