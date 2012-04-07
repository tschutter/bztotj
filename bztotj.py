#!/usr/bin/python
# $Id: bztotj.py,v 1.29 2008-01-04 15:48:46 tom Exp $
#
# Script to export TaskJuggler tasks from Bugzilla.
#
# This script relies on the following packages to be installed:
#   python
#   python-mysqldb
#
# Copyright (c) 2006-2008 Tom Schutter
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    - Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    - Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# ChangeLog
#
#   2006-03-28 Tom Schutter (1.16)
#     Initial release.
#
#   2006-07-06 Tom Schutter (1.19)
#     Extract keywords from Bugzilla.
#     Added comment to unPrioritized setting.
#     Tabs to spaces.
#
#   2007-10-11 Tom Schutter (1.22)
#     Fixed int vs float test problem introduced by Python 2.4.
#     Now handles remaining_time from Bugzilla.
#     Added ChangeLog.
#
#   2007-10-31 Tom Schutter (1.27)
#     Renamed BugID as BugRef, which is a taskjuggler "reference" to the bug.
#     Output BugID which is just the bug number.
#     Output BugURL which is just the bug URL.
#
#   2007-11-01 Tom Schutter (1.28)
#     Stripping of email suffix is now more robust.
#
#   2008-01-04 Tom Schutter (1.29)
#     Strip "." from Bugzilla AssignedTo to make resource id

# Configuration variables
flagsFilename = "bugzilla_flags.tji"
projectFilename = "bugzilla_project.tji"
metaTag = "META: "
unPrioritized = "P5" # see https://bugzilla.mozilla.org/show_bug.cgi?id=49862
priorityDictionary = {
   "P1": "900",
   "P2": "700",
   "P3": "500",
   "P4": "300",
   "P5": "100"
}
defaultEffort = "16.0h"

db_scheme = "mysql"           # what type of database?

# Values from /etc/bugzilla/localconfig
db_host = "bugzilla.bou.platte.com" # where is the database?
db_port = 3306                # which port to use
db_name = "bugzilla"          # name of the MySQL database
db_user = "bugzilla"          # user to attach to the MySQL database
db_pass = "jayzilla"          # password for db_user

urlbase = "http://bugzilla.bou.platte.com:8080/"

# End of configuration variables

# The preferred database package is adodb, but debian-3.1 does not
# have python-adodb.
# from adodb import adodb
import MySQLdb
import sys

def writeFlagsFile():
    # Open the output file
    outfile = open(flagsFilename, "w")

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

def writeProjectData():
    # Open the output file
    outfile = open(projectFilename, "w")

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

def getRelativeName(taskList, bug_id, currentName):
    for task in taskList:
        if currentName.endswith("!"):
            newCurrentName = currentName + "bug_" + str(task.bug_id)
        else:
            newCurrentName = currentName + ".bug_" + str(task.bug_id)
        if task.bug_id == bug_id:
            return newCurrentName
        relativeName = getRelativeName(task.taskList, bug_id, newCurrentName)
        if relativeName != "":
            return relativeName
    return ""

class TaskjugglerTask(object):
    """A TaskJuggler task"""
    def __init__(
        self,
        bug_id,
        name,
        bzPriority,
        bzProduct,
        bzSeverity,
        bzKeywords,
        bzAssignedTo,
        resource,
        priority,
        fixedTimestamp,
        effort,
        isMeta,
        flagEstimateNeeded,
        flagPriorityNeeded
    ):
        self.bug_id = bug_id
        self.name = name
        self.bzPriority = bzPriority
        self.bzProduct = bzProduct
        self.bzSeverity = bzSeverity
        self.bzKeywords = bzKeywords
        self.bzAssignedTo = bzAssignedTo
        self.resource = resource
        self.priority = priority
        self.fixedTimestamp = fixedTimestamp
        self.effort = effort
        self.isMeta = isMeta
        self.flagEstimateNeeded = flagEstimateNeeded
        self.flagPriorityNeeded = flagPriorityNeeded
        self.taskList = []
        self.depends = []

    def write(self, outfile, rootList, nestingLevel):
        indent = "  " * nestingLevel
        bugurl = urlbase + "show_bug.cgi?id=" + str(self.bug_id)
        outfile.write(
            indent + "task bug_" + str(self.bug_id) + " \"" + self.name + "\" {\n" +
            indent + "  BugID \"" + str(self.bug_id) + "\"\n" +
            indent + "  BugURL \"" + bugurl + "\"\n" +
            indent + "  BugRef \"" + bugurl + "\" {\n" +
            indent + "    label \"" + str(self.bug_id) + "\"\n" +
            indent + "  }\n"
        )

        # Write dependencies
        if self.fixedTimestamp == "":
            args = ""
            for depend in self.depends:
                relativeName = getRelativeName(
                    rootList,
                    depend,
                     "!" * (nestingLevel + 1)
                )
                if len(relativeName) == 0:
                    continue
                if len(args) > 0:
                    args += ","
                args += relativeName
            if len(args) > 0:
                outfile.write(indent + "  depends " + args + "\n")
            exit

        if self.isMeta:
            if len(self.taskList) == 0:
                print(
                    "bztotj.py: META bug " + str(self.bug_id) +
                    " has no open dependencies in milestone \"" +
                    milestone + "\""
                )
            for task in self.taskList:
                task.write(outfile, rootList, nestingLevel + 1)
        else:
            outfile.write(
                indent + "  Priority \"" + self.bzPriority + "\"\n" +
                indent + "  Product \"" + self.bzProduct + "\"\n" +
                indent + "  Severity \"" + self.bzSeverity + "\"\n" +
                indent + "  Keywords \"" + self.bzKeywords + "\"\n" +
                indent + "  AssignedTo \"" + self.bzAssignedTo + "\"\n"
            )
            if self.fixedTimestamp != "":
                outfile.write(
                    indent + "  milestone\n" +
                    indent + "  flags flagIsResolved\n" +
                    indent + "  end " + self.fixedTimestamp + "\n"
                )
            else:
                outfile.write(
                    indent + "  allocate " + self.resource + "\n" +
                    indent + "  effort " + self.effort + "\n" +
                    indent + "  priority " + self.priority + "\n"
                )
            if self.bzSeverity == "enhancement":
                outfile.write(indent + "  flags flagIsEnhancement\n")
            if self.flagEstimateNeeded:
                outfile.write(indent + "  flags flagEstimateNeeded\n")
            if self.flagPriorityNeeded:
                outfile.write(indent + "  flags flagPriorityNeeded\n")
        outfile.write(indent + "}\n")

def buildResolvedBugTaskList():
    taskList = []

    # Connect to the Bugzilla database
    #connection = adodb.NewADOConnection(db_scheme)
    #connection.Connect(db_host, db_user, db_pass, db_name)
    connection = MySQLdb.connect(
        host = db_host,
        port = db_port,
        user = db_user,
        passwd = db_pass,
        db = db_name
    )

    # Process resolved bugs -> milestones
    columns = "bugs.bug_id,bugs.priority,products.name,bugs.bug_severity,bugs.keywords,profiles.login_name,MAX(bugs_activity.bug_when),bugs.short_desc"
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
        bzPriority = row[1]
        bzProduct = row[2]
        bzSeverity = row[3]
        bzKeywords = row[4]
        bzAssignedTo = str(row[5])
        fixedTimestamp = row[6].isoformat("-")
        summary = row[7]

        flagEstimateNeeded = False
        flagPriorityNeeded = False
        isMeta = False
        if summary.startswith(metaTag):
            continue

        # Translate Bugzilla values to TaskJuggler values
        name = summary.replace('"', "'")
        resource = bzAssignedTo.split("@")[0].replace(".", "")
        priority = priorityDictionary.get(bzPriority, "100")
        effort = ""

        # Optional, simplify the Bugzilla assigned to
        bzAssignedTo = bzAssignedTo.split("@")[0].replace(".", "")

        taskList.append(
            TaskjugglerTask(
                bug_id,
                name,
                bzPriority,
                bzProduct,
                bzSeverity,
                bzKeywords,
                bzAssignedTo,
                resource,
                priority,
                fixedTimestamp,
                effort,
                isMeta,
                flagEstimateNeeded,
                flagPriorityNeeded
            )
        )

    #cursor.Close()
    cursor.close()

    # Close the connection to the Bugzilla database
    #connection.Close()
    connection.close()

    return taskList

def buildOpenBugTaskList():
    taskList = []

    # Connect to the Bugzilla database
    #connection = adodb.NewADOConnection(db_scheme)
    #connection.Connect(db_host, db_user, db_pass, db_name)
    connection = MySQLdb.connect(
        host = db_host,
        port = db_port,
        user = db_user,
        passwd = db_pass,
        db = db_name
    )

    columns = "bugs.bug_id,bugs.priority,products.name,bugs.bug_severity,bugs.keywords,profiles.login_name,bugs.estimated_time,bugs.remaining_time,bugs.short_desc"
    from_clause = " FROM bugs,products,profiles"
    where = " WHERE"
    where += " bugs.product_id = products.id"
    where += " AND bugs.assigned_to = profiles.userid"
    where += " AND target_milestone='" + milestone + "'"
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
        bzPriority = row[1]
        bzProduct = row[2]
        bzSeverity = row[3]
        bzKeywords = row[4]
        bzAssignedTo = str(row[5])
        estimated_time = float(row[6])
        remaining_time = float(row[7])
        summary = row[8]

        flagEstimateNeeded = False
        flagPriorityNeeded = False
        isMeta = False
        if summary.startswith(metaTag):
            summary = summary[len(metaTag):]
            isMeta = True

        # Translate Bugzilla values to TaskJuggler values
        name = summary.replace('"', "'")
        resource = bzAssignedTo.split("@")[0].replace(".", "")
        if bzPriority == unPrioritized:
          flagPriorityNeeded = True
        priority = priorityDictionary.get(bzPriority, "100")
        fixedTimestamp = ""
        if remaining_time > 0.0:
          effort = str(remaining_time) + "h"
        elif estimated_time > 0.0:
          effort = str(estimated_time) + "h"
        else:
          effort = defaultEffort
          flagEstimateNeeded = True

        # Optional, simplify the Bugzilla assigned to
        bzAssignedTo = bzAssignedTo.split("@")[0].replace(".", "")

        taskList.append(
            TaskjugglerTask(
                bug_id,
                name,
                bzPriority,
                bzProduct,
                bzSeverity,
                bzKeywords,
                bzAssignedTo,
                resource,
                priority,
                fixedTimestamp,
                effort,
                isMeta,
                flagEstimateNeeded,
                flagPriorityNeeded
            )
        )

    #cursor.Close()
    cursor.close()

    # Process bug dependencies
    sql = "SELECT dependson FROM dependencies WHERE blocked="
    taskListCopy = taskList[:]
    for task in taskListCopy:
        #rows = connection.Execute(sql + str(task.bug_id))
        cursor = connection.cursor()
        cursor.execute(sql + str(task.bug_id))
        rows = cursor.fetchall()
        for row in rows:
            dependson = row[0]

            if (task.isMeta):
                #print "META: " + str(task.bug_id) + "<-" + str(dependson)
                for blockedTask in taskList:
                    if blockedTask.bug_id == dependson:
                        task.taskList.append(blockedTask)
                        taskList.remove(blockedTask)
                        break
            else:
                task.depends.append(dependson)
        #cursor.Close()
        cursor.close()

    # Close the connection to the Bugzilla database
    #connection.Close()
    connection.close()

    return taskList

def writeTaskList(taskList):
    # Open the output file
    outfile = open(taskFilename, "w")

    # Write each task to the file
    for task in taskList:
        task.write(outfile, taskList, 0)

    # Close the output file
    outfile.close()

# main

# Process arguments
if len(sys.argv) < 2:
   print "ERROR: No milestone specified."
   print "USAGE: " + sys.argv[0] + " MILESTONE [MILESTONE...]"
   sys.exit()

# Write the flags data file
writeFlagsFile()

# Write the project data file
writeProjectData()

for milestone in sys.argv[1:]:
  # Build a task list of resolved bugs from the Bugzilla database
  taskList = buildResolvedBugTaskList()

  # Write the task list to the output file
  taskFilename = milestone + "_resolved_tasks.tji"
  writeTaskList(taskList)

  # Build a task list of open bugs from the Bugzilla database
  taskList = buildOpenBugTaskList()

  # Write the task list to the output file
  taskFilename = milestone + "_open_tasks.tji"
  writeTaskList(taskList)
