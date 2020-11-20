from kivy import utils
from kivy.app import App
from kivy.core.text import Label
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty, ListProperty, NumericProperty, BooleanProperty, DictProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import ScreenManager, CardTransition, Screen
from kivy.core.window import Window
from kivy.uix.textinput import TextInput

import CustomWidgets
import utils.DBLayer as db
import utils.ConfigParser as config
import lang.Localization as lang


class ScreenManagement(ScreenManager):

    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.on_key)

    def on_key(self, window, key, *args):
        if key == 27:  # the esc key or 'Back' key on phone
            if self.current_screen.name == "lists_screen":
                return False  # exit the app from this page
            elif self.current_screen.name == "settings_screen":
                self.change_screen("lists_screen", 'right')
                return True  # do not exit the app
            elif self.current_screen.name == "entries_screen":
                self.change_screen("lists_screen", 'right')
                return True  # do not exit the app

    def change_screen(self, screen_name, direction):
        self.transition = CardTransition(direction=direction, duration=float(config.get('screen_transition_duration')))
        self.current = screen_name


class ListsScreen(Screen):
    def __init__(self,  **kw):
        super().__init__(**kw)
        Clock.schedule_once(self._do_setup)

    def _do_setup(self, *l):
        self.refresh_lists()

    @staticmethod
    def read_entries_count(list_id):
        return db.read_entries_count(list_id)

    def refresh_lists(self):
        lists = db.read_lists()
        self.ids.lists_panel_id.clear_widgets()
        for i in lists:
            list_btn = CustomWidgets.ButtonCustom(
                id=str(i[0]),  # id
                text=str(i[1] + " (" + db.read_entries_count(i[0]) + ")"),  # list name
                long_press_time=1,
                font_size=config.get('lists_font_size'),
                size_hint=(1, None),
            )
            list_btn.bind(on_release=self.open_entry)
            list_btn.bind(on_long_press=self.delete_list)
            lists_panel = self.ids.lists_panel_id
            lists_panel.add_widget(list_btn)

    def open_entry(self, btn_obj):
        EntriesScreen.current_list_id = btn_obj.id
        EntriesScreen.current_list_name = db.get_list_name(btn_obj.id)
        self.manager.transition = CardTransition(direction='left', duration=float(config.get('screen_transition_duration')))
        self.manager.current = "entries_screen"

    @staticmethod
    def create_list(text):
        text = text.strip()
        if text:
            result = db.create_list(text)
            if not result:
                MainApp.open_error_popup('Database error')

    def delete_list(self, btn_obj):
        db.delete_list_by_id(btn_obj.id)
        self.refresh_lists()


class EntriesScreen(Screen):
    current_list_id = StringProperty()
    current_list_name = StringProperty()

    def add_entry(self, entry_id, text, index):
        entry = Button(
            id=str(entry_id),
            text=str(text),
            size_hint=(1, None),
            height="70dp",
            font_size=config.get('entries_font_size'),
        )
        entry.bind(on_release=self.done_entry)
        self.ids.entries_panel_id.add_widget(entry, index)

    def refresh_entries(self):
        entries_list = db.read_entries(self.current_list_id)
        entries_count = len(entries_list)
        self.ids.entries_panel_id.clear_widgets()
        for entry_num in range(len(entries_list)):
            self.add_entry(entries_list[entry_num][0], entries_list[entry_num][2], (entries_count - entry_num))

    def done_entry(self, btn_obj):
        db.complete_entry(btn_obj.id)
        self.ids.entries_panel_id.remove_widget(btn_obj)

    def focus_entries_panel_id(self):
        self.ids.entries_panel_id.focus = True

    def create_entry(self, text):
        text = text.strip()
        if text:
            db.create_entry(self.current_list_id, text)
            self.refresh_entries()


class SettingsScreen(Screen):
    # TODO fix bug with font_size not apply on save(same as lang)
    # TODO move all kv strings to lang

    current_settings = {
        'background_colour': config.get('background_colour'),
        'lang': config.get('lang'),
        'entries_font_size': config.get('entries_font_size'),
        'lists_font_size': config.get('lists_font_size'),
        'max_suggestions_count': config.get('max_suggestions_count'),
        'font_size': config.get('font_size'),
    }

    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        self.get_current_settings()

    def get_current_settings(self):
        for key in self.current_settings:
            self.current_settings[key] = config.get(key)

    @staticmethod
    def reset_db():
        db.recreate_database()

    def apply_settings(self):
        for key in self.current_settings:
            config.set(key, self.current_settings[key])
        # TODO lang reload doesnt work
        # lang.reload_lang()
        # config.load_config()
        MainApp.build(self)


class ErrorPopup(Popup):
    # TODO implement exact error display
    popup_title = 'some popup title'
    error_text = "some error text"


class MainApp(App):

    def build(self):
        # TODO refactor backgroung
        backgroung_dict = {'Orange': [0.8, 0.4, 0.0, 1], "White": [1.0, 1.0, 1.0, 1]}
        Window.clearcolor = backgroung_dict[config.get('background_colour')]
        Window.softinput_mode = 'below_target'  # TextInput keyboard position https://android.developreference.com/article/19684878/Android+on-screen+keyboard+hiding+Python+Kivy+TextInputs
        # TODO move ALL paths to system settings
        self.icon = 'images/icon.png'
        self.title = config.get('app_title') + '   ' + config.get('app_version')
        return ScreenManagement()

    def build_config(self, app_config):
        app_config.setdefaults('', {
            #'font_size': '15dp',
            #'entries_font_size': 42,
            #'lists_font_size': '15dp',
            'app_version': '0.0.20',
            'app_title': 'TODOit',
            'db_path': "..// TODO.db",
            'screen_transition_duration': 0,

        },
                               )

    @staticmethod
    def open_error_popup(text):
        ErrorPopup.error_text = text
        ErrorPopup().open()


if __name__ == '__main__':
    config.load_config()
    db.create_db()
    MainApp().run()






