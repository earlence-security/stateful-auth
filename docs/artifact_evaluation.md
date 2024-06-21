# Artifact Evaluation

## Setup

We recommmend using the AWS instances we have set up for testing the code and reproducing the results. 

1. Open a terminal and SSH to the **server**:
```bash
ssh -i <PATH_TO_PRIVATE_KEY> ubuntu@ec2-3-18-8-25.us-east-2.compute.amazonaws.com
```
2. Open another terminal and SSH to the **client**:
```bash
ssh -i <PATH_TO_PRIVATE_KEY> ubuntu@ec2-52-8-5-83.us-west-1.compute.amazonaws.com
```
3. Download the [policy](https://github.com/earlence-security/stateful-auth/blob/eval/client/policies/77a6a23a3c4d424dba1e7efae21cef16d01f156c6d0194e406c98cf46c22bf37.wasm) and [state updater](https://github.com/earlence-security/stateful-auth/blob/eval/client/update_program/update_program.wasm) WebAssembly (WASM) on your local machine. These are the client-supplied programs that attenuate the token's authority and define the state, respectively (Section~2.2).

Note that we mark the following steps with [Server-side] and [Client-side] to clear which terminal each commands should be run on.

## Get Token (Basic Test)

1. __[Server-side]__ Start the server with:
```bash
cd stateful-auth/server
AUTHLIB_INSECURE_TRANSPORT=1 gunicorn -b 0.0.0.0:5000 app:app --limit-request-line=0 --limit-request-fields=0 --limit-request-field_size=0
```
2. __[Server-side]__ Open a browser and go to http://3.18.8.25 and input any username you like to sign up (for example, `artifact-eval`).

3. __[Server-side]__ Create a client by clicking the "Create Client" button, and filling the form as follows:
```
Client Name: client_00
Client URI: http://52.8.5.83
Allowed Scope: profile
Upload Policy WASM: Upload 77a6a23a3c4d424dba1e7efae21cef16d01f156c6d0194e406c98cf46c22bf37.wasm (the policy WASM you have downloaded)
Upload State Updater WASM: Upload update_program.wasm (the state updater WASM you have downloaded)
Redirect URIs: http://52.8.5.83/auth
Allowed Grant Types: authorization_code
Allowed Response Types: code
Token Endpoint Auth Method: client_secret_basic
```
Note: we leave `Policy Program Hashes` and `Policy Program Endpoint` as blank. This is an alternative way to upload policy program WASM.

4. __[Server-side]__ Click "Submit". You will be directed to the page listing all the registered clients.

5. __[Client-side]__ Start the client with:
```bash
cd stateful-auth/client
CLIENT_ID=<CLIENT_ID> CLIENT_SECRET=<CLIENT_SECRET> ACCESS_TOKEN_URL='http://3.18.8.25/oauth/token' AUTHORIZE_URL='http://3.18.8.25/oauth/authorize' REDIRECT_URI='http://52.8.5.83/auth' gunicorn -b 0.0.0.0:8080 app:app
```
Replace the `<CLIENT_ID>` and `<CLIENT_SECRET>` with the `client_id` and `client_id` you find in the server-side page after client's registration from the previous step.

6. __[Client-side]__ Go to http://52.8.5.83, and click "Request a Token from Auth Server". Select a policy the client has registered. For this test, let's select `77a6a23a3c4d424dba1e7efae21cef16d01f156c6d0194e406c98cf46c22bf37`. The string is a hash of a policy WASM we downloaded in the setup, which only allow modifying the events created with the same token. Click "Submit".

7. __[Client-side]__ You will see a page saying that the client application 
  is requesting a scope with a policy hash. Click "Consent?" box and click "Submit".

8. __[Client-side]__ You will see your access token, which will be used when the client makes a request to the server. Click ''send requests with this token''.

9. __[Client-side]__ You will be directed to http://52.8.5.83/make_request. The two selection boxes are default to `GET` and `api/me`. Click "Make API call''. The expected results should be:

   ```json
   {
     "id": 1,
     "message": "Hello World!",
     "username": "luoxim"
   }
   E2E Latency: ??? milliseconds
   ```

   



