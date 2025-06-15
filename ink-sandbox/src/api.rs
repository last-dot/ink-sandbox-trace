use std::path::Path;
use crate::sandbox::Sandbox;

pub trait CliApi {
    fn start(path: &str) -> Self;

    fn set_breakpoint(&mut self, path: &Path, line: usize);

    fn continue_exec(&mut self, path: &Path) -> bool;

    fn call_contract_method(&mut self, path: &Path, method_name: &str, args: Vec<&str>);

    fn memory_read_only(&mut self, mem_addr: &str) -> &str;
}

struct SandboxDebugAdapter {
    sandbox: Sandbox,
}

impl CliApi for SandboxDebugAdapter {
    fn start(path: &str) -> Self {
        todo!()
    }

    fn set_breakpoint(&mut self, path: &Path, line: usize) {
        todo!()
    }

    fn continue_exec(&mut self, path: &Path) -> bool {
        todo!()
    }

    fn call_contract_method(&mut self, path: &Path, method_name: &str, args: Vec<&str>) {
        todo!()
    }

    fn memory_read_only(&mut self, mem_addr: &str) -> &str {
        todo!()
    }
}