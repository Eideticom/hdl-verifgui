# Linting

Linting is done using Verilator, which must be installed for linting to succeed.

Verilator outputs messages, which can either be Warnings or Errors, depending
on the severity of the syntax issue. These messages are displayed in the
Linter tab, where you can click on messages to see more information about
them, and open the file in an editor. The file always gets opened in a
read-only editor tab, which shows the file and highlights the line the
message relates to. By clicking "Open" you can open the file in a proper
editing tab, which allows you to edit and save the file directly in the GUI.

## Waivers

The main feature of the Linter tab is waivers. These allow you to mark
messages that you believe are not valid for your module, while assigning a
name and a reason to that waiver. By doing this you can whittle down
extraneous linting messages and leave only the messages that could flag
actual bugs. Messages that have been reviewd - but not waived - can be marked as
such by right-clicking on them, and selecting "Toggle Reviewed".

On the top right of the box with the waivers there is a set of radio buttons.
These allow you to filter the messages you see, and view different sets of
messages.

## Diff View

This view allows you to see the differences in messages and waivers between
different builds.
