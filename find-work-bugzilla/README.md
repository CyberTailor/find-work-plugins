<!-- SPDX-FileCopyrightText: 2024 Anna <cyber@sysrq.in> -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

find-work-bugzilla
==================

[find-work][find-work] is a utility for Gentoo repository maintainers that
helps them find ebuilds to improve.

This plugin adds commands that use [Gentoo Bugzilla][bugzilla] to find work.

[find-work]: https://find-work.sysrq.in/
[bugzilla]: https://bugs.gentoo.org/


Installing
----------

### Gentoo

```sh
eselect repository enable guru
emaint sync -r guru
emerge dev-util/find-work-bugzilla
```

### Other systems

`pip install find-work-bugzilla --user`


Packaging
---------

You can track new releases using an [atom feed][atom] provided by PyPI.

[atom]: https://pypi.org/rss/project/find-work-bugzilla/releases.xml


Contributing
------------

Patches and pull requests are welcome. Please use either [git-send-email(1)][1]
or [git-request-pull(1)][2], addressed to <cyber@sysrq.in>.

If you prefer GitHub-style workflow, use the [mirror repo][gh] to send pull
requests.

Your commit message should conform to the following standard:

```
file/changed: Concice and complete statement of the purpose

This is the body of the commit message.  The line above is the
summary.  The summary should be no more than 72 chars long.  The
body can be more freely formatted, but make it look nice.  Make
sure to reference any bug reports and other contributors.  Make
sure the correct authorship appears.
```

[1]: https://git-send-email.io/
[2]: https://git-scm.com/docs/git-request-pull
[gh]: http://github.com/cybertailor/find-work-plugins


IRC
---

You can join the `#find-work` channel either on [Libera Chat][libera] or
[via Matrix][matrix].

[libera]: https://libera.chat/
[matrix]: https://matrix.to/#/#find-work:sysrq.in


License
-------

WTFPL
