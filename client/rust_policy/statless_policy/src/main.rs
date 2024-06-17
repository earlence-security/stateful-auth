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

//TODO: add error handling
fn main() {
    let args: Vec<String> = env::args().collect();
    let json_str = &args[1];

    let parsed: Request = read_json(json_str);

    //println!("the request have method {} with uri {} at time {}", parsed.method, parsed.uri, parsed.time);

    // policy
    if parsed.uri == "http://127.0.0.1:5000/api/me" {
        println!("Accept");
    } else {
        println!("Deny");
    }
}

fn read_json(json_str: &str) -> Request {
    // Parse the string of data into serde_json::Value.
    let v: Request = serde_json::from_str(json_str).unwrap();
    return v;
}