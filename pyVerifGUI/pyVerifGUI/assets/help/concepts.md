# Core Concepts

## Configurations

A configuration is simply a YAML file that describes customizations and settings
required to open a given RTL project. There should be one configuration file
per project.

## Builds

A build is a "unit" of a project. This translates into a directory underneath the working directory specified in your configuration. This can be used, for
example, to quantify changes between branches or builds of your project.

In the build directory, you'll find parser outputs and saved linter messages.

## Linter Messages

These are the `Error` or `Warning` messages given by Verilator when running
linting, and are linked to a file, line number, and position.

## Waivers

Waivers are structures that can waive linter messages. Usually an explanation
will be attached to them. This allows you to explicitly state that a given
warning does not apply or is not important to the application, and discern
legitimate messages from spurious linter messages.

## Orphaned waivers

The GUI will track old waivers, as well as new ones that are generated. When the
existing waivers do not match with new messages exactly (i.e. the line number
changed after an edit), these are called orphaned waivers. There is built in
functionality to match these orphans against existing waivers to ensure the
changes are valid.
