use crate::api::dispatch_request;
use crate::constants::messages::{STD_OUT_ERROR, STD_OUT_FLUSH_ERROR};
use crate::dap_handler::CliHandler;
use crate::domain::rpc::JsonRpcRequest;
use std::io::{BufReader, Write};
use std::ops::DerefMut;
use std::rc::Rc;
use std::sync::Mutex;

mod api;
mod constants;
mod dap_handler;
mod domain;
mod sandbox;

// {"jsonrpc":"2.0","method":"initialize","params":{"polkavm":"/Users/maliketh/ink/ink-sandbox-trace/ink-trace-extension/sampleWorkspace/target/ink/flipper.polkavm"},"id":"1"}
fn main() {
    let stdin = std::io::stdin();
    let mut stdout = std::io::stdout();
    let reader = Rc::new(Mutex::new(BufReader::new(stdin.lock())));

    loop {
        let request = JsonRpcRequest::from(reader.as_ref().lock().unwrap().deref_mut());
        let mut handler = CliHandler::new();
        let result = dispatch_request(&mut handler, request);

        writeln!(stdout, "{}", result.clone().with_default_headers()).expect(STD_OUT_ERROR);
        stdout.flush().expect(STD_OUT_FLUSH_ERROR);
    }
}
