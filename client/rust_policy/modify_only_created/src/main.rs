//use serde_json::{Result, Value};
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

#[derive(Deserialize, Serialize)]
struct History {
    api: String,
    method: String,
    counter: i32,
    timestamp: f64,
}

type HistoryMap = HashMap<String, Vec<History>>;

//TODO: add error handling
fn main() {
    let args: Vec<String> = env::args().collect();
    let json_str = &args[1];
    let hist_str = &args[2];

    let parsed_req: Request = read_json(json_str);
    let parsed_hist: HistoryMap = read_history(hist_str);

    // Modify or delete an existing event.
    if parsed_req.path.starts_with("/api/events") && parsed_req.method != "GET" {
        // Accept if creating a new event.
        if parsed_req.path == "/api/events" && parsed_req.method == "POST" {
            println!("Accept");
            return
        }
        // Check history if modifying or delete an existing event.
        for (_obj_id, history) in parsed_hist {
            for entry in history {
                if entry.method == "POST" && entry.api == "/api/events" {
                    println!("Accept");
                    return
                }
            }
        }
        println!("Deny");
    } else {
        println!("Accept");
    }
}

fn read_json(json_str: &str) -> Request {
    // Parse the string of data into serde_json::Value.
    let v: Request = serde_json::from_str(json_str).unwrap();
    return v;
}

fn read_history(json_str: &str) -> HistoryMap {
    // Parse the string of data into serde_json::Value.
    let v: HistoryMap = serde_json::from_str(json_str).unwrap();
    return v;
}