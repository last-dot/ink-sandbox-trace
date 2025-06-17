use crate::api::DapCommand::*;
use crate::dap_handler::DapHandler;
use crate::domain::params::InitializeParams;
use crate::domain::rpc::JsonRpcRequest;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DapCommand {
    Initialize(Option<InitializeParams>), // Инициализация отладчика
    Pause,                                // Приостановить выполнение
    Continue,                             // Продолжить выполнение
    Disconnect,                           // Отключение отладчика
    Next,                                 // Step Over (шаг через)

    // ConfigurationDone,          // Завершение конфигурации
    // SetBreakpoints(Vec<usize>), // Установка брейкпоинтов
    // StepIn,                     // Step In (шаг внутрь)
    // StepOut,                    // Step Out (шаг наружу)
    // Threads,                    // Список потоков (один поток)
    // StackTrace,                 // Стек вызовов
    // Scopes,                     // Области видимости переменных
    // Variables,                  // Переменные
    Unknown(String), // Любая неподдерживаемая команда
}

pub fn dispatch_command<T, H: DapHandler<T>>(handler: &mut H, command: DapCommand) -> T {
    match command {
        Initialize(path) => handler.handle_initialize(path.map(|x| x.path)),
        Disconnect => handler.handle_disconnect(),
        Continue => handler.handle_continue(),
        Next => handler.handle_next(),
        Pause => handler.handle_pause(),
        Unknown(name) => handler.handle_unknown(name),
    }
}

impl From<&JsonRpcRequest> for DapCommand {
    fn from(req: &JsonRpcRequest) -> Self {
        match req.method.as_str() {
            "initialize" => Initialize(Some(InitializeParams::from(req))),
            "pause" => Pause,
            "continue" => Continue,
            "disconnect" => Disconnect,
            "next" => Next,
            other => Unknown(other.to_string()),
        }
    }
}
