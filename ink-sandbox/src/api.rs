use crate::sandbox::Sandbox;
use std::path::Path;

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
        println!("SandboxDebugAdapter::start path: {}", path);
        let polkavm = crate::utils::find_polkavm(path).expect("PolkaVM not found in target. Did you build contract with 'cargo contract build --release'?");
        let sandbox = Sandbox::from_uri(polkavm.as_os_str().to_str().unwrap()).expect("Sandbox from URI returned by 'not a Sandbox'");
        SandboxDebugAdapter { sandbox }
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

#[cfg(test)]
mod client_api_tests {
    use crate::api::{CliApi, SandboxDebugAdapter};
    use crate::utils::tests::{get_root_dir, SRC};

    #[test]
    fn start_test() {
        let sandbox_adapter = SandboxDebugAdapter::start(get_root_dir().join(SRC).to_str().unwrap());
        let imports = sandbox_adapter.sandbox.module.imports();

        assert_eq!(imports.is_empty(), false);
    }
}
