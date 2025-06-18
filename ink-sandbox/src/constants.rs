pub(crate) mod messages {
    pub(crate) const EOF: &str = "EOF";
    pub(crate) const PARAMS_NOT_FOUND: &str = "No params found";
    pub(crate) const JSON_RPC_VERSION: &str = "2.0";
    pub(crate) const POLKAVM_FILE_NOT_FOUND: &str = "Could not find the polkavm file";
    pub(crate) const STD_OUT_ERROR: &str = "Could not write to stdout";
    pub(crate) const STD_OUT_FLUSH_ERROR: &str = "Could not flush to stdout";
    pub(crate) const HEADER_PARSING_ERROR: &str = "Header parsing error";
}

pub(crate) mod headers {
    pub(crate) const CONTENT_LENGTH: &str = "Content-Length";
}
