bztotj
======

Export Bugzilla bugs to a TaskJuggler project.

Usage
-----
::

    bztotj.py MILESTONE [MILESTONE...]

Bugzilla Assumptions
--------------------

This script makes some assumptions regarding your Bugzilla installation.

#. Grouping bugs all have a common description prefix.  The default prefix is "META: ".  Bugs that are part of a group are made into subtasks of that group.

#. Not all bugs will have an time estimate.  Those bugs are flagged and assigned a default effort.

#. The set of priority values is ["P1", "P2", "P3", "P4", "P5"].

#. The lowest bug priority of "P5" means that the bug is not prioritized.  Those bugs are flagged.

To Do
-----

* Update to current Bugzilla schema.

* Update to current TaskJuggler syntax.
