use std::env;
use std::path::PathBuf;

fn main() {
    // 只有在启用 mpv feature 时才配置链接
    #[cfg(feature = "mpv")]
    {
        let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
        let mpv_lib_dir = manifest_dir.join("libs").join("mpv").join("lib");
        let mpv_bin_dir = manifest_dir.join("libs").join("mpv").join("bin");

        // 告诉 Cargo 在哪里找 libmpv
        println!("cargo:rustc-link-search=native={}", mpv_lib_dir.display());
        
        // 链接 mpv 库
        println!("cargo:rustc-link-lib=dylib=mpv");

        // 在 Windows 上，确保运行时能找到 DLL
        let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
        let target_dir = out_dir.ancestors().nth(3).unwrap(); // 从 OUT_DIR 回到 target/debug 或 target/release
        
        // 尝试复制 libmpv-2.dll 或 mpv-2.dll
        let dll_src = if mpv_bin_dir.join("libmpv-2.dll").exists() {
            mpv_bin_dir.join("libmpv-2.dll")
        } else {
            mpv_bin_dir.join("mpv-2.dll")
        };
        
        let dll_dst = target_dir.join("mpv-2.dll");
        
        if dll_src.exists() && !dll_dst.exists() {
            std::fs::copy(&dll_src, &dll_dst).expect("Failed to copy mpv DLL to target directory");
            println!("cargo:warning=Copied {} to {}", dll_src.file_name().unwrap().display(), dll_dst.display());
        }

        // 监听 libs 目录变化
        println!("cargo:rerun-if-changed=libs/mpv/lib/mpv.lib");
        println!("cargo:rerun-if-changed=libs/mpv/bin/");
    }
}
