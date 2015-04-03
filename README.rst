bztotj
======

Export Bugzilla bugs to a TaskJuggler project.

Usage
-----

Export bugs to a TaskJuggler include file::

    bztotj.py MILESTONE [MILESTONE...]

This creates the files "bugzilla_flags.tji", "bugzilla_project.tji",
"MILESTONE_resolved_tasks.tji", and "MILESTONE_open_tasks.tji".
Import them as shown in the example project "bzexample.tjp"::

    project bzexample "Example" "1.0" 2012-05-01 2012-06-01 {
      include "bugzilla_project.tji"
    }

    # Flag declarations.
    include "bugzilla_flags.tji"

    # Resource definitions.
    # Define Bugzilla users here.
    resource tjefferson "Thomas Jefferson" { }

    # Include the tasks exported from Bugzilla
    task resolved_tasks "Resolved Tasks" { }
    include "bzexample_resolved_tasks.tji" { taskprefix resolved_tasks }
    task open_tasks "Open Tasks" {
      start 2012-05-01
    }
    include "bzexample_open_tasks.tji" { taskprefix open_tasks }

    # Charts
    ...


Bugzilla Assumptions
--------------------

This script makes some assumptions regarding your Bugzilla installation.

#. The database is MySQL.

#. Grouping bugs all have a common description prefix.  The default prefix is "META: ".  Bugs that are part of a group are made into subtasks of that group.

#. Not all bugs will have an time estimate.  Those bugs are flagged and assigned a default effort.

#. The set of priority values is ["P1", "P2", "P3", "P4", "P5"].

#. The lowest bug priority of "P5" means that the bug is not prioritized.  Those bugs are flagged.
