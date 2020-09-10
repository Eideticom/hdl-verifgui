# Managing Orphans

When a linter or coverage waiver exists, but can't be matched up to a
linter/coverage message, it is considered an orphan. This can happen because
you changed the contents of a line, or if you inserted or deleted a line
beforehand, shifting the location of the line the waiver applies to.

Instead of having to manually edit this waiver, an extra filter shows up,
circled in red, called orphaned waivers. This allows you to see all orphaned
waivers in one place, and opens up a new tab to the right, called "Orphan
Management". When you click on an orphaned waiver, this tab will display a
list of all the messages from the same file. You can right click on these to
see the options available.

"Update Orphan" will match the currently selected orphan waiver to the
message, and remove the waiver from the orphans list. This is what you use to
actually fix these. "Open in editor" shows the line in the editor tab, so you
can see the context of the issue, and match lines to waivers.
