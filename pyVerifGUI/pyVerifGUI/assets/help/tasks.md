# Running Tasks

In the "Overview" tab, you will see a list of tasks. Each of these represents
some unit of work that the GUI can do. Tasks can depend on each other (for
future features anyways), so running a task with dependancies will run all of
its requirements.

Tasks will be in one of three states:
- Unfinished
- Running
- Finished (failed or passed)

On opening a new build, tasks start as unfinished, and begin Running when the
button next to their name is clicked.

Once running, tasks can be killed, which will place them back in the
Unfinished state.

Once finished, regardless of if it passed or failed, a task can be
temporarily reset to Unfinished, in order to run it again.
