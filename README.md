This is a Dockerfile sanity and semantics checker. It provides hints based on best practices.

Currently output is json to be displayed by web front-end.

The rules used to validate the Dockerfile are defined by a yaml file. To customize the ruleset copy the dockerfile_rules.yaml, edit the file and pass the `--rules` argument to specify the custom dockerfile ruleset.

## Running

`./check_dockerfile.py <path/to/Dockerfile> [--rules <path/to/custom/rules.yaml>]`

## TODO

* DONE: check is a ssh rpm gets installed => no good

* DONE: check if ENTRYPOINT or CMD is present

* check if a wrapper script is used for ENTRYPOINT or CMD
 - wrapper should use exec, but we dont have the wrapper, just the Dockerfile

* check if a user is created within the Dockerfile

* DONE: check if ports got EXPOSEd

* DONE: check is USER <otherthanroot> is used

