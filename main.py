from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, SystemExitEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

import subprocess


ACTIVATE_COMMAND = 'wmctrl -i -a {}'


def list_windows():
    """List the windows being managed by the window manager.

    Returns:
        list -- with dict for each window entry:
                'id': window ID
                'desktop': desktop num, -1 for sticky (see `man wmctrl`)
                'pid': process id for the window
                'host': hostname where the window is at
                'title': window title"""
    proc = subprocess.Popen(['wmctrl', '-lp'],  # -l for list, -p include PID
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    windows = []
    for line in out.splitlines():
        info = str(line, encoding='utf8').split()
        # Format expected: ID num PID host title with spaces
        window_id = info[0]
        desktop_num = info[1]
        pid = info[2]
        host = info[3]
        title = ' '.join(info[4:])
        windows.append({
            'id': window_id,
            'desktop': desktop_num,
            'pid': pid,
            'host': host,
            'title': title
        })

    return windows


def get_process_name(pid):
    """Find out process name, given its' ID

    Arguments:
        pid {int} -- process ID
    Returns:
        str -- process name
    """
    proc = subprocess.Popen(['ps', '-p', pid, '-o', 'comm='],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err=proc.communicate()
    return out.strip().decode('utf-8')


def get_open_windows():
    """Get open windows

    Returns:
        List[ExtensionResultItem] -- list of Ulauncher result items
    """
    windows=list_windows()
    # Filter out stickies (desktop is -1)
    non_stickies=filter(lambda x: x['desktop'] != '-1', windows)

    results = []
    for window in non_stickies:
        results.append(ExtensionResultItem(icon='images/icon.png',
                                           name=get_process_name(window['pid']),
                                           description=window['title'],
                                           on_enter=RunScriptAction(ACTIVATE_COMMAND.format(window['id']), None)
                       ))
    return results


class DemoExtension(Extension):

    def __init__(self):
        super(DemoExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(SystemExitEvent, SystemExitEventListener())
        self.windows = []


class SystemExitEventListener(EventListener):
    def on_event(self, event, extension):
        pass

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        windows = get_open_windows()
        extension.windows = windows  # persistance

        arg = event.get_argument()
        if arg is not None:
            # filter by title or process name
            windows = filter(lambda x: arg in x.get_name() or arg in x.get_description(None),
                             windows)

        return RenderResultListAction(list(windows))


if __name__ == '__main__':
    DemoExtension().run()
