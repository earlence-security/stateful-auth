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
    time: f64
}

#[derive(Deserialize, Serialize)]
struct History {
    api: String,
    method: String,
    counter: i32,
    timestamp: f64,
}

type HistoryMap = HashMap<String, Vec<History>>;

fn main() {
    let args: Vec<String> = env::args().collect();
    let json_str = &args[1];
    let hist_str = &args[2];

    let parsed_req: Request = read_json(json_str);
    let mut parsed_hist: HistoryMap = read_history(hist_str);

    for history in parsed_hist.values_mut() {
        // find an entry to update (same method and api)
        let mut found = false;
        for entry in history.iter_mut() {
            if entry.method == parsed_req.method && entry.api == parsed_req.path {
                entry.counter = entry.counter + 1;
                entry.timestamp = parsed_req.time;
                found = true;
                break;
            }
        }
        if found {
            continue;
        }
        // not found, append a new history
        let newhist = History {api: parsed_req.path.clone(), method: parsed_req.method.clone(), counter: 0, timestamp: parsed_req.time};
        history.push(newhist);
    }
    let ret = serde_json::to_string(&parsed_hist).unwrap();
    print!("{}", ret);
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