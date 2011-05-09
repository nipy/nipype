#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought logger package component>
#------------------------------------------------------------------------------

# Standard library imports.
import logging
import os

# Enthought library imports.
from traits.util.home_directory import get_home_directory


# Setup a logger for this module.
logger = logging.getLogger(__name__)


def create_email_message(fromaddr, toaddrs, ccaddrs, subject, priority,
                         include_project=False, stack_trace="", comments=""):
    # format a message suitable to be sent to the Roundup bug tracker

    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    from email.MIMEBase import MIMEBase

    message = MIMEMultipart()
    message['Subject'] = "%s [priority=%s]" % (subject, priority)
    message['To'] = ', '.join(toaddrs)
    message['Cc'] = ', '.join(ccaddrs)
    message['From'] = fromaddr
    message.preamble = 'You will not see this in a MIME-aware mail reader.\n'
    message.epilogue = ' ' # To guarantee the message ends with a newline

    # First section is simple ASCII data ...
    m = []
    m.append("Bug Report")
    m.append("==============================")
    m.append("")

    if len(comments) > 0:
        m.append("Comments:")
        m.append("========")
        m.append(comments)
        m.append("")

    if len(stack_trace) > 0:
        m.append("Stack Trace:")
        m.append("===========")
        m.append(stack_trace)
        m.append("")

    msg = MIMEText('\n'.join(m))
    message.attach(msg)

    # Include the log file ...
    if True:
        try:
            log = os.path.join(get_home_directory(), 'envisage.log')
            f = open(log, 'r')
            entries = f.readlines()
            f.close()

            ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            msg = MIMEBase(maintype, subtype)

            msg = MIMEText(''.join(entries))
            msg.add_header('Content-Disposition', 'attachment', filename='logfile.txt')
            message.attach(msg)
        except:
            logger.exception('Failed to include log file with message')

    # Include the environment variables ...
    if True:
        """
        Transmit the user's environment settings as well.  Main purpose is to
        work out the user name to help with following up on bug reports and
        in future we should probably send less data.
        """
        try:
            entries = []
            for key, value in os.environ.iteritems():
                entries.append('%30s : %s\n' % (key, value))

            ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            msg = MIMEBase(maintype, subtype)

            msg = MIMEText(''.join(entries))
            msg.add_header('Content-Disposition', 'attachment', filename='environment.txt')
            message.attach(msg)

        except:
            logger.exception('Failed to include environment variables with message')


# FIXME: no project plugins exist for Envisage 3, yet, and this isn't the right
# way to do it, either. See the docstring of attachments.py.
#    # Attach the project if requested ...
#    if include_project:
#        from attachments import Attachments
#        try:
#            attachments = Attachments(message)
#            attachments.package_any_relevant_files()
#        except:
#            logger.exception('Failed to include workspace files with message')

    return message


