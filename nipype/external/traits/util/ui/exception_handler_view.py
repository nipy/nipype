
from traitsui.api import Group, Item, View

class ExceptionHandlerView( View ):
    """ Default trait view for the ExceptionHandler. """

    width = 400
    height = 240
    title = 'Application Error'
    kind='modal'

    def __init__(self):
        super(ExceptionHandlerView, self).__init__(
            self.get_general_group(),
            self.get_details_group(),
            buttons=['OK'],
            resizable = True,
            handler = self.get_handler()
            )

    def get_general_group(self):
        """ Returns the Group containing the most basic information about
        the error.
        """
        group = Group( Item( name='message', style='readonly'),
                       Item( name='exception_only_text', style='readonly'),
                       label='General',
                       show_labels=False
                     )
        return group

    def get_details_group(self):
        """ Returns the Group containing the all available information about
        the error including the stack trace.
        """
        group = Group( Item( name='message', style='readonly'),
                       Item( name='exception_text', style='readonly',
                             resizable = True
                             ),
                       label='Details',
                       show_labels=False,
                     )
        return group

    def get_handler(self):
        """ Returns the Handler for the View.
        Default is None.
        """
        return None

### EOF
