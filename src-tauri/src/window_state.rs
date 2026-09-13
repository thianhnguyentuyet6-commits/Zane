use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct WindowState {
    pub x: i32,
    pub y: i32,
    pub width: u32,
    pub height: u32,
    pub maximized: bool,
}

impl WindowState {
    pub fn load() -> Self {
        let path = Self::config_path();
        if path.exists() {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(state) = serde_json::from_str(&content) {
                    return state;
                }
            }
        }
        Self::default()
    }
    
    pub fn save(&self) {
        let path = Self::config_path();
        if let Some(parent) = path.parent() {
            let _ = fs::create_dir_all(parent);
        }
        if let Ok(json) = serde_json::to_string_pretty(self) {
            let _ = fs::write(path, json);
        }
    }
    
    fn config_path() -> PathBuf {
        // 尝试多个位置
        if let Ok(current) = std::env::current_dir() {
            let p = current.join("config").join("window_state.json");
            if p.parent().map_or(false, |par| par.exists()) {
                return p;
            }
        }
        PathBuf::from("config/window_state.json")
    }
    
    pub fn from_tauri_window(window: &tauri::WebviewWindow) -> Self {
        let mut state = Self::default();
        if let Ok(pos) = window.outer_position() {
            state.x = pos.x;
            state.y = pos.y;
        }
        if let Ok(size) = window.outer_size() {
            state.width = size.width;
            state.height = size.height;
        }
        if let Ok(max) = window.is_maximized() {
            state.maximized = max;
        }
        state
    }
}

impl Default for WindowState {
    fn default() -> Self {
        Self {
            x: 100,
            y: 100,
            width: 1200,
            height: 800,
            maximized: false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_window_state_default() {
        let state = WindowState::default();
        assert_eq!(state.width, 1200);
        assert_eq!(state.height, 800);
    }
    
    #[test]
    fn test_window_state_save_load() {
        let state = WindowState {
            x: 50,
            y: 50,
            width: 1000,
            height: 700,
            maximized: false,
        };
        // 不实际写入文件，仅测试序列化
        let json = serde_json::to_string(&state).unwrap();
        let loaded: WindowState = serde_json::from_str(&json).unwrap();
        assert_eq!(loaded.x, 50);
        assert_eq!(loaded.width, 1000);
    }
}
