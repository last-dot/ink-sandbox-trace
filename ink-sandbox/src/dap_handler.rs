use crate::domain::params::ContinueParams;
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
    fn handle_initialize(&mut self, path: String) -> Result<T, SandboxError>;
    fn handle_disconnect(&mut self) -> Result<T, SandboxError>;
    fn handle_pause(&mut self) -> Result<T, SandboxError>;
    fn handle_continue(&mut self, params: ContinueParams) -> Result<T, SandboxError>;
    fn handle_next(&mut self) -> Result<T, SandboxError>;
    fn handle_unknown(&mut self, command: String) -> Result<T, SandboxError>;
}

impl DapHandler<JsonRpcResponse> for CliHandler {
    fn handle_initialize(&mut self, polkavm_path: String) -> Result<JsonRpcResponse, SandboxError> {
        self.sandbox = Some(Sandbox::from_uri(polkavm_path.as_str())?);
        Ok(JsonRpcResponse::result(
            json!({
                "status": "initialized",
                "version": env!("CARGO_PKG_VERSION")
            }),
            None,
        ))
    }

    fn handle_disconnect(&mut self) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::result(
            json!({ "disconnected": true }),
            None,
        ))
    }

    fn handle_pause(&mut self) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::default())
    }

    // 3. Continue
    // // Запрос:
    // Content-Length: 67\r\n\r\n{"jsonrpc": "2.0", "method": "continue", "params": {"until": "123123"}, "id": 3}
    //
    // // Ответ:
    // Content-Length: 56\r\n
    // \r\n
    // {"jsonrpc": "2.0", "result": {"status": "running"}, "id": 3}
    //
    // // Позже придет событие (без id - это notification):
    // Content-Length: 145\r\n
    // \r\n
    // {"jsonrpc": "2.0", "method": "stopped", "params": {"reason": "breakpoint", "address": 0x1000, "breakpointId": 1}}
    fn handle_continue(&mut self, params: ContinueParams) -> Result<JsonRpcResponse, SandboxError> {
        self.sandbox.as_mut().unwrap().execute_until(params.until.as_str());
        Ok(JsonRpcResponse::result(
            json!({ "status": "running", "instructionPointer": params.until }),
            None,
        ))
    }

    fn handle_next(&mut self) -> Result<JsonRpcResponse, SandboxError> {
        Ok(JsonRpcResponse::default())
    }

    // {"jsonrpc": "2.0", "method": "ksdjifghlsakrjghawlrieuw", "params": {}}
    fn handle_unknown(&mut self, command: String) -> Result<JsonRpcResponse, SandboxError> {
        let message = format!("Unknown method: {}", command);
        if let Some(resp) = json!({"code": "404","message": message}).as_str() {
            Ok(JsonRpcResponse::error(resp, None))
        } else {
            Ok(JsonRpcResponse::error("Unknown method", None))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_handle_continue() {
        let mut handler = CliHandler::new();
        let result = handler.handle_initialize("/Users/maliketh/ink/ink-sandbox-trace/ink-trace-extension/sampleWorkspace/target/ink/flipper.polkavm".to_string());
        assert!(result.is_ok());

        handler.handle_continue(ContinueParams {
            until: "instruction123".to_string(),
        }).unwrap();
    }
}
