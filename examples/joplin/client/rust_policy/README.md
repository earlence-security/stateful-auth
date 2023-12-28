## To create a new rust project
` cargo new foldername `

Then write policy adhering to spec

## Build to wasm
` cargo build --target wasm32-wasi --release `

## Optimizing for size
put the following to the ` Cargo.toml ` file:

``` 
[profile.release]
strip = "debuginfo"
lto = true
opt-level = 's' 
```
After building to wasm, furthur optimize by running:

`  wasm-opt -Os file.wasm -o file.wasm `

### Tips for optimizing for size
(TODO)
1. No string formatting
2. Write code such that Rust does not "panick".
   1. manually check index out of bound
   2. no Result.unwrap()
   3. https://rustwasm.github.io/docs/book/reference/code-size.html#avoid-panicking

## To get the SHA of program
` openssl dgst -sha256 file.wasm `
