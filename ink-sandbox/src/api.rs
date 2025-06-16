use std::fmt::{Display, Formatter};
use crate::api::DapCommand::*;
use crate::dap_handler::DapHandler;
use serde::{Deserialize, Serialize};
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

#[derive(Debug, Serialize)]
pub(crate) struct DapResponse {
    pub(crate) command: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub(crate) message: Option<String>,
    pub(crate) status: bool,
}

impl DapResponse {
    pub(crate) fn new(command: &str, status: bool) -> Self {
        DapResponse {
            command: command.to_string(),
            message: None,
            status,
        }
    }

    pub(crate) fn set_message(&mut self, message: &str) {
        self.message = Some(message.to_string());
    }
}

impl Display for DapResponse {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        let j = json!(self);
        write!(f, "{}", j)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DapCommand {
    Initialize(Option<String>), // Инициализация отладчика
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

pub fn dispatch_command<T, H: DapHandler<T>>(handler: &mut H, command: DapCommand) -> T {
    match command {
        Initialize(path) => handler.handle_initialize(path),
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

impl From<&mut BufReader<StdinLock<'_>>> for DapCommand {
    fn from(reader: &mut BufReader<StdinLock>) -> Self {
        let mut line = String::new();
        if reader.read_line(&mut line).unwrap() == 0 {
            return Unknown(String::from("EOF"));
        };

        let request = serde_json::from_str::<DapRequest>(&line).unwrap();

        match request.command.as_str() {
            "initialize" => Initialize(request.arguments.map(|args| args.path.unwrap())),
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
