Contribute to Unknown Horizons!
===============================

We have lots of opportunities besides hacking code:
Check our page on how to [Get Involved] (http://www.unknown-horizons.org/get-involved/)!

Checklist for contributing code
-------------------------------
* Our repository hoster, bug tracker and otherwise awesome development platform is GitHub.
  [Sign up] (https://github.com/signup/free) if you have no account yet to get started!
* Find something you want to improve or fix
* Check whether our [bug tracker] (https://github.com/unknown-horizons/unknown-horizons/issues)
  contains a ticket for this particular something
* If not, you can either open it or (for smaller fixes) submit a pull request describing the issue
* [Fork us] (https://github.com/unknown-horizons/unknown-horizons) and start working in a topic branch for the fork
* Make sure to check the *Coding style* and *Pull requests* sections below

Coding style
------------
We closely follow [PEP-8] (http://www.python.org/dev/peps/pep-0008/).
Things that are handled differently:
* **Tabs** only, no spaces for indentation
* We do not strictly enforce a **line length** of 79 characters, usually our code stays at around 90 columns per line
* **String formatting** should prefer the [Python3-style `format()`]
  (http://svn.python.org/view/sandbox/trunk/pep3101/doctests/basic_examples.txt?revision=54966&view=markup)
  over the `%` operator

Pull requests
-------------
Commit in small, logical sections instead of assembling one huge patch. Use the power of pull requests :)

The commit messages in your pull request should follow these common guidelines:
* First line is a short summary, followed by a blank line and a more detailed description
* If you are referring to a bug in our tracker, the short summary should should contain that issue number: `#1322`
* Remember to explain why you do something and why you chose a certain way of doing it!
* Wrap the commit message at 72 chars per line. If your summary is longer than that, it is no summary!


More resources
==============

IRC
---
Our developers are available on IRC for all your questions:
**#unknown-horizons** @ irc.freenode.net
or via [webchat](http://www.unknown-horizons.org/support/irc/).

In-code tutorial
----------------
We wrote an **in-code tutorial** to give you a code architecture overview before you start coding on Unknown Horizons.
You find the first tutorial in [`run_uh.py`] (https://github.com/unknown-horizons/unknown-horizons/blob/master/run_uh.py).
Starting there, just follow the instruction comments (and ask us if something is unclear or outdated!).

Epydoc
------
We are pretty good at standing our ground against documentation, but here you go:
[Epydoc] (http://epydoc.unknown-horizons.org/).
We recommend you check the in-code tutorial first however :)

A better example is [FIFE epydoc] (http://www.fifengine.net/epydoc) which helps understanding the engine glue.

Tests
-----
* [Wiki overview page] (http://wiki.unknown-horizons.org/w/Tests)
* [Writing GUI tests] (http://wiki.unknown-horizons.org/w/Writing_GUI_tests)

Github help
-----------
* [General GitHub documentation] (http://help.github.com/)
* [GitHub pull request documentation] (http://help.github.com/send-pull-requests/)
