#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod llm_detector;
mod backend_manager;
mod tray;
mod window_state;

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_autostart::init(tauri_plugin_autostart::MacosLauncher::LaunchAgent, None))
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_single_instance::init(|_app, _args, _cwd| {}))
        .setup(|app| {
            // 窗口状态恢复
            let win_state = window_state::WindowState::load();
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_position(tauri::Position::Physical(tauri::PhysicalPosition { x: win_state.x, y: win_state.y }));
                let _ = window.set_size(tauri::Size::Physical(tauri::PhysicalSize { width: win_state.width, height: win_state.height }));
                if win_state.maximized {
                    let _ = window.maximize();
                }
                println!("✅ 窗口状态恢复: {}x{} @ {},{} maximized={}", win_state.width, win_state.height, win_state.x, win_state.y, win_state.maximized);
            }
            
            // LLM混合检测
            match llm_detector::detect_llm() {
                Some(config) => {
                    println!("✅ 检测到LLM: model={:?} server={:?} external={}", 
                        config.model_path, config.server_path, config.is_external);
                }
                None => {
                    println!("⚠️ 未检测到外置LLM，将使用内置sidecar或提示用户配置");
                    println!("   检测顺序: env MODEL_PATH > config/model_paths.json > D:\\llama.cpp\\ > C:\\llama.cpp\\ > 内置");
                }
            }
            
            // Backend sidecar
            let backend_manager = backend_manager::BackendManager::new(8000);
            println!("🚀 Backend sidecar: {}", backend_manager.health_url());
            
            // 托盘
            if let Err(e) = tray::create_tray(app) {
                eprintln!("创建托盘失败: {}", e);
            }
            
            // 全局快捷键 Alt+Space
            #[cfg(desktop)]
            {
                use tauri_plugin_global_shortcut::{Code, Modifiers, Shortcut, ShortcutState};
                let app_handle = app.handle().clone();
                if let Err(e) = app.global_shortcut().on_shortcut("Alt+Space", move |_app, _shortcut, event| {
                    if event.state == ShortcutState::Pressed {
                        if let Some(window) = app_handle.get_webview_window("main") {
                            if window.is_visible().unwrap_or(false) {
                                let _ = window.hide();
                            } else {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                    }
                }) {
                    eprintln!("注册全局快捷键失败: {}", e);
                } else {
                    println!("✅ 全局快捷键 Alt+Space 已注册");
                }
            }
            
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // 保存窗口状态
                let state = window_state::WindowState::from_tauri_window(window);
                state.save();
                println!("💾 窗口状态已保存: {:?}", state);
                
                window.hide().unwrap();
                api.prevent_close();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
