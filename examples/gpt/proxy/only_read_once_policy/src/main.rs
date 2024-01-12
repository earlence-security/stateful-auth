//use serde_json::{Result, Value};
use std::env;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize)]
struct Request {
    method: String,
    uri: String,
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

    // policy
    if parsed_req.uri == "http://127.0.0.1:5000/api/emails"{
        println!("Accept");
    } else if parsed_req.uri.starts_with("http://127.0.0.1:5000/api/emails") && parsed_req.method == "GET"{
        for (obj_id, history) in parsed_hist {
            for entry in history {
                if entry.api.starts_with("/api/emails") && entry.method == "GET"{
                    println!("Deny");
                    return
                }
            }
        }
        println!("Accept");
    } else {
        // defaut to deny
        println!("Deny");
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