# Standard library imports
from cStringIO import StringIO
import logging
import os
import zipfile

# Enthought library imports
from pyface.workbench.api import View as WorkbenchView
from traits.api import Any, Callable, HasTraits, Instance, List, \
    Property, Undefined, on_trait_change

root_logger = logging.getLogger()
logger = logging.getLogger(__name__)


class LoggerService(HasTraits):
    """ The persistent service exposing the Logger plugin's API.
    """

    # The Envisage application.
    application = Any()

    # The logging Handler we use.
    handler = Any()

    # Our associated LoggerPreferences.
    preferences = Any()

    # The view we use.
    plugin_view = Instance(WorkbenchView)

    # Contributions from other plugins.
    mail_files = Property(List(Callable))

    def save_preferences(self):
        """ Save the preferences.
        """
        self.preferences.preferences.save()

    def whole_log_text(self):
        """ Return all of the logged data as formatted text.
        """
        lines = [ self.handler.format(rec) for rec in self.handler.get() ]
        # Ensure that we end with a newline.
        lines.append('')
        text = '\n'.join(lines)
        return text

    def create_email_message(self, fromaddr, toaddrs, ccaddrs, subject,
                             priority, include_userdata=False, stack_trace="",
                             comments="", include_environment=True):
        """ Format a bug report email from the log files.
        """
        from email.mime.application import MIMEApplication
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        message = MIMEMultipart()
        message['Subject'] = "%s [priority=%s]" % (subject, priority)
        message['To'] = ', '.join(toaddrs)
        message['Cc'] = ', '.join(ccaddrs)
        message['From'] = fromaddr
        message.preamble = 'You will not see this in a MIME-aware mail ' \
            'reader.\n'
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
        logtext = self.whole_log_text()
        msg = MIMEText(logtext)
        msg.add_header('Content-Disposition', 'attachment',
            filename='logfile.txt')
        message.attach(msg)

        # Include the environment variables ...
        # FIXME: ask the user, maybe?
        if include_environment:
            # Transmit the user's environment settings as well.  Main purpose is
            # to work out the user name to help with following up on bug reports
            # and in future we should probably send less data.
            entries = []
            for key, value in sorted(os.environ.items()):
                entries.append('%30s : %s\n' % (key, value))

            msg = MIMEText(''.join(entries))
            msg.add_header('Content-Disposition', 'attachment',
                filename='environment.txt')
            message.attach(msg)

        if include_userdata and len(self.mail_files) != 0:
            f = StringIO()
            zf = zipfile.ZipFile(f, 'w')
            for mf in self.mail_files:
                mf(zf)
            zf.close()

            msg = MIMEApplication(f.getvalue())
            msg.add_header('Content-Disposition', 'attachment',
                filename='userdata.zip')
            message.attach(msg)

        return message

    def send_bug_report(self, smtp_server, fromaddr, toaddrs, ccaddrs, message):
        """ Send a bug report email.
        """
        try:
            import smtplib
            logger.debug("Connecting to: %s" % smtp_server)
            server = smtplib.SMTP(host=smtp_server)
            logger.debug("Connected: %s" % server)
            #server.set_debuglevel(1)
            server.sendmail(fromaddr, toaddrs + ccaddrs, message.as_string())
            server.quit()
        except Exception, e:
            logger.exception("Problem sending error report")

    #### Traits stuff #########################################################

    def _get_mail_files(self):
        return self.application.get_extensions(
            'traits.logger.plugin.mail_files')

    @on_trait_change('preferences.level_')
    def _level_changed(self, new):
        if (new is not None and new is not Undefined and
            self.handler is not None):
            root_logger.setLevel(self.preferences.level_)
            self.handler.setLevel(self.preferences.level_)
