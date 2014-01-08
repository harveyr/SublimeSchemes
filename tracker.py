import os
import pickle

import sublime
import sublime_plugin


PLUGIN_PATH = os.path.split(os.path.realpath(__file__))[0]
SAVE_PATH = os.path.join(PLUGIN_PATH, 'history.sav')
SETTINGS_FILE = 'Preferences.sublime-settings'


def get_settings():
    return sublime.load_settings(SETTINGS_FILE)


class TrackedColorSchemes(object):
    def __init__(self):
        try:
            with open(SAVE_PATH, 'rb') as f:
                self.history = pickle.load(f)
        except (FileNotFoundError, EOFError):
            self.history = []

    def _pickle(self):
        with open(SAVE_PATH, 'wb') as f:
            pickle.dump(self.history, f)

    def promote(self, scheme):
        if self.history and scheme == self.history[0]:
            return
        try:
            self.history.pop(self.history.index(scheme))
        except ValueError:
            pass
        self.history.insert(0, scheme)
        self._pickle()

    def scheme_changed(self):
        settings = get_settings()
        scheme = settings.get('color_scheme')
        # Promote only if not already tracking. Otherwise the order will get
        # messed up while the user is highlighting different schemes.
        if not scheme in self.history:
            self.promote(scheme)

    def remove(self, index):
        self.history.pop(index)
        self._pickle()


tracked_schemes = TrackedColorSchemes()
get_settings().add_on_change('color_scheme', tracked_schemes.scheme_changed)


class BaseCommand(sublime_plugin.TextCommand):
    def show_quick_panel(self, on_done, on_highlight=None):
        sublime.active_window().show_quick_panel(
            [os.path.split(f)[1] for f in tracked_schemes.history],
            on_done,
            on_highlight=on_highlight
        )


class RemoveTrackedColorSchemeCommand(BaseCommand):
    def run(self, edit):
        self.show_quick_panel(self._remove)

    def _remove(self, index):
        tracked_schemes.remove(index)


class SwitchColorSchemeCommand(BaseCommand):
    def run(self, edit):
        self.show_quick_panel(self._switch, on_highlight=self._highlight)

    def _highlight(self, index):
        self._switch(index, reorder=False)

    def _switch(self, index, reorder=True):
        if index == -1:
            return

        scheme = tracked_schemes.history[index]
        if reorder:
            tracked_schemes.promote(scheme)

        settings = get_settings()
        if scheme == settings.get('color_scheme'):
            return

        print('Setting scheme to {}'.format(scheme))
        settings.set('color_scheme', scheme)
