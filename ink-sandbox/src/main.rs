use crate::api::{dispatch_command, DapCommand};
use crate::dap_handler::CliHandler;
use std::io::{BufReader, Read, Write};
use std::ops::DerefMut;
use std::rc::Rc;
use std::sync::Mutex;
use crate::api::DapCommand::Disconnect;

mod api;
mod dap_handler;
mod sandbox;
mod utils;

// {"command":"launch","type":"request","seq":1}
// {"seq":1,"type":"request","command":"initialize","arguments":{"path":"/Users/maliketh/ink/ink-sandbox-trace/ink-trace-extension/sampleWorkspace/lib.rs"}}
fn main() {
    let stdin = std::io::stdin();
    let mut stdout = std::io::stdout();
    let mut reader = Rc::new(Mutex::new(BufReader::new(stdin.lock())));

    loop {
        let api = DapCommand::from(reader.as_ref().lock().unwrap().deref_mut());
        let mut handler = CliHandler::new();
        let result = dispatch_command(&mut handler, api.clone());

        writeln!(stdout, "{}", result).unwrap();
        if api == Disconnect {
            break;
        }
        stdout.flush().unwrap();
    }
}
