use crate::sandbox::Sandbox;
use crate::utils::find_polkavm;
use serde_json::{json, Value};
use crate::api::DapResponse;

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
    fn handle_launch(&mut self) -> T;
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
            String::new()
        };
        self.sandbox =
            Some(Sandbox::from_uri(polkavm.as_str()).expect("Could not create the sandbox"));
        if let Some(sandbox) = &mut self.sandbox {
            sandbox.enable_step_tracing();
        }

        DapResponse::new("initialize", true)
    }

    fn handle_launch(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_disconnect(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_configuration_done(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_set_breakpoints(&mut self, lines: Vec<usize>) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_continue(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
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
        DapResponse::new("initialize", true)
    }

    fn handle_scopes(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_variables(&mut self) -> DapResponse {
        DapResponse::new("initialize", true)
    }

    fn handle_unknown(&mut self, command: String) -> DapResponse {
        let mut response =  DapResponse::new(command.as_str(), false);
        response.set_message("Unknown command");
        response
    }
}
