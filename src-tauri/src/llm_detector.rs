use std::path::{Path, PathBuf};
use std::env;

#[derive(Debug, Clone)]
pub struct LlmConfig {
    pub server_path: PathBuf,
    pub model_path: PathBuf,
    pub is_external: bool,
}

pub fn detect_llm() -> Option<LlmConfig> {
    // 优先级：env > config/model_paths.json > D:\llama.cpp\ > C:\llama.cpp\ > PATH > 内置sidecar
    
    // 1. env MODEL_PATH/QWEN_MODEL_PATH/LLM_MODEL_PATH/ZANE_MODEL_PATH/HF_MODEL_PATH
    for env_key in &["MODEL_PATH", "QWEN_MODEL_PATH", "LLM_MODEL_PATH", "ZANE_MODEL_PATH", "HF_MODEL_PATH"] {
        if let Ok(path) = env::var(env_key) {
            let p = PathBuf::from(&path);
            if p.exists() {
                return Some(LlmConfig {
                    server_path: find_llama_server(),
                    model_path: p,
                    is_external: true,
                });
            }
        }
    }
    
    // 2. config/model_paths.json
    if let Some(config) = read_model_paths_config() {
        if config.exists() {
            return Some(LlmConfig {
                server_path: find_llama_server(),
                model_path: config,
                is_external: true,
            });
        }
    }
    
    // 3. D:\llama.cpp\ / C:\llama.cpp\ / 常见路径
    for base in &["D:\\llama.cpp", "C:\\llama.cpp", "D:\\llama", "C:\\llama", "/tmp/llama.cpp"] {
        let base_path = PathBuf::from(base);
        if base_path.exists() {
            if let Some(gguf) = find_gguf_in_dir(&base_path) {
                return Some(LlmConfig {
                    server_path: base_path.join("llama-server.exe"),
                    model_path: gguf,
                    is_external: true,
                });
            }
        }
    }
    
    // 4. 未找到，返回None，提示用户配置，符合v0914-14找不到报错退出
    None
}

fn find_llama_server() -> PathBuf {
    for path in &["D:\\llama.cpp\\llama-server.exe", "C:\\llama.cpp\\llama-server.exe", "llama-server.exe", "llama-server"] {
        let p = PathBuf::from(path);
        if p.exists() {
            return p;
        }
    }
    PathBuf::from("llama-server")
}

fn read_model_paths_config() -> Option<PathBuf> {
    // 读取config/model_paths.json
    let config_path = PathBuf::from("../config/model_paths.json");
    if !config_path.exists() {
        return None;
    }
    if let Ok(content) = std::fs::read_to_string(&config_path) {
        if let Ok(json) = serde_json::from_str::<serde_json::Value>(&content) {
            // 尝试多个字段
            for key in &["qwen", "model_path", "llm_path", "default"] {
                if let Some(path_str) = json.get(key).and_then(|v| v.as_str()) {
                    return Some(PathBuf::from(path_str));
                }
            }
            // 如果是数组，取第一个
            if let Some(arr) = json.as_array() {
                if let Some(first) = arr.first().and_then(|v| v.as_str()) {
                    return Some(PathBuf::from(first));
                }
            }
        }
    }
    None
}

fn find_gguf_in_dir(dir: &Path) -> Option<PathBuf> {
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().map_or(false, |ext| ext == "gguf") {
                return Some(path);
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_detect_llm_no_panic() {
        let _ = detect_llm();
    }
    
    #[test]
    fn test_find_llama_server_no_panic() {
        let _ = find_llama_server();
    }
}
