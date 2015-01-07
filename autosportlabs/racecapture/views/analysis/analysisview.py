import kivy
kivy.require('1.8.0')
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from installfix_garden_graph import Graph, MeshLinePlot
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.uix.track.trackmap import TrackMap
from autosportlabs.racecapture.datastore import DataStore
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import os.path
from threading import Thread

Builder.load_file('autosportlabs/racecapture/views/analysis/analysisview.kv')

class LogImportWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(LogImportWidget, self).__init__(**kwargs)
        self._dstore = kwargs.get('datastore')
        self._dismiss = kwargs.get('dismiss_cb')
        if self._dstore.is_open:
            self.remove_widget(self.ids['dstore_path'])
            self.remove_widget(self.ids['dstore_select'])
            self.remove_widget(self.ids['dstore_loc_label'])

    def warn(self, title='', text=''):
          content = Label(text=text)
          popup = Popup(title=title, content=content , size_hint=(0.9, 0.9))
          popup.open()

    def close_dstore_select(self, *args):
        self._dstore_select.dismiss()
        self._dstore_select = None

    def set_dstore_path(self, instance):
        filename = os.path.join(instance.path, instance.filename)
        if not filename.endswith('.sq3'):
            filename = filename + '.sq3'
        self.ids['dstore_path'].text = filename
        self._dstore_select.dismiss()

    def select_dstore(self):
        ok_cb = self.close_dstore_select
        content = SaveDialog(ok=self.set_dstore_path,
                             cancel=self.close_dstore_select,
                             filters=['*' + '.sq3'])
        self._dstore_select = Popup(title="Select Datastore", content=content, size_hint=(0.9, 0.9))
        self._dstore_select.open()

    def close_log_select(self, *args):
        self._log_select.dismiss()
        self._log_select = None

    def set_log_path(self, instance):
        print instance
        self.ids['log_path'].text = instance.selection[0]
        self._log_select.dismiss()

    def select_log(self):
        ok_cb = self.close_log_select
        content = LoadDialog(ok=self.set_log_path,
                             cancel=self.close_log_select,
                             filters=['*' + '.log'])
        self._log_select = Popup(title="Select Log", content=content, size_hint=(0.9, 0.9))
        self._log_select.open()

    def _loader_thread(self, logpath, session_name, session_notes):
        self._dstore.import_datalog(logpath, session_name, session_notes, self._update_progress)
        self._dismiss()

    def _update_progress(self, percent_complete=0):
        self.ids['log_load_progress'].value = int(percent_complete)
        

    def load_log(self):
        logpath = self.ids['log_path'].text
        dstore_path = self.ids['dstore_path'].text
        session_name = self.ids['session_name'].text
        session_notes = self.ids['session_notes'].text

        if logpath == '':
            self.warn("No Log Specified",
                      "Please select a log file using the button to the right of 'Datalog Location'"\
                      ", or enter its path into the Datalog Location text box")
            return

        if not os.path.isfile(logpath):
            self.warn("Invalid log specified",
                      "Unable to find specified log file: {}. \nAre you sure it exists?".format(logpath))
            return

        if not self._dstore.is_open:
            if dstore_path == '':
                self.warn("No Datastore Specified",
                          "Please select a location to store the datastore using the button\n"\
                          "to the right of 'Datastore Location' or enter a valid path into the text box.\n\n"\
                          "You may also select an existing datstore to append lap data.")
                return

            if os.path.isfile(dstore_path):
                self._dstore.open_db(dstore_path)
            else:
                self._dstore.new(dstore_path)

        print "loading log", self.ids['log_path'].text

        if session_name == '':
            self.warn("No session name specified", "Please specify a name for this session")
            return

        t = Thread(target=self._loader_thread, args=(logpath, session_name, session_notes))
        t.daemon = True
        t.start()


class AnalysisView(Screen):
    _settings = None
    _databus = None
    _trackmanager = None
    _datastore = DataStore()

    def __init__(self, **kwargs):
        super(AnalysisView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = kwargs.get('dataBus')
        self._settings = kwargs.get('settings')
        self._trackmanager = kwargs.get('trackmanager')
        self.init_view()

    def on_tracks_updated(self, track_manager):
        tracks = track_manager.getAllTrackIds()

        if len(tracks) > 0:
            trackId = track_manager.getAllTrackIds()[0]
            track = track_manager.getTrackById(trackId)
            self.ids.trackview.initMap(track)
            self._trackmanager = track_manager

    def open_datastore(self):
        pass

    def _log_import_thread(self):
        self._datastore.import_datalog
        pass

    def _start_log_import(self, instance):
        self._popup.dismiss()
        #The comma is necessary since we need to pass in a sequence of args
        t = Thread(target=self._log_import_thread, args=(instance,))
        t.daemon = True
        t.start()

    def import_datalog(self):
        content = LogImportWidget(datastore=self._datastore, dismiss_cb=self.dismiss_popup)

        self._popup = Popup(title="Import Datalog", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def init_view(self):
        pass

    def dismiss_popup(self, *args):
        self._popup.dismiss()
