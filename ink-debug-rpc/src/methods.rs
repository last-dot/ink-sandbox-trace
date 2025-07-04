use serde_json::json;

use crate::domain::{JsonRpcError, JsonRpcRequest, JsonRpcResponse};

#[derive(Debug)]
pub(crate) enum Methods {
    Initialize(JsonRpcRequest),
}

fn match_request(request: JsonRpcRequest) -> Option<Methods> {
    match request.method.as_str() {
        "initialize" => Some(Methods::Initialize(request)),
        _ => None,
    }
}

pub(crate) fn handle(request: JsonRpcRequest) -> JsonRpcResponse {
    log::info!("Method call: {:?}", request);
    let method = match_request(request.clone());
    if let None = method {
        return JsonRpcResponse::new(
            None,
            Some(JsonRpcError {
                code: 404,
                message: "Method not found".to_string(),
                data: None,
            }),
            request.id,
        );
    }
    match method.unwrap() {
        Methods::Initialize(req) => {
            log::info!("Params: {:#?}", req.params);
            JsonRpcResponse::new(
                Some(json!({"status": "initialized", "version": "0.1.0"})),
                None,
                req.id,
            )
        }
    }
}
