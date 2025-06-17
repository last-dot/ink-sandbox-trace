use crate::api::DapResponse;
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
    fn handle_configuration_done(&mut self) -> T;
    fn handle_set_breakpoints(&mut self, lines: Vec<usize>) -> T;
    fn handle_continue(&mut self) -> T;
    fn handle_next(&mut self) -> T;
    fn handle_step_in(&mut self) -> T;
    fn handle_step_out(&mut self) -> T;
    fn handle_pause(&mut self) -> T;
    fn handle_threads(&mut self) -> T;
    fn handle_stack_trace(&mut self) -> T;
    fn handle_scopes(&mut self) -> T;
    fn handle_variables(&mut self) -> T;
    fn handle_unknown(&mut self, command: String) -> T;
}

impl DapHandler<DapResponse> for CliHandler {
    fn handle_initialize(&mut self, path: Option<String>) -> DapResponse {
        let polkavm = if let Some(path) = path {
            find_polkavm(path.as_str())
                .expect("Could not find the polkavm file")
                .as_os_str()
                .to_str()
                .unwrap()
                .to_string()
        } else {
            return DapResponse::new("initialize", false);
        };
        self.sandbox =
            Some(Sandbox::from_uri(polkavm.as_str()).expect("Could not create the sandbox"));

        DapResponse::new("initialize", true)
    }

    fn handle_disconnect(&mut self) -> DapResponse {
        let mut response = DapResponse::new("disconnect", true);
        response.set_message("Disconnected from server");
        response
    }

    fn handle_configuration_done(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_set_breakpoints(&mut self, lines: Vec<usize>) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_continue(&mut self) -> DapResponse {
        DapResponse::new("continue", true)
    }

    fn handle_next(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_step_in(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_step_out(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_pause(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_threads(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_stack_trace(&mut self) -> DapResponse {

        DapResponse::new("stack_trace", true)
    }

    fn handle_scopes(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_variables(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_unknown(&mut self, command: String) -> DapResponse {
        let mut response = DapResponse::new(command.as_str(), false);
        response.set_message("Unknown command");
        response
    }
}

#[cfg(test)]
mod tests {
    use crate::api::DapResponse;
    use crate::dap_handler::{CliHandler, DapHandler};
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
        assert_eq!(response, DapResponse::new("initialize", true));

        let response = handler.handle_initialize(None);
        assert_eq!(response, DapResponse::new("initialize", false));
    }

    #[test]
    #[should_panic(expected = "Could not find the polkavm file")]
    fn test_initialize_panic() {
        let mut handler = CliHandler::new();

        handler.handle_initialize(Some(String::default()));
    }

    #[test]
    fn test_handle_stack_trace() {
        let mut handler = CliHandler::new();
        let polkavm = polkavm();
        handler.handle_initialize(Some(polkavm));
        handler.handle_stack_trace();
        assert_eq!(
            handler.handle_stack_trace(),
            DapResponse::new("stack_trace", true)
        );
    }
}
