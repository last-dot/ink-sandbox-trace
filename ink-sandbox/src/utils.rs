use std::path::{Path, PathBuf};

const CARGO_TOML: &str = "Cargo.toml";
const POLKAVM_LOCATION: &str = "target/ink/flipper.polkavm";

pub(crate) fn find_root(rust_src: &str) -> Option<PathBuf> {
    let current_src = Path::new(rust_src);
    let mut current_dir = current_src.parent()?;

    if current_dir.as_os_str().is_empty() {
        return None;
    }

    let project_root_file = CARGO_TOML;

    loop {
        let project_root_candidate = current_dir.join(project_root_file);
        if project_root_candidate.exists() {
            return Some(project_root_candidate.parent().unwrap().to_path_buf());
        }

        match current_dir.parent() {
            Some(dir) => current_dir = dir,
            None => break,
        }
    }

    None
}

pub(crate) fn find_polkavm(rust_src: &str) -> Option<PathBuf> {
    let root = find_root(rust_src)?;

    let polkavm_candidate = root.join(POLKAVM_LOCATION);
    if polkavm_candidate.exists() {
        return Some(polkavm_candidate);
    }
    None
}

#[cfg(test)]
pub(crate) mod tests {
    use crate::utils::{find_polkavm, find_root};
    use std::path::PathBuf;

    pub(crate) const SRC: &str = "ink-trace-extension/sampleWorkspace/lib.rs";
    const POLKAVM_LOCATION: &str = "ink-trace-extension/sampleWorkspace/target/ink/flipper.polkavm";
    const SRC_CONTRACT_LOCATION: &str = "ink-trace-extension/sampleWorkspace";

    #[test]
    fn test_find_root() {
        assert_eq!(find_root(""), None);
        assert_eq!(find_root("main.rs"), None);

        let project_root = get_root_dir();
        let path = project_root.join(SRC);
        let result = find_root(path.as_os_str().to_str().unwrap());
        let expected = Some(project_root.join(SRC_CONTRACT_LOCATION));
        println!("{:?}", expected);
        assert_eq!(result, expected);
    }

    #[test]
    fn test_find_polkavm() {
        assert_eq!(find_polkavm(""), None);
        assert_eq!(find_polkavm("main.rs"), None);

        let project_root = get_root_dir();
        let path = project_root.join(SRC);
        let expected = Some(project_root.join(POLKAVM_LOCATION));
        let result = find_polkavm(path.as_os_str().to_str().unwrap());
        assert_eq!(result, expected);
    }

    pub(crate) fn get_root_dir() -> PathBuf {
        let root_dir = std::env::current_dir()
            .unwrap()
            .parent()
            .unwrap()
            .to_path_buf();
        root_dir
    }
}
