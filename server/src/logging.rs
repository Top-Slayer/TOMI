#[macro_export]
macro_rules! log_concat {
    ($($arg:tt)*) => {{
        let now = chrono::Utc::now().with_timezone(&chrono_tz::Asia::Vientiane);
        format!(
            "[{}] [SERVER]: {}",
            now.format("%d-%m-%Y %H:%M:%S.%f"),
            format!($($arg)*)
        )
    }};
}
