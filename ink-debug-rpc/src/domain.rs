use serde::{Deserialize, Serialize};
use serde_json::Value;

const JSON_RPC_VERSION: &str = "2.0";

#[derive(Debug, Deserialize, Clone)]
pub struct JsonRpcRequest {
    pub jsonrpc: String,
    pub method: String,
    #[serde(default)]
    pub params: Value,
    pub id: usize,
}

#[derive(Debug, Serialize)]
pub struct JsonRpcResponse {
    pub jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<JsonRpcError>,
    pub id: usize,
}

#[derive(Debug, Serialize)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
}

impl JsonRpcResponse {
    pub(crate) fn new(result: Option<Value>, error: Option<JsonRpcError>, id: usize) -> JsonRpcResponse {
        JsonRpcResponse {
            jsonrpc: JSON_RPC_VERSION.to_string(),
            result,
            error,
            id
        }
    }
}
