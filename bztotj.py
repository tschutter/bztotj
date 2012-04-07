#!/usr/bin/env python

"""

Export Bugzilla bugs to a TaskJuggler project.

This script relies on the following packages to be installed:
  python
  python-mysqldb

Copyright (c) 2006-2012 Tom Schutter
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

   - Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
   - Redistributions in binary form must reproduce the above
     copyright notice, this list of conditions and the following
     disclaimer in the documentation and/or other materials provided
     with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""


# Configuration variables
FLAGS_FILENAME = "bugzilla_flags.tji"
PROJECT_FILENAME = "bugzilla_project.tji"
META_TAG = "META: "
UN_PRIORITIZED = "P5"  # see https://bugzilla.mozilla.org/show_bug.cgi?id=49862
PRIORITY_DICTIONARY = {
   "P1": "900",
   "P2": "700",
   "P3": "500",
   "P4": "300",
   "P5": "100"
}
DEFAULT_EFFORT = "16.0h"

DB_SCHEME = "mysql"           # what type of database?

# Values from /etc/bugzilla/localconfig
DB_HOST = "bugzilla.bou.platte.com"  # where is the database?
DB_PORT = 3306                # which port to use
DB_NAME = "bugzilla"          # name of the MySQL database
DB_USER = "bugzilla"          # user to attach to the MySQL database
DB_PASS = "jayzilla"          # password for DB_USER

URLBASE = "http://bugzilla.bou.platte.com:8080/"

# End of configuration variables

# The preferred database package is adodb, but debian-3.1 does not
# have python-adodb.
# from adodb import adodb
import MySQLdb
import sys


def write_flags_file():
    """Write include file with flags."""
    # Open the output file
    outfile = open(FLAGS_FILENAME, "w")

    # Write header
    outfile.write("# Written by bztotj.py\n")
    outfile.write(
        "# Should be included at main level after the project section\n"
    )

    # Write flags
    outfile.write("flags flagIsEnhancement\n")
    outfile.write("flags flagIsResolved\n")
    outfile.write("flags flagEstimateNeeded\n")
    outfile.write("flags flagPriorityNeeded\n")

    # Close the output file
    outfile.close()


def write_project_data():
    """Write project include file."""
    # Open the output file
    outfile = open(PROJECT_FILENAME, "w")

    # Write header
    outfile.write("# Written by bztotj.py\n")
    outfile.write("# Should be included inside the project section\n")

    # Write each task extensions to the file
    outfile.write(
        "extend task {\n"
        "  text BugID \"BugID\"\n"
        "}\n"
    )
    outfile.write(
        "extend task {\n"
        "  text BugURL \"BugURL\"\n"
        "}\n"
    )
    outfile.write(
        "extend task {\n"
        "  reference BugRef \"BugRef\"\n"
        "}\n"
    )
    outfile.write(
        "extend task {\n"
        "  text Priority \"Priority\"\n"
        "}\n"
    )
    outfile.write(
        "extend task {\n"
        "  text Product \"Product\"\n"
        "}\n"
    )
    outfile.write(
        "extend task {\n"
        "  text Severity \"Severity\"\n"
        "}\n"
    )
    outfile.write(
        "extend task {\n"
        "  text Keywords \"Keywords\"\n"
        "}\n"
    )
    outfile.write(
        "extend task {\n"
        "  text AssignedTo \"AssignedTo\"\n"
        "}\n"
    )

    # Close the output file
    outfile.close()


def get_relative_name(task_list, bug_id, current_name):
    """Convert a name to a relative name."""
    for task in task_list:
        if current_name.endswith("!"):
            new_current_name = "%sbug_%i" % (current_name, task.bug_id)
        else:
            new_current_name = "%s.bug_%i" % (current_name, task.bug_id)
        if task.bug_id == bug_id:
            return new_current_name
        relative_name = get_relative_name(
            task.taskList,
            bug_id,
            new_current_name
        )
        if relative_name != "":
            return relative_name
    return ""


class TaskjugglerTask(object):
    """A TaskJuggler task"""
    def __init__(
        self,
        milestone,
        bug_id,
        name,
        bz_priority,
        bz_product,
        bz_severity,
        bz_keywords,
        bz_assigned_to,
        resource,
        priority,
        fixed_timestamp,
        effort,
        is_meta,
        flag_estimate_needed,
        flag_priority_needed
    ):
        self.milestone = milestone
        self.bug_id = bug_id
        self.name = name
        self.bz_priority = bz_priority
        self.bz_product = bz_product
        self.bz_severity = bz_severity
        self.bz_keywords = bz_keywords
        self.bz_assigned_to = bz_assigned_to
        self.resource = resource
        self.priority = priority
        self.fixed_timestamp = fixed_timestamp
        self.effort = effort
        self.is_meta = is_meta
        self.flag_estimate_needed = flag_estimate_needed
        self.flag_priority_needed = flag_priority_needed
        self.task_list = []
        self.depends = []

    def write(self, outfile, root_list, nesting_level):
        """Write task to outfile."""
        indent = "  " * nesting_level
        bugurl = "%sshow_bug.cgi?id=%i" % (URLBASE, self.bug_id)
        outfile.write(
            indent + "task bug_%i \"%s\" {\n" % (self.bug_id, self.name) +
            indent + "  BugID \"%i\"\n" % self.bug_id +
            indent + "  BugURL \"%s\"\n" % bugurl +
            indent + "  BugRef \"%s\" {\n" % bugurl +
            indent + "    label \"%i\"\n" % self.bug_id +
            indent + "  }\n"
        )

        # Write dependencies
        if self.fixed_timestamp == "":
            args = ""
            for depend in self.depends:
                relative_name = get_relative_name(
                    root_list,
                    depend,
                     "!" * (nesting_level + 1)
                )
                if len(relative_name) == 0:
                    continue
                if len(args) > 0:
                    args += ","
                args += relative_name
            if len(args) > 0:
                outfile.write(indent + "  depends " + args + "\n")
            exit

        if self.is_meta:
            if len(self.task_list) == 0:
                print(
                    "bztotj.py: META bug %i has no open" % self.bug_id +
                    " dependencies in milestone \"%s\"" % self.milestone
                )
            for task in self.task_list:
                task.write(outfile, root_list, nesting_level + 1)
        else:
            outfile.write(
                indent + "  Priority \"" + self.bz_priority + "\"\n" +
                indent + "  Product \"" + self.bz_product + "\"\n" +
                indent + "  Severity \"" + self.bz_severity + "\"\n" +
                indent + "  Keywords \"" + self.bz_keywords + "\"\n" +
                indent + "  AssignedTo \"" + self.bz_assigned_to + "\"\n"
            )
            if self.fixed_timestamp != "":
                outfile.write(
                    indent + "  milestone\n" +
                    indent + "  flags flagIsResolved\n" +
                    indent + "  end " + self.fixed_timestamp + "\n"
                )
            else:
                outfile.write(
                    indent + "  allocate " + self.resource + "\n" +
                    indent + "  effort " + self.effort + "\n" +
                    indent + "  priority " + self.priority + "\n"
                )
            if self.bz_severity == "enhancement":
                outfile.write(indent + "  flags flagIsEnhancement\n")
            if self.flag_estimate_needed:
                outfile.write(indent + "  flags flagEstimateNeeded\n")
            if self.flag_priority_needed:
                outfile.write(indent + "  flags flagPriorityNeeded\n")
        outfile.write(indent + "}\n")


def build_resolved_bug_task_list(milestone):
    """Build a list of resolved bugs."""
    task_list = []

    # Connect to the Bugzilla database
    #connection = adodb.NewADOConnection(DB_SCHEME)
    #connection.Connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    connection = MySQLdb.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        passwd=DB_PASS,
        db=DB_NAME
    )

    # Process resolved bugs -> milestones
    columns = "bugs.bug_id,bugs.priority,products.name,bugs.bug_severity," +\
        "bugs.keywords,profiles.login_name,MAX(bugs_activity.bug_when)," +\
        "bugs.short_desc"
    from_clause = " FROM bugs,products,profiles,bugs_activity"
    where = " WHERE"
    where += " bugs.product_id = products.id"
    where += " AND bugs.assigned_to = profiles.userid"
    where += " AND bugs.bug_id = bugs_activity.bug_id"
    where += " AND bugs.target_milestone='" + milestone + "'"
    where += " AND bugs_activity.added='RESOLVED'"
    where += " AND (bugs.bug_status='RESOLVED' OR bugs.bug_status='VERIFIED')"
    where += " AND (bugs.resolution<>'INVALID')"
    where += " AND (bugs.resolution<>'DUPLICATE')"
    group = " GROUP BY bugs.bug_id,bugs_activity.added"
    sql = "SELECT " + columns + from_clause + where + group

    #rows = connection.Execute(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        # Get the values from the record
        bug_id = row[0]
        bz_priority = row[1]
        bz_product = row[2]
        bz_severity = row[3]
        bz_keywords = row[4]
        bz_assigned_to = str(row[5])
        fixed_timestamp = row[6].isoformat("-")
        summary = row[7]

        flag_estimate_needed = False
        flag_priority_needed = False
        is_meta = False
        if summary.startswith(META_TAG):
            continue

        # Translate Bugzilla values to TaskJuggler values
        name = summary.replace('"', "'")
        resource = bz_assigned_to.split("@")[0].replace(".", "")
        priority = PRIORITY_DICTIONARY.get(bz_priority, "100")
        effort = ""

        # Optional, simplify the Bugzilla assigned to
        bz_assigned_to = bz_assigned_to.split("@")[0].replace(".", "")

        task_list.append(
            TaskjugglerTask(
                milestone,
                bug_id,
                name,
                bz_priority,
                bz_product,
                bz_severity,
                bz_keywords,
                bz_assigned_to,
                resource,
                priority,
                fixed_timestamp,
                effort,
                is_meta,
                flag_estimate_needed,
                flag_priority_needed
            )
        )

    #cursor.Close()
    cursor.close()

    # Close the connection to the Bugzilla database
    #connection.Close()
    connection.close()

    return task_list


def build_open_bug_task_list(milestone):
    """Build a list of open bugs."""
    task_list = []

    # Connect to the Bugzilla database
    #connection = adodb.NewADOConnection(DB_SCHEME)
    #connection.Connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    connection = MySQLdb.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        passwd=DB_PASS,
        db=DB_NAME
    )

    columns = "bugs.bug_id,bugs.priority,products.name,bugs.bug_severity," +\
        "bugs.keywords,profiles.login_name,bugs.estimated_time," +\
        "bugs.remaining_time,bugs.short_desc"
    from_clause = " FROM bugs,products,profiles"
    where = " WHERE"
    where += " bugs.product_id = products.id"
    where += " AND bugs.assigned_to = profiles.userid"
    where += " AND target_milestone='%s'" % milestone
    where += " AND (bug_status='UNCONFIRMED'"
    where += " OR bug_status='NEW'"
    where += " OR bug_status='ASSIGNED'"
    where += " OR bug_status='REOPENED')"
    sql = "SELECT " + columns + from_clause + where

    #rows = connection.Execute(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        # Get the values from the record
        bug_id = row[0]
        bz_priority = row[1]
        bz_product = row[2]
        bz_severity = row[3]
        bz_keywords = row[4]
        bz_assigned_to = str(row[5])
        estimated_time = float(row[6])
        remaining_time = float(row[7])
        summary = row[8]

        flag_estimate_needed = False
        flag_priority_needed = False
        is_meta = False
        if summary.startswith(META_TAG):
            summary = summary[len(META_TAG):]
            is_meta = True

        # Translate Bugzilla values to TaskJuggler values
        name = summary.replace('"', "'")
        resource = bz_assigned_to.split("@")[0].replace(".", "")
        if bz_priority == UN_PRIORITIZED:
            flag_priority_needed = True
        priority = PRIORITY_DICTIONARY.get(bz_priority, "100")
        fixed_timestamp = ""
        if remaining_time > 0.0:
            effort = str(remaining_time) + "h"
        elif estimated_time > 0.0:
            effort = str(estimated_time) + "h"
        else:
            effort = DEFAULT_EFFORT
            flag_estimate_needed = True

        # Optional, simplify the Bugzilla assigned to
        bz_assigned_to = bz_assigned_to.split("@")[0].replace(".", "")

        task_list.append(
            TaskjugglerTask(
                milestone,
                bug_id,
                name,
                bz_priority,
                bz_product,
                bz_severity,
                bz_keywords,
                bz_assigned_to,
                resource,
                priority,
                fixed_timestamp,
                effort,
                is_meta,
                flag_estimate_needed,
                flag_priority_needed
            )
        )

    #cursor.Close()
    cursor.close()

    # Process bug dependencies
    sql = "SELECT dependson FROM dependencies WHERE blocked="
    task_list_copy = task_list[:]
    for task in task_list_copy:
        #rows = connection.Execute(sql + str(task.bug_id))
        cursor = connection.cursor()
        cursor.execute(sql + str(task.bug_id))
        rows = cursor.fetchall()
        for row in rows:
            dependson = row[0]

            if (task.is_meta):
                #print "META: %i<-%s" % (task.bug_id, str(dependson))
                for blocked_task in task_list:
                    if blocked_task.bug_id == dependson:
                        task.task_list.append(blocked_task)
                        task_list.remove(blocked_task)
                        break
            else:
                task.depends.append(dependson)
        #cursor.Close()
        cursor.close()

    # Close the connection to the Bugzilla database
    #connection.Close()
    connection.close()

    return task_list


def write_task_list(task_list, filename):
    """Write a task list to a file."""
    # Open the output file
    outfile = open(filename, "w")

    # Write each task to the file
    for task in task_list:
        task.write(outfile, task_list, 0)

    # Close the output file
    outfile.close()


def main():
    """main"""

    # Process arguments
    if len(sys.argv) < 2:
        print "ERROR: No milestone specified."
        print "USAGE: " + sys.argv[0] + " MILESTONE [MILESTONE...]"
        sys.exit()

    # Write the flags data file
    write_flags_file()

    # Write the project data file
    write_project_data()

    for milestone in sys.argv[1:]:
        # Build a task list of resolved bugs from the Bugzilla database
        task_list = build_resolved_bug_task_list(milestone)

        # Write the task list to the output file
        write_task_list(task_list, milestone + "_resolved_tasks.tji")

        # Build a task list of open bugs from the Bugzilla database
        task_list = build_open_bug_task_list(milestone)

        # Write the task list to the output file
        write_task_list(task_list, milestone + "_open_tasks.tji")


if __name__ == "__main__":
    sys.exit(main())
