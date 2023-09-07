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

#[derive(Serialize, Deserialize)]
struct SendMoney {
    recipient: String,
    amount: i32,
}

//TODO: add error handling
fn main() {
    let args: Vec<String> = env::args().collect();
    let json_str = &args[1];

    let parsed: Request = read_json(json_str);

    let parsed_sendmoney: SendMoney = read_json_body(parsed.body.as_str());

    // policy
    if parsed.uri == "http://127.0.0.1:5000/api/send-money" {

        if parsed_sendmoney.amount > 100{
            println!("Deny");
            return ();
        }
        println!("Accept");

    } else {
        println!("Accept");
    }
}

fn read_json(json_str: &str) -> Request {
    // Parse the string of data into serde_json::Value.
    let v: Request = serde_json::from_str(json_str).unwrap();
    return v;
}

fn read_json_body(json_str: &str) -> SendMoney {
    // Parse the string of data into serde_json::Value.
    let v: SendMoney = serde_json::from_str(json_str).unwrap();
    return v;
}