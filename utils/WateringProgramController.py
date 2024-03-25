import threading
import time
from datetime import datetime

from google.cloud.firestore_v1.watch import ChangeType

from domain.WateringProgram import WateringProgram
from utils.datetime_utils import get_current_datetime_tz
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.raspberry_controller import RaspberryController
from utils.remote_requests import RemoteRequests


class WateringProgramController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self._watering_programs = {}
        self._active_watering_program_id = None
        self._is_watering_programs_active = None

        self.raspberry_id = getserial()
        self._pump_controller = RaspberryController().pump_controller
        self._moisture_controller = RaspberryController().moisture_controller
        self._raspberry_controller = RaspberryController()

        self._watering_thread = None
        self._moisture_check_thread = None

        self._watering_thread_finished = threading.Event()
        self._moisture_check_thread_finished = threading.Event()

        self._gui_update_callback = None

        self._watering_cycle_start_time = None
        self._watering_cycle_end_time = None

    def perform_initial_setup(self):
        self.get_watering_programs()
        self.get_is_watering_programs_active()
        self.get_active_watering_program_id()

        RemoteRequests().add_listener_for_watering_programs_changes(
            self._update_values_on_receive_from_network
        )

        self._schedule_watering()

    def get_watering_programs(self):
        watering_programs_list = RemoteRequests().get_watering_programs()
        self._watering_programs = {program.id: program for program in watering_programs_list}
        return watering_programs_list

    def get_active_watering_program_id(self):
        self._active_watering_program_id = RemoteRequests().get_active_watering_program_id()
        return self._active_watering_program_id

    def set_active_watering_program_id(self, program_id):
        RemoteRequests().set_active_watering_program_id(program_id)
        self._active_watering_program_id = program_id
        self._schedule_watering()

    def get_is_watering_programs_active(self):
        self._is_watering_programs_active = RemoteRequests().get_is_watering_programs_active()
        return self._is_watering_programs_active

    def set_is_watering_programs_active(self, is_active):
        RemoteRequests().set_is_watering_programs_active(is_active)
        self._is_watering_programs_active = is_active

    def _get_active_watering_program(self):
        if self._active_watering_program_id is None or self._watering_programs is None:
            return None
        if self._active_watering_program_id not in self._watering_programs:
            return None
        return self._watering_programs[self._active_watering_program_id]

    def _compute_initial_delay_sec(self, program):
        current_time = get_current_datetime_tz()
        seconds_passed_today = (current_time.time().hour * 60 * 60
                                + current_time.time().minute * 60
                                + current_time.time().second)

        program_start_time = program.time_of_day_min * 60
        time_to_wait_sec = program_start_time - seconds_passed_today

        if time_to_wait_sec < 0:
            time_to_wait_sec += 24 * 60 * 60

        return time_to_wait_sec

    def _compute_watering_interval_sec(self, program):
        return program.frequency_days * 24 * 60 * 60

    def _schedule_watering(self):
        if self._active_watering_program_id is None:
            return

        self._cancel_running_tasks()
        active_program = self._get_active_watering_program()
        if active_program is None:
            return

        initial_delay_sec = self._compute_initial_delay_sec(active_program)
        self._watering_thread_finished.clear()
        self._moisture_check_thread_finished.clear()

        self._watering_thread = threading.Thread(
            target=self._watering_task,
            args=(active_program, initial_delay_sec,),
            daemon=True
        )
        self._watering_thread.start()

        self._moisture_check_thread = threading.Timer(
            interval=0,
            function=self._moisture_check_task,
            args=(active_program, 3600,),
        )
        self._moisture_check_thread.daemon = True
        self._moisture_check_thread.start()

    def _cancel_running_tasks(self):
        if self._watering_thread is not None:
            self._watering_thread_finished.set()
            self._watering_thread.join()

        if self._moisture_check_thread is not None:
            self._moisture_check_thread_finished.set()
            self._moisture_check_thread.join()

    def _watering_task(self, program, initial_delay_sec=0):
        self._watering_thread_finished.wait(initial_delay_sec)
        if self._watering_thread_finished.is_set():
            return

        water_interval_sec = self._compute_watering_interval_sec(program)

        while not self._watering_thread_finished.is_set():
            self._watering_thread_finished.wait(water_interval_sec)
            if self._watering_thread_finished.is_set():
                return

            if self._is_watering_programs_active:
                current_soil_moisture = self._moisture_controller.get_moisture_percentage()

                if current_soil_moisture < program.max_moisture:
                    self._raspberry_controller.water_for_liters(program.quantity_l)

    def _moisture_check_task(self, program, sleep_time_sec=600):
        while not self._moisture_check_thread_finished.is_set():
            self._moisture_check_thread_finished.wait(sleep_time_sec)
            if self._moisture_check_thread_finished.is_set():
                return

            if self._is_watering_programs_active:
                current_soil_moisture = self._moisture_controller.get_moisture_percentage()

                if current_soil_moisture < program.min_moisture:
                    self._raspberry_controller.water_for_liters(program.quantity_l)

    def set_on_receive_from_network_callback(self, _update_values_on_receive_from_network):
        self._gui_update_callback = _update_values_on_receive_from_network

    def _update_values_on_receive_from_network(
            self,
            doc_snapshot,
            changes,
            read_time
    ):
        # print(f"Received new data from network in {read_time}")

        for change in changes:
            change_type = change.type
            changed_doc = change.document
            doc_id = changed_doc.id
            doc_data = changed_doc.to_dict()
            #
            # print(f"Change type: {change_type}")
            # print(f"Changed doc id: {doc_id}")
            # print(f"Changed doc data: {doc_data}")

            new_programs = {}
            new_active_program_id = None
            new_is_watering_programs_active = None

            changed_active_program = False

            if "name" in doc_data:  # this is a program
                doc_data["id"] = doc_id

                if change_type == ChangeType.ADDED or change_type == ChangeType.MODIFIED:
                    new_programs[doc_id] = WateringProgram().fromDict(doc_data)
                elif change_type == ChangeType.REMOVED:
                    new_programs.pop(doc_id, None)

                if doc_id == self._active_watering_program_id:
                    changed_active_program = True

            if "activeProgramId" in doc_data:
                new_active_program_id = str(doc_data["activeProgramId"])

            if "wateringProgramsEnabled" in doc_data:
                new_is_watering_programs_active = doc_data["wateringProgramsEnabled"]

            old_active_program_id = self._active_watering_program_id

            if new_programs is not None:
                self._watering_programs = new_programs
            if new_active_program_id is not None:
                self._active_watering_program_id = new_active_program_id
            if new_is_watering_programs_active is not None:
                self._is_watering_programs_active = new_is_watering_programs_active

            if new_active_program_id != old_active_program_id or changed_active_program:
                self._schedule_watering()

            if self._gui_update_callback is not None:
                self._gui_update_callback(
                    new_programs=new_programs,
                    new_active_program_id=new_active_program_id,
                    new_is_watering_programs_active=new_is_watering_programs_active
                )
            else:
                print("No callback set for updating the GUI")
