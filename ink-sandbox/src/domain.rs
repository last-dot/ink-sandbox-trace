pub(crate) mod rpc {
    use crate::api::DapCommand;
    use crate::constants::messages::{EOF, JSON_RPC_VERSION};
    use crate::sandbox::SandboxError;
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
        pub id: Option<String>,
    }

    #[derive(Serialize, Debug, Clone, PartialEq, Eq)]
    pub struct JsonRpcResponse {
        pub jsonrpc: String,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub result: Option<Value>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub error: Option<String>,
        #[serde(skip_serializing_if = "Option::is_none")]
        pub id: Option<String>,
    }

    impl JsonRpcRequest {
        pub fn new(method: String, params: Option<Value>, id: Option<String>) -> Self {
            JsonRpcRequest {
                jsonrpc: JSON_RPC_VERSION.to_string(),
                method,
                params,
                id,
            }
        }

        pub fn as_command(&self) -> DapCommand {
            DapCommand::from(self)
        }

        pub fn from(reader: &mut BufReader<StdinLock>) -> Result<Self, SandboxError> {
            let mut line = String::new();
            if reader.read_line(&mut line).unwrap() == 0 {
                panic!("{}", EOF);
            };

            let request = serde_json::from_str::<JsonRpcRequest>(&line)?;
            Ok(request)
        }
    }

    impl Default for JsonRpcRequest {
        fn default() -> Self {
            JsonRpcRequest::new(String::default(), None, None)
        }
    }

    impl JsonRpcResponse {
        pub(crate) fn new(
            result: Option<Value>,
            error: Option<String>,
            id: Option<String>,
        ) -> Self {
            JsonRpcResponse {
                jsonrpc: JSON_RPC_VERSION.to_string(),
                result,
                error,
                id,
            }
        }

        pub(crate) fn error(error: &str, id: Option<String>) -> Self {
            JsonRpcResponse::new(None, Some(String::from(error)), id)
        }

        pub(crate) fn result(result: Value, id: Option<String>) -> Self {
            JsonRpcResponse::new(Some(result), None, id)
        }

        pub(crate) fn with_default_headers(&mut self) -> String {
            let body = serde_json::to_string(self).unwrap();
            let headers = format!("Content-Length: {}\r\n\r\n", body.len());
            format!("{}{}", headers, body)
        }

        pub fn set_request_id(&mut self, id: &str) {
            self.id = Some(id.to_string());
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
    use serde::{Deserialize, Serialize};

    #[derive(Deserialize, Debug, Clone, PartialEq, Eq)]
    pub(crate) struct InitParams {
        pub polkavm: String,
    }

    impl From<&JsonRpcRequest> for InitParams {
        fn from(value: &JsonRpcRequest) -> Self {
            let params = &value.params;
            let params = params.as_ref().expect(PARAMS_NOT_FOUND);
            let polkavm = params["polkavm"]
                .as_str()
                .expect(PARAMS_NOT_FOUND)
                .to_string();
            InitParams { polkavm }
        }
    }

    #[derive(Serialize, Debug, Clone, PartialEq, Eq)]
    pub(crate) struct ResultMsg {
        pub result: String,
    }

    impl ResultMsg {
        pub fn new(result: &str) -> Self {
            ResultMsg {
                result: result.to_string(),
            }
        }
    }
}
