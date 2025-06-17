use crate::api::dispatch_command;
use crate::dap_handler::CliHandler;
use crate::domain::rpc::JsonRpcRequest;
use std::io::{BufReader, Write};
use std::ops::DerefMut;
use std::rc::Rc;
use std::sync::Mutex;

mod api;
mod dap_handler;
mod sandbox;
mod utils;
mod domain;
mod constants;

// {"jsonrpc":"2.0","method":"initialize","params":{"path":"/Users/maliketh/ink/ink-sandbox-trace/ink-trace-extension/sampleWorkspace/lib.rs"},"id":1}
fn main() {
    let stdin = std::io::stdin();
    let mut stdout = std::io::stdout();
    let reader = Rc::new(Mutex::new(BufReader::new(stdin.lock())));

    loop {
        let request = JsonRpcRequest::from(reader.as_ref().lock().unwrap().deref_mut());
        let mut handler = CliHandler::new();
        let result = dispatch_command(&mut handler, request.as_command());

        writeln!(stdout, "{}", result.clone().with_default_headers()).unwrap();
        if request.is_disconnect() {
            break;
        }
        stdout.flush().unwrap();
    }
}
