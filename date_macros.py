#!/usr/bin/python
# $Id: date_macros.py,v 1.6 2006/03/28 23:38:20 tom Exp $
#
# Script to write TaskJuggler macros that define various dates.
#
# This script relies on the following packages to be installed:
#   python
#
# Copyright (c) 2006-2006 Tom Schutter
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

# Configuration variables
macrosFilename = "date_macros.tji"
# End of configuration variables

import datetime

def writeMacros():
    # Get today's datetime
    now = datetime.datetime.today().replace(microsecond = 0)
    today = datetime.date.today()

    # Open the output file
    outfile = open(macrosFilename, "w")

    # Write DATETIME_NOW_LABEL
    outfile.write(
        "# DATETIME_NOW_LABEL is in human readable format\n" +
        "macro DATETIME_NOW_LABEL [" + now.isoformat(" ") + "]\n"
    )

    # Write DATETIME_NOW
    outfile.write(
        "# DATETIME_NOW is in taskjuggler format\n" +
        "macro DATETIME_NOW [" + now.isoformat("-") + "]\n"
    )

    # Write DATE_TODAY
    outfile.write(
        "macro DATE_TODAY [" + today.isoformat() + "]\n"
    )

    # Write DATE_TODAY_PLUS_X_MONTHS
    date = today
    month = datetime.timedelta(days=30)
    for delta in range(1,13):
        date += month
        outfile.write("macro DATE_TODAY_PLUS_" + str(delta) + "_MONTH")
        if delta > 1:
            outfile.write("S")
        outfile.write(" [" + date.isoformat()  + "]\n")

    # Close the output file
    outfile.close()

# main

# Write the project data file
writeMacros()
