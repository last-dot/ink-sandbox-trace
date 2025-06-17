use crate::constants::messages::POLKAVM_FILE_NOT_FOUND;
use crate::domain::rpc::JsonRpcResponse;
use crate::sandbox::Sandbox;
use crate::utils::find_polkavm;

pub struct CliHandler {
    sandbox: Option<Sandbox>,
}

impl CliHandler {
    pub fn new() -> CliHandler {
        CliHandler { sandbox: None }
    }
}

pub(crate) trait DapHandler<T> {
    fn handle_initialize(&mut self, path: Option<String>) -> T;
    fn handle_disconnect(&mut self) -> T;
    fn handle_pause(&mut self) -> T;
    fn handle_continue(&mut self) -> T;
    fn handle_next(&mut self) -> T;
    fn handle_unknown(&mut self, command: String) -> T;
}

impl DapHandler<JsonRpcResponse> for CliHandler {
    fn handle_initialize(&mut self, path: Option<String>) -> JsonRpcResponse {
        let polkavm = if let Some(path) = path {
            find_polkavm(path.as_str())
                .expect(POLKAVM_FILE_NOT_FOUND)
                .as_os_str()
                .to_str()
                .unwrap()
                .to_string()
        } else {
            return JsonRpcResponse::default();
        };
        self.sandbox =
            Some(Sandbox::from_uri(polkavm.as_str()).expect("Could not create the sandbox"));

        JsonRpcResponse::default()
    }

    fn handle_disconnect(&mut self) -> JsonRpcResponse {
        JsonRpcResponse::default()
    }

    fn handle_pause(&mut self) -> JsonRpcResponse {
        JsonRpcResponse::default()
    }

    fn handle_continue(&mut self) -> JsonRpcResponse {
        JsonRpcResponse::default()
    }

    fn handle_next(&mut self) -> JsonRpcResponse {
        JsonRpcResponse::default()
    }

    fn handle_unknown(&mut self, command: String) -> JsonRpcResponse {

        JsonRpcResponse::new(None, None, None)
    }
}

#[cfg(test)]
mod tests {
    use crate::dap_handler::{CliHandler, DapHandler};
    use crate::domain::rpc::JsonRpcResponse;
    use crate::utils::tests::{get_root_dir, POLKAVM_LOCATION};

    fn polkavm() -> String {
        get_root_dir()
            .join(POLKAVM_LOCATION)
            .as_os_str()
            .to_str()
            .unwrap()
            .to_string()
    }

    #[test]
    fn test_initialize() {
        let mut handler = CliHandler::new();
        let polkavm = polkavm();
        let response = handler.handle_initialize(Some(polkavm));
        assert_eq!(response, JsonRpcResponse::default());

        let response = handler.handle_initialize(None);
        assert_eq!(response, JsonRpcResponse::default());
    }

    #[test]
    #[should_panic(expected = "Could not find the polkavm file")]
    fn test_initialize_panic() {
        let mut handler = CliHandler::new();

        handler.handle_initialize(Some(String::default()));
    }
}
