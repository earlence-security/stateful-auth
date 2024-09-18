# StatefulAuth
### Stateful Least Privilege Authorization for the Cloud
---

StatefulAuth is an authorization library built on top of [Authlib](https://authlib.org/) that enables (1) a client app developer (and their security team) to express the minimum privilege they need and (2) the service developer to enforce these requirements.

## Repository Organization

```
stateful-auth/
├── auth-lib/      # StatefulAuth Python library
├── historylib/    # History library of StatefulAuth
├── server/        # Server-side integration example
├── client/        # Client-side integration example
├── proxy/         # Helper module that integrates StatefulAuth with real apps
├── examples/      # Real app examples
├── scripts/       # Evaluation and analysis scripts
└── utils/         # Util modules
```

## Get Started

- For USENIX Security '24 Artifact Evaluation, please refer to our Artifact Appendix PDF. 
- For quick installation on your local machine, please refer to our [Installation](https://github.com/earlence-security/stateful-auth/tree/eval/docs/installation.md) doc.
- For setting StatefulAuth on AWS, please refer to our [Setup on AWS](https://github.com/earlence-security/stateful-auth/tree/eval/docs/setup_aws.md) doc.

## Contact

Luoxi Meng (lumeng@ucsd.edu)

Leo Cao (z2cao@ucsd.edu)
