use std::env;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize)]
struct Request {
    method: String,
    uri: String,
    path: String,
    body: String,
    headers: HashMap<String, String>,
    time: f32
}

#[derive(Serialize, Deserialize)]
struct Event {
    title: Option<String>,
    description: Option<String>,
    time: Option<String>,
    location: Option<String>,
}

//TODO: add error handling
fn main() {
    let args: Vec<String> = env::args().collect();
    let json_str = &args[1];

    let parsed: Request = read_json(json_str);

    // Create or modify an event.
    if parsed.path.starts_with("/api/events") && parsed.method == "POST" {
        let e: Event = read_json_body(parsed.body.as_str());
        if e.title.is_some() && !(e.title.unwrap().starts_with("Meeting")) {
                println!("Deny");
                return;
        }
    }
    println!("Accept");
    return;
}

fn read_json(json_str: &str) -> Request {
    // Parse the string of data into serde_json::Value.
    let v: Request = serde_json::from_str(json_str).unwrap();
    return v;
}

fn read_json_body(json_str: &str) -> Event {
    // Parse the string of data into serde_json::Value.
    let v: Event = serde_json::from_str(json_str).unwrap();
    return v;
}
