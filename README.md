This is a Dockerfile sanity and semantics checker. It will give hints based on best practices. 

The upstream project is at https://github.com/goern/dockerfile_checker

TODO
====

* DONE: check is a ssh rpm gets installed => no good

* check if ENTRYPOINT or CMD is present

* check if a wrapper script is used for ENTRYPOINT or CMD
 - wrapper should use exec, but we dont have the wrapper, just the Dockerfile

* check if a user is created within the Dockerfile
 
* DONE: check if ports got EXPOSEd

* DONE: check is USER <otherthanroot> is used

