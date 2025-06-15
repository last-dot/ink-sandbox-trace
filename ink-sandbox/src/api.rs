use crate::api::DapCommand::*;
use crate::sandbox::Sandbox;
use crate::utils::find_polkavm;
use serde::Deserialize;
use serde_json::{json, Value};
use std::io::{BufRead, BufReader, StdinLock};

#[derive(Debug, Deserialize)]
struct DapRequestArgs {
    path: Option<String>,
}

#[derive(Debug, Deserialize)]
struct DapRequest {
    #[serde(rename = "type")]
    typ: String,
    command: String,
    arguments: Option<DapRequestArgs>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DapCommand {
    Initialize(Option<String>), // Инициализация отладчика
    Launch,                     // Запуск отладки
    Disconnect,                 // Отключение отладчика
    ConfigurationDone,          // Завершение конфигурации
    SetBreakpoints(Vec<usize>), // Установка брейкпоинтов
    Continue,                   // Продолжить выполнение
    Next,                       // Step Over (шаг через)
    StepIn,                     // Step In (шаг внутрь)
    StepOut,                    // Step Out (шаг наружу)
    Pause,                      // Приостановить выполнение
    Threads,                    // Список потоков (один поток)
    StackTrace,                 // Стек вызовов
    Scopes,                     // Области видимости переменных
    Variables,                  // Переменные
    Unknown(String),            // Любая неподдерживаемая команда
}

pub trait DapHandler {
    fn handle_initialize(&mut self, path: Option<String>) -> Value;
    fn handle_launch(&mut self) -> Value;
    fn handle_disconnect(&mut self) -> Value;
    fn handle_configuration_done(&mut self) -> Value;
    fn handle_set_breakpoints(&mut self, lines: Vec<usize>) -> Value;
    fn handle_continue(&mut self) -> Value;
    fn handle_next(&mut self) -> Value;
    fn handle_step_in(&mut self) -> Value;
    fn handle_step_out(&mut self) -> Value;
    fn handle_pause(&mut self) -> Value;
    fn handle_threads(&mut self) -> Value;
    fn handle_stack_trace(&mut self) -> Value;
    fn handle_scopes(&mut self) -> Value;
    fn handle_variables(&mut self) -> Value;
    fn handle_unknown(&mut self, command: String) -> Value;
}

pub fn dispatch_command<H: DapHandler>(handler: &mut H, command: DapCommand) -> Value {
    match command {
        Initialize(path) => handler.handle_initialize(path),
        Launch => handler.handle_launch(),
        Disconnect => handler.handle_disconnect(),
        ConfigurationDone => handler.handle_configuration_done(),
        SetBreakpoints(lines) => handler.handle_set_breakpoints(lines),
        Continue => handler.handle_continue(),
        Next => handler.handle_next(),
        StepIn => handler.handle_step_in(),
        StepOut => handler.handle_step_out(),
        Pause => handler.handle_pause(),
        Threads => handler.handle_threads(),
        StackTrace => handler.handle_stack_trace(),
        Scopes => handler.handle_scopes(),
        Variables => handler.handle_variables(),
        Unknown(name) => handler.handle_unknown(name),
    }
}

pub struct CliHandler {
    sandbox: Option<Sandbox>,
}

impl CliHandler {
    pub fn new() -> CliHandler {
        CliHandler { sandbox: None }
    }
}

impl DapHandler for CliHandler {
    fn handle_initialize(&mut self, path: Option<String>) -> Value {
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
        json!({ "command": "initialized", "path": polkavm })
    }

    fn handle_launch(&mut self) -> Value {
        json!({"type": "Launch", "polkavm": true})
    }

    fn handle_disconnect(&mut self) -> Value {
        json!({"type": "handle_disconnect", "polkavm": true})
    }

    fn handle_configuration_done(&mut self) -> Value {
        json!({"type": "handle_configuration_done", "polkavm": true})
    }

    fn handle_set_breakpoints(&mut self, lines: Vec<usize>) -> Value {
        json!({"type": "handle_set_breakpoints", "polkavm": true})
    }

    fn handle_continue(&mut self) -> Value {
        json!({"type": "handle_continue", "polkavm": true})
    }

    fn handle_next(&mut self) -> Value {
        json!({"type": "handle_next", "polkavm": true})
    }

    fn handle_step_in(&mut self) -> Value {
        json!({"type": "handle_step_in", "polkavm": true})
    }

    fn handle_step_out(&mut self) -> Value {
        json!({"type": "handle_step_out", "polkavm": true})
    }

    fn handle_pause(&mut self) -> Value {
        json!({"type": "handle_pause", "polkavm": true})
    }

    fn handle_threads(&mut self) -> Value {
        json!({"type": "handle_threads", "polkavm": true})
    }

    fn handle_stack_trace(&mut self) -> Value {
        json!({"type": "handle_stack_trace", "polkavm": true})
    }

    fn handle_scopes(&mut self) -> Value {
        json!({"type": "handle_scopes", "polkavm": true})
    }

    fn handle_variables(&mut self) -> Value {
        json!({"type": "handle_variables", "polkavm": true})
    }

    fn handle_unknown(&mut self, command: String) -> Value {
        json!({"type": "handle_unknown", "polkavm": true})
    }
}

impl From<&mut BufReader<StdinLock<'_>>> for DapCommand {
    fn from(reader: &mut BufReader<StdinLock>) -> Self {
        let mut line = String::new();
        if reader.read_line(&mut line).unwrap() == 0 {
            return Unknown(String::from("EOF"));
        };

        let request = serde_json::from_str::<DapRequest>(&line).unwrap();

        match request.command.as_str() {
            "initialize" => Initialize(request.arguments.map(|a| a.path.unwrap())),
            "launch" => Launch,
            "disconnect" => Disconnect,
            "configurationDone" => ConfigurationDone,
            "setBreakpoints" => SetBreakpoints(Vec::new()),
            "continue" => Continue,
            "next" => Next,
            "stepIn" => StepIn,
            "stepOut" => StepOut,
            "pause" => Pause,
            "threads" => Threads,
            "stackTrace" => StackTrace,
            "scopes" => Scopes,
            "variables" => Variables,
            other => Unknown(other.to_string()),
        }
    }
}
