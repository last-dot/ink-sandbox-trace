use crate::constants::messages::POLKAVM_FILE_NOT_FOUND;
use crate::domain::params::ResultMsg;
use crate::domain::rpc::JsonRpcResponse;
use crate::sandbox::{Sandbox, SandboxError};
use serde_json::json;

pub struct CliHandler {
    sandbox: Option<Sandbox>,
}

impl CliHandler {
    pub fn new() -> CliHandler {
        CliHandler { sandbox: None }
    }
}

pub(crate) trait DapHandler<T> {
    fn handle_initialize(&mut self, path: Option<String>) -> Result<T, SandboxError>;
    fn handle_disconnect(&mut self) -> Result<T, SandboxError>;
    fn handle_pause(&mut self) -> Result<T, SandboxError>;
    fn handle_continue(&mut self) -> Result<T, SandboxError>;
    fn handle_next(&mut self) -> Result<T, SandboxError>;
    fn handle_unknown(&mut self, command: String) -> Result<T, SandboxError>;
}

impl DapHandler<JsonRpcResponse> for CliHandler {
    fn handle_initialize(
        &mut self,
        polkavm_path: Option<String>,
    ) -> Result<JsonRpcResponse, SandboxError> {
        let response = if let Some(path) = polkavm_path {
            self.sandbox = Some(Sandbox::from_uri(path.as_str())?);
            JsonRpcResponse::result(json!(ResultMsg::new("initialized")), None)
        } else {
            JsonRpcResponse::error(POLKAVM_FILE_NOT_FOUND, None)
        };

        Ok(response)
    }

    fn handle_disconnect(&mut self) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::default())
    }

    fn handle_pause(&mut self) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::default())
    }

    fn handle_continue(&mut self) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::default())
    }

    fn handle_next(&mut self) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::default())
    }

    fn handle_unknown(&mut self, command: String) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::error(
            format!("Unknown command: {}", command).as_str(),
            None,
        ))
    }
}
