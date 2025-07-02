use serde_json::{Value, to_value};
use std::{
    io::{Error, ErrorKind},
    net::SocketAddr,
};
use tokio::{
    io::{AsyncReadExt, AsyncWriteExt},
    net::{TcpListener, TcpSocket},
};

use crate::{domain::{JsonRpcError, JsonRpcRequest}, methods};

#[derive(Debug, Clone)]
pub(crate) struct SandboxRpc {
    host: String,
    port: String,
    max_connections: u8,
    buf_capacity: usize,
}

impl Default for SandboxRpc {
    fn default() -> Self {
        simple_logger::init_with_level(log::Level::Debug).expect("Logger initialization faled");
        SandboxRpc {
            host: String::from("127.0.0.1"),
            port: String::from("9229"),
            max_connections: 5,
            buf_capacity: 1024,
        }
    }
}

impl SandboxRpc {
    pub(crate) fn url(&self) -> Result<SocketAddr, Error> {
        let url = format!("{}:{}", self.host, self.port);
        url.parse::<SocketAddr>()
            .map_err(|_| Error::new(ErrorKind::InvalidInput, "invalid addr"))
    }

    pub(crate) fn socket(&self) -> Result<TcpSocket, Error> {
        let socket = TcpSocket::new_v4()?;
        socket.set_keepalive(false)?;
        socket.set_reuseaddr(true)?;
        socket.set_reuseport(true)?;
        socket.bind(self.url()?)?;
        Ok(socket)
    }

    pub(crate) fn listener(&self) -> Result<TcpListener, Error> {
        let socket = self.socket()?;
        let listener = socket.listen(self.max_connections as u32)?;
        Ok(listener)
    }

    pub async fn serve(&self) -> Result<(), std::io::Error> {
        let listener = self.listener()?;
        loop {
            let (mut stream, addr) = listener.accept().await?;
            log::info!("Incoming from client: {addr}");
            let buf_capacity = self.buf_capacity;
            tokio::spawn(async move {
                let mut buf = vec![0u8; buf_capacity];
                loop {
                    match stream.read(&mut buf).await {
                        Ok(n) if n > 0 => {
                            let request = std::str::from_utf8(&buf[..n])
                                .map(|s| s.trim_end())
                                .unwrap_or("");
                            log::debug!("Incoming request string: {request}");
                            let response = dispatch_request(request).await;
                            let response = format!("{}\n", response.to_string());
                            if let Err(e) = stream.write_all(response.as_bytes()).await {
                                log::error!("Write error: {e}");
                            }
                        }
                        Ok(_) => {
                            log::warn!("Closed");
                            break;
                        }
                        Err(e) => log::error!("Read error: {e}"),
                    }
                }
            });
        }
    }

    pub async fn serve_async(&self) -> Result<(), std::io::Error> {
        let this = self.clone();
        log::info!("[Rpc Sandbox starting]");
        tokio::spawn(async move {
            if let Err(e) = this.serve().await {
                log::error!("Serve failed: {e}");
            }
        });

        Ok(())
    }
}

pub(crate) async fn dispatch_request(request: &str) -> Value {
    let request_value = serde_json::from_str::<JsonRpcRequest>(request);
    let response = match request_value {
        Ok(req) => {
            log::info!("Resuest: {:#?}", req);
            to_value(methods::handle(req))
        }
        Err(_) => to_value(JsonRpcError {
            code: 400,
            message: "Request error. Bad request.".to_string(),
            data: None,
        }),
    };
    response.unwrap()
}
