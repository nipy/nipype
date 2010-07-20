# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""IPython 'nipype' profile.

Updates the TAB completion of IPython to hide Traits attributes from
results of TAB completion.  Also defines a magic command
``nipype_mode`` to allow users to toggle the traits completer on and
off.

"""
#__test__ = False

import IPython.ipapi



def get_nipype_mode():
    ip = IPython.ipapi.get()
    try:
        nipype_mode = ip.user_ns['nipype_mode']
    except KeyError:
        # Make sure nipype_mode exists in user namespace
        vars = {'nipype_mode' : True}
        ip.to_user_ns(vars, interactive=False)
    return ip.user_ns['nipype_mode']

def toggle_nipype_mode(self, args):
    """Toggle nipype mode on and off.

    When nipype mode is on, several attributes meant for internal use
    only are hidden from view.  This effects the attributes that are
    shown when using TAB-completion on nipype.interfaces objects.

    Specifically this enables an ipython traits completer which
    filters out the traits attributes.

    Examples
    --------
    In [1]: %nipype_mode
    nipype_mode is OFF

    In [2]: %nipype_mode
    nipype_mode is ON

    """

    ip = self.api
    mode = get_nipype_mode()
    if mode == True:
        # switch mode off
        nipype_mode_off()
        ip.user_ns['nipype_mode'] = False
    else:
        # switch mode on
        nipype_mode_on()
        ip.user_ns['nipype_mode'] = True

def nipype_mode_on():
    """Turn on the traits completer.

    This will hide all the traits attributes from the view of the user
    when doing TAB completion on any object that is a descendant of
    HasTraits.
    """
    from ipy_traits_completer import activate

    ip = IPython.ipapi.get()
    activate()
    print 'nipype_mode is ON'

def nipype_mode_off():
    """Turn traits completer off"""
    from IPython.strdispatch import StrDispatch

    ip = IPython.ipapi.get()
    sdisp = StrDispatch()
    ip.IP.strdispatchers['complete_command'] = sdisp
    ip.IP.Completer.custom_completers = sdisp
    print 'nipype_mode is OFF'

def main():
    """When we use the nipype profile we turn nipype_mode on."""
    
    ip = IPython.ipapi.get()

    mode = get_nipype_mode() # initialize nipype_mode in user_ns
    nipype_mode_on()

    # enable magic function
    ip.expose_magic('nipype_mode', toggle_nipype_mode)

if __name__ == '__main__':
    main()

