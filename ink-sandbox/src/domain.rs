pub(crate) mod rpc {
    use crate::api::DapCommand;
    use crate::constants::headers::CONTENT_LENGTH;
    use crate::constants::messages::{EOF, HEADER_PARSING_ERROR, JSON_RPC_VERSION};
    use serde::{Deserialize, Serialize};
    use serde_json::{json, Value};
    use std::fmt::{Display, Formatter};
    use std::io::{BufRead, BufReader, StdinLock};

    #[derive(Deserialize, Debug, Clone, PartialEq, Eq)]
    pub struct JsonRpcRequest {
        pub jsonrpc: String,
        pub method: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub params: Option<Value>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub id: Option<usize>,
    }

    #[derive(Serialize, Debug, Clone, PartialEq, Eq)]
    pub struct JsonRpcResponse {
        pub jsonrpc: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub result: Option<Value>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub error: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub id: Option<usize>,
    }

    impl JsonRpcRequest {
        pub fn new(method: String, params: Option<Value>, id: Option<usize>) -> Self {
            JsonRpcRequest {
                jsonrpc: JSON_RPC_VERSION.to_string(),
                method,
                params,
                id,
            }
        }

        pub fn as_command(&self) -> Result<DapCommand, SandboxError> {
            DapCommand::try_from(self)
        }
    }

    impl Default for JsonRpcRequest {
        fn default() -> Self {
            JsonRpcRequest::new(String::default(), None, None)
        }
    }

    impl TryFrom<&mut BufReader<StdinLock<'_>>> for JsonRpcRequest {
        type Error = SandboxError;

        fn try_from(reader: &mut BufReader<StdinLock>) -> Result<Self, Self::Error> {
            let mut line = String::new();

            let bytes_read = reader
                .read_line(&mut line)
                .map_err(|e| SandboxError::from(e))?;

            if bytes_read == 0 {
                return Err(SandboxError::from(EOF));
            }

            let parse_line = if line.contains(CONTENT_LENGTH) {
                line.split(r"\r\n")
                    .last()
                    .ok_or_else(|| SandboxError::from(HEADER_PARSING_ERROR))?
            } else {
                line.as_str()
            };
            let request = serde_json::from_str::<JsonRpcRequest>(parse_line)?;
            Ok(request)
        }
    }

    impl JsonRpcResponse {
        pub(crate) fn new(result: Option<Value>, error: Option<String>, id: Option<usize>) -> Self {
            JsonRpcResponse {
                jsonrpc: JSON_RPC_VERSION.to_string(),
                result,
                error,
                id,
            }
        }

        pub(crate) fn error(error: &str, id: Option<usize>) -> Self {
            JsonRpcResponse::new(None, Some(String::from(error)), id)
        }

        pub(crate) fn result(result: Value, id: Option<usize>) -> Self {
            JsonRpcResponse::new(Some(result), None, id)
        }

        pub(crate) fn with_default_headers(&mut self) -> String {
            let body = serde_json::to_string(self).unwrap();
            let headers = format!("Content-Length: {}\r\n\r\n", body.len());
            format!("{}{}", headers, body)
        }

        pub fn set_request_id(&mut self, id: usize) {
            self.id = Some(id);
        }
    }

    impl Display for JsonRpcResponse {
        fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
            let j = json!(self);
            write!(f, "{}", j)
        }
    }

    impl Default for JsonRpcResponse {
        fn default() -> Self {
            JsonRpcResponse::new(None, None, None)
        }
    }
}

pub(crate) mod params {
    use crate::constants::messages::PARAMS_NOT_FOUND;
    use crate::domain::rpc::JsonRpcRequest;
    use serde::Deserialize;

    #[derive(Deserialize, Debug, Clone, PartialEq, Eq)]
    pub(crate) struct InitParams {
        pub polkavm: String,
    }

    #[derive(Deserialize, Debug, Clone, PartialEq, Eq)]
    pub(crate) struct ContinueParams {
        pub until: String,
    }

    impl TryFrom<&JsonRpcRequest> for ContinueParams {
        type Error = SandboxError;

        fn try_from(value: &JsonRpcRequest) -> Result<Self, Self::Error> {
            let params = value
                .params
                .as_ref()
                .ok_or_else(|| Self::Error::from(PARAMS_NOT_FOUND.to_string()))?;

            let until = params
                .get("until")
                .and_then(|v| v.as_str())
                .ok_or_else(|| Self::Error::from(PARAMS_NOT_FOUND.to_string()))?
                .to_string();

            Ok(ContinueParams { until })
        }
    }

    impl TryFrom<&JsonRpcRequest> for InitParams {
        type Error = SandboxError;

        fn try_from(value: &JsonRpcRequest) -> Result<Self, Self::Error> {
            let params = value
                .params
                .as_ref()
                .ok_or_else(|| Self::Error::from(PARAMS_NOT_FOUND.to_string()))?;

            let polkavm = params
                .get("path")
                .and_then(|v| v.as_str())
                .ok_or_else(|| Self::Error::from(PARAMS_NOT_FOUND.to_string()))?
                .to_string();

            Ok(InitParams { polkavm })
        }
    }
}
