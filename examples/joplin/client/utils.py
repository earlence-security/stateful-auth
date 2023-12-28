import os

def read_policy_hashes():
    policy_folder = "policies"

    files = os.listdir(os.path.join(os.getcwd(), policy_folder))
    wasm_files = [file for file in files if file.endswith(".wasm")]
    hashes = [file.replace(".wasm", "") for file in wasm_files]
    return hashes

def build_policy_decription_dict():
    hashes = read_policy_hashes()

    policy_path= os.path.join(os.getcwd(), "policies")
    files = os.listdir(policy_path)
    policy_decription_dict = {}
    for hash in hashes:
        file_path = os.path.join(policy_path, hash + ".txt")
        with open(file_path, 'r') as file:
            policy_decription_dict[hash] = file.read()
    
    return policy_decription_dict