import time
import json

from wasmtime import Linker, Module, Store, WasiConfig
import os
import tempfile

# Build the request JSON string to pass into policy program given a request object
def build_request_JSON(request):
    # Build JSON data for request
    request_data = {}
    request_data['method'] = request.method
    request_data['uri'] = request.uri
    
    # check if request contain JSON body
    request_body = None
    headers = {k:v for k, v in request.headers.items()}
    if "Content-Type" in headers:
        if headers["Content-Type"] == "application/json":
            request_body = request.data
    
    if request_body == None:
        request_data['body'] = "null"
    else:
        request_data['body'] = json.dumps(request_body)

    # TODO: header contains Token. Is this a security concern??
    request_data['headers'] = headers
    request_data['time'] = time.time()

    json_data = json.dumps(request_data)
    return json_data

def run_policy(linker, policy_addr, program_name, request_str, history_str):
    # Design: https://docs.rs/wasmtime/latest/wasmtime/#example-architecture

    # Module is the unit of deployment, loading, and compilation
    # Module.from_file compiles .wasm binary into wasm Module
    # Most expensive operation
    # we should consider caching Modules! 
    policy_module = Module.from_file(linker.engine, policy_addr)

    config = WasiConfig()
    config.argv = (program_name, request_str, history_str)
    config.preopen_dir(".", "/")
    print("running policy with hash: " + program_name)
    with tempfile.TemporaryDirectory() as chroot:

        out_log = os.path.join(chroot, "out.log")
        err_log = os.path.join(chroot, "err.log")
        config.stdout_file = out_log
        config.stderr_file = err_log

        # Store is a unit of isolation in wasmtime
        # containes wasm objects
        # We must have one Store per request, because Store dont' have GC and isolation.
        store = Store(linker.engine)
        store.set_wasi(config)

        # instantiated module
        # both new store and instantiate are very cheap
        instance = linker.instantiate(store, policy_module)

        # _start is the default wasi main function
        start = instance.exports(store)["_start"]

        try:
            start(store)
        except Exception as e:
            print(e)
            raise

        with open(out_log) as f:
            result = f.read()
            print("Policy returned: " + result)
            if "Deny" in result:
                return False
            elif "Accept" in result:
                return True
            else:
                return False
        