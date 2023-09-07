import time
import json

from wasmtime import Config, Engine, Linker, Module, Store, WasiConfig
import os
import tempfile

# Build the request JSON string to pass into policy program given a request object
def build_request_JSON(request):
    # Build JSON data for request
    request_data = {}
    request_data['method'] = request.method
    request_data['uri'] = request.uri
    request_body = request.data
    if request_body == None:
        request_data['body'] = "null"
    else:
        request_data['body'] = json.dumps(request_body)

    # TODO: header contains Token. Is this a security concern??
    request_data['headers'] = {k:v for k, v in request.headers.items()}
    request_data['time'] = time.time()

    json_data = json.dumps(request_data)
    return json_data

def run_policy(policy_addr, program_name, request_str, history_str = None):

    engine_cfg = Config()
    linker = Linker(Engine(engine_cfg))
    linker.define_wasi()
    python_module = Module.from_file(linker.engine, policy_addr)
    config = WasiConfig()
    config.argv = (program_name, request_str)
    config.preopen_dir(".", "/")

    with tempfile.TemporaryDirectory() as chroot:
        out_log = os.path.join(chroot, "out.log")
        err_log = os.path.join(chroot, "err.log")
        config.stdout_file = out_log
        config.stderr_file = err_log

        store = Store(linker.engine)

        store.set_wasi(config)
        instance = linker.instantiate(store, python_module)

        # _start is the default wasi main function
        start = instance.exports(store)["_start"]
        try:
            start(store)
        except Exception as e:
            print(e)
            raise

        with open(out_log) as f:
            result = f.read()
            if "Deny" in result:
                return False
            elif "Accept" in result:
                return True
            else:
                return False
        