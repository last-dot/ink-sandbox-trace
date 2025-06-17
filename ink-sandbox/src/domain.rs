pub(crate) mod rpc {
    use crate::constants::messages::{COULD_NOT_PARSE_THE_REQUEST, JSON_RPC_VERSION};
    use serde::{Deserialize, Serialize};
    use serde_json::{json, Value};
    use std::fmt::{Display, Formatter};
    use std::io::{BufRead, BufReader, StdinLock};
    use crate::api::DapCommand;

    #[derive(Deserialize, Debug, Clone, PartialEq, Eq)]
    pub struct JsonRpcRequest {
        pub jsonrpc: String,
        pub method: String,
        pub params: Option<Value>,
        pub id: Option<Value>,
    }

    #[derive(Serialize, Debug, Clone, PartialEq, Eq)]
    pub struct JsonRpcResponse {
        pub jsonrpc: String,
        pub result: Option<Value>,
        pub error: Option<Value>,
        pub id: Option<Value>,
    }

    impl JsonRpcRequest {
        pub fn new(method: String, params: Option<Value>, id: Option<Value>) -> Self {
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

        pub fn is_disconnect(&self) -> bool {
            self.as_command() == DapCommand::Disconnect
        }
    }

    impl Default for JsonRpcRequest {
        fn default() -> Self {
            JsonRpcRequest::new(String::default(), None, None)
        }
    }

    impl From<&mut BufReader<StdinLock<'_>>> for JsonRpcRequest {
        fn from(reader: &mut BufReader<StdinLock>) -> Self {
            let mut line = String::new();
            if reader.read_line(&mut line).unwrap() == 0 {
                return JsonRpcRequest::default();
            };

            serde_json::from_str::<JsonRpcRequest>(&line).expect(COULD_NOT_PARSE_THE_REQUEST)
        }
    }

    impl JsonRpcResponse {
        pub(crate) fn new(result: Option<Value>, error: Option<Value>, id: Option<Value>) -> Self {
            JsonRpcResponse {
                jsonrpc: JSON_RPC_VERSION.to_string(),
                result,
                error,
                id,
            }
        }

        pub(crate) fn set_error(&mut self, error: Value) {
            self.error = Some(error);
            self.result = None;
        }

        pub(crate) fn set_result(&mut self, result: Value) {
            self.result = Some(result);
            self.error = None;
        }

        pub(crate) fn with_default_headers(&mut self) -> String {
            let headers = "Content-Length: ";
            let headers = format!("{}{}", headers, self.to_string().len());
            let body = serde_json::to_string(self).unwrap();
            format!("{}{}", headers, body)
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
    pub(crate) struct InitializeParams {
        pub path: String,
    }

    impl From<&JsonRpcRequest> for InitializeParams {
        fn from(value: &JsonRpcRequest) -> Self {
            let params = &value.params;
            let params = params.as_ref().expect(PARAMS_NOT_FOUND);
            let path = params["path"].as_str().expect(PARAMS_NOT_FOUND).to_string();
            InitializeParams { path }
        }
    }
}
