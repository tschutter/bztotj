#!/usr/bin/env python3

"""
Export Bugzilla bugs to a TaskJuggler project.

Tested with Bugzilla-3.6.2 and TaskJuggler-3.1.0.
"""

import argparse
import sys

try:
    import mysql.connector
except Exception:
    print("Unable to import mysql.connector", file=sys.stderr)
    print("Get from https://launchpad.net/myconnpy/", file=sys.stderr)
    sys.exit(1)

# Configuration variables
FLAGS_FILENAME = "bugzilla_flags.tji"
PROJECT_FILENAME = "bugzilla_project.tji"
PRIORITY_DICTIONARY = {
    "P1": "900",
    "P2": "700",
    "P3": "500",
    "P4": "300",
    "P5": "100"
}
# End of configuration variables


def write_flags_file():
    """Write include file with flags."""
    with open(FLAGS_FILENAME, "w") as outfile:
        # Write header
        outfile.write("# Written by %s\n" % __file__)
        outfile.write(
            "# Should be included at main level after the project section\n"
        )

        # Write flags
        outfile.write("flags flagIsEnhancement\n")
        outfile.write("flags flagIsResolved\n")
        outfile.write("flags flagEstimateNeeded\n")
        outfile.write("flags flagPriorityNeeded\n")


def write_project_data():
    """Write project include file."""
    with open(PROJECT_FILENAME, "w") as outfile:
        # Write header
        outfile.write("# Written by bztotj.py\n")
        outfile.write("# Should be included inside the project section\n")

        # Write each task extension to the file.
        outfile.write(
            "extend task {\n"
            "  text BugID \"BugID\"\n"
            "}\n"
            "extend task {\n"
            "  text BugURL \"BugURL\"\n"
            "}\n"
            "extend task {\n"
            "  reference BugRef \"BugRef\"\n"
            "}\n"
            "extend task {\n"
            "  text Priority \"Priority\"\n"
            "}\n"
            "extend task {\n"
            "  text Product \"Product\"\n"
            "}\n"
            "extend task {\n"
            "  text Severity \"Severity\"\n"
            "}\n"
            "extend task {\n"
            "  text Keywords \"Keywords\"\n"
            "}\n"
            "extend task {\n"
            "  text AssignedTo \"AssignedTo\"\n"
            "}\n"
        )


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
            task.task_list,
            bug_id,
            new_current_name
        )
        if relative_name != "":
            return relative_name
    return ""


class TaskjugglerTask(object):
    """A TaskJuggler task."""
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

    def write(self, args, outfile, root_list, nesting_level):
        """Write task to outfile."""
        indent = "  " * nesting_level
        bugurl = "%sshow_bug.cgi?id=%i" % (args.baseurl, self.bug_id)
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


def build_resolved_bug_task_list(args, db_connection, milestone):
    """Build a list of resolved bugs."""
    task_list = []

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

    cursor = db_connection.cursor()
    cursor.execute(sql)
    for row in cursor.fetchall():
        # Get the values from the record
        bug_id = row[0]
        bz_priority = row[1]
        bz_product = row[2]
        bz_severity = row[3]
        bz_keywords = row[4]
        bz_assigned_to = str(row[5])
        # timestamp must be aligned to timingresolution (1h)
        timestamp = row[6]
        timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
        fixed_timestamp = timestamp.isoformat("-")
        summary = row[7]

        flag_estimate_needed = False
        flag_priority_needed = False
        is_meta = False
        if summary.startswith(args.meta_prefix):
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

    cursor.close()

    return task_list


def build_open_bug_task_list(args, db_connection, milestone):
    """Build a list of open bugs."""
    task_list = []

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

    cursor = db_connection.cursor()
    cursor.execute(sql)
    for row in cursor.fetchall():
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
        if summary.startswith(args.meta_prefix):
            summary = summary[len(args.meta_prefix):]
            is_meta = True

        # Translate Bugzilla values to TaskJuggler values
        name = summary.replace('"', "'")
        resource = bz_assigned_to.split("@")[0].replace(".", "")
        if bz_priority == args.not_prioritized:
            flag_priority_needed = True
        priority = PRIORITY_DICTIONARY.get(bz_priority, "100")
        fixed_timestamp = ""
        if remaining_time > 0.0:
            effort = str(remaining_time) + "h"
        elif estimated_time > 0.0:
            effort = str(estimated_time) + "h"
        else:
            effort = args.default_effort
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

    cursor.close()

    # Process bug dependencies
    sql = "SELECT dependson FROM dependencies WHERE blocked="
    task_list_copy = task_list[:]
    for task in task_list_copy:
        cursor = db_connection.cursor()
        cursor.execute(sql + str(task.bug_id))
        for row in cursor.fetchall():
            dependson = row[0]

            if (task.is_meta):
                # print("META: %i<-%s" % (task.bug_id, str(dependson)))
                for blocked_task in task_list:
                    if blocked_task.bug_id == dependson:
                        task.task_list.append(blocked_task)
                        task_list.remove(blocked_task)
                        break
            else:
                task.depends.append(dependson)
        cursor.close()

    return task_list


def write_task_list(args, task_list, filename):
    """Write a task list to a file."""
    with open(filename, "w") as outfile:
        for task in task_list:
            task.write(args, outfile, task_list, 0)


def export(args, db_connection):
    """Read from the Bugzilla database and export to the .tji file."""
    for milestone in args.milestones:
        # Build a task list of resolved bugs from the Bugzilla database
        task_list = build_resolved_bug_task_list(
            args,
            db_connection,
            milestone
        )

        # Write the task list to the output file
        write_task_list(args, task_list, milestone + "_resolved_tasks.tji")

        # Build a task list of open bugs from the Bugzilla database
        task_list = build_open_bug_task_list(args, db_connection, milestone)

        # Write the task list to the output file
        write_task_list(args, task_list, milestone + "_open_tasks.tji")


def main():
    """main"""
    arg_parser = argparse.ArgumentParser(
        description=(
            "Exports Bugzilla bugs to a TaskJuggler project. "
            "See /etc/bugzilla3/localconfig for --db-* values."
        )
    )
    arg_parser.add_argument(
        "--meta-prefix",
        action="store",
        dest="meta_prefix",
        metavar="STR",
        default="META: ",
        help="name prefix for meta bugs (default=%(default)s)"
    )
    # see https://bugzilla.mozilla.org/show_bug.cgi?id=49862
    arg_parser.add_argument(
        "--not-prioritized",
        action="store",
        dest="not_prioritized",
        metavar="PRIORITY",
        default="P5",
        help="Bugzilla priority of non-prioritized bugs (default=%(default)s)"
    )
    arg_parser.add_argument(
        "--default-effort",
        action="store",
        dest="default_effort",
        metavar="STR",
        default="16.0h",
        help="effort to use if bug has no effort assigned (default=%(default)s)"
    )
    arg_parser.add_argument(
        "--db-host",
        action="store",
        dest="db_host",
        metavar="HOST",
        default="localhost",
        help="Bugzilla database hostname (default=%(default)s)"
    )
    arg_parser.add_argument(
        "--db-port",
        action="store",
        type="int",
        dest="db_port",
        metavar="PORT",
        default=3306,
        help="Bugzilla database port (default=%(default)i)"
    )
    arg_parser.add_argument(
        "--db-name",
        action="store",
        dest="db_name",
        metavar="NAME",
        default="bugzilla3",
        help="Bugzilla database name (default=%(default)s)"
    )
    arg_parser.add_argument(
        "--db-user",
        action="store",
        dest="db_user",
        metavar="NAME",
        default="bugzilla3",
        help="Bugzilla database user (default=%(default)s)"
    )
    arg_parser.add_argument(
        "--db-pass",
        action="store",
        dest="db_pass",
        metavar="PASSWORD",
        default=None,
        help="Bugzilla database password (default=%(default)s)"
    )
    arg_parser.add_argument(
        "--baseurl",
        action="store",
        dest="baseurl",
        metavar="URL",
        default="http://bugzilla.monticello.com/",
        help="Bugzilla base URL (default=%(default)s)"
    )
    arg_parser.add_argument(
        "milestones",
        metavar="milestone",
        nargs="+",
        help="Bugzilla milestone"
    )
    args = arg_parser.parse_args()

    # Connect to the Bugzilla database
    try:
        db_connection = mysql.connector.connect(
            host=args.db_host,
            port=args.db_port,
            user=args.db_user,
            passwd=args.db_pass,
            db=args.db_name
        )
    except Exception as exc:
        print("Error connecting to database: %s" % exc, file=sys.stderr)
        return 1

    try:
        # Export from the database.
        export(args, db_connection)
    finally:
        # Close the connection to the Bugzilla database
        db_connection.close()

    # Write the flags data file.
    write_flags_file()

    # Write the project data file.
    write_project_data()

    return 0


if __name__ == "__main__":
    sys.exit(main())
