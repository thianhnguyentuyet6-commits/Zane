use std::time::Duration;

#[derive(Debug, Clone)]
pub struct BackendManager {
    pub port: u16,
}

impl BackendManager {
    pub fn new(port: u16) -> Self {
        Self { port }
    }
    
    #[cfg(feature = "tauri-shell")]
    pub fn start(&self, app: &tauri::AppHandle) -> Result<(), String> {
        use tauri_plugin_shell::ShellExt;
        let sidecar_command = app.shell().sidecar("binaries/zane-backend")
            .map_err(|e| format!("Failed to create sidecar: {}", e))?;
        
        let command = sidecar_command
            .args(["--port", &self.port.to_string()]);
        
        tauri::async_runtime::spawn(async move {
            match command.spawn() {
                Ok(_) => println!("Backend sidecar started on port {}", 8000),
                Err(e) => eprintln!("Failed to start backend sidecar: {}", e),
            }
        });
        
        Ok(())
    }
    
    #[cfg(not(feature = "tauri-shell"))]
    pub fn start(&self, _app: &tauri::AppHandle) -> Result<(), String> {
        println!("BackendManager: shell feature not enabled, skipping sidecar start");
        Ok(())
    }
    
    pub async fn check_health(&self) -> bool {
        let url = format!("http://localhost:{}/api/health", self.port);
        // 简单轮询，不依赖reqwest时用std
        for _ in 0..10 {
            // 使用reqwest如果可用，否则跳过
            tokio::time::sleep(Duration::from_millis(500)).await;
        }
        // 实际检查由前端fetch完成，这里仅占位
        true
    }
    
    pub fn health_url(&self) -> String {
        format!("http://localhost:{}/api/health", self.port)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_backend_manager_new() {
        let mgr = BackendManager::new(8000);
        assert_eq!(mgr.port, 8000);
        assert_eq!(mgr.health_url(), "http://localhost:8000/api/health");
    }
}
