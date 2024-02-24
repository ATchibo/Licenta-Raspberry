import threading
import time
from datetime import datetime

from google.cloud.firestore_v1.watch import ChangeType

from domain.WateringProgram import WateringProgram
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.raspberry_controller import RaspberryController

# TODO :
# add listener in firebase controller - look for changes in selected active program
# add listener to look for enabled watering programs
# add listener to look for updates to the watering program list

class WateringProgramController:
    _self = None

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self):
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

        self._scheduling_counter = 0
        self._watering_counter = 0
        self.finished_counter = 0

    def perform_initial_setup(self):
        self.get_watering_programs()
        self.get_is_watering_programs_active()
        self.get_active_watering_program_id()

        FirebaseController().add_listener_for_watering_programs_changes(
            self.raspberry_id,
            self._update_values_on_receive_from_network
        )

    def get_watering_programs(self):
        watering_programs_list = FirebaseController().get_watering_programs(self.raspberry_id)
        self._watering_programs = {program.id: program for program in watering_programs_list}
        return watering_programs_list

    def get_active_watering_program_id(self):
        self._active_watering_program_id = FirebaseController().get_active_watering_program_id(self.raspberry_id)
        return self._active_watering_program_id

    def set_active_watering_program_id(self, program_id):
        FirebaseController().set_active_watering_program_id(self.raspberry_id, program_id)
        self._active_watering_program_id = program_id
        self._schedule_watering()

    def get_is_watering_programs_active(self):
        self._is_watering_programs_active = FirebaseController().get_is_watering_programs_active(self.raspberry_id)
        return self._is_watering_programs_active

    def set_is_watering_programs_active(self, is_active):
        FirebaseController().set_is_watering_programs_active(self.raspberry_id, is_active)
        self._is_watering_programs_active = is_active

    def _get_active_watering_program(self):
        if self._active_watering_program_id is None or self._watering_programs is None:
            return None
        if self._active_watering_program_id not in self._watering_programs:
            return None
        return self._watering_programs[self._active_watering_program_id]

    def _compute_initial_delay_sec(self, program):
        current_time = datetime.now()
        seconds_passed_today = (current_time.time().hour * 24 * 60
                                + current_time.time().minute * 60
                                + current_time.time().second)
        program_start_time = program.time_of_day_min * 60
        time_to_wait_sec = program_start_time - seconds_passed_today

        if time_to_wait_sec < 0:
            time_to_wait_sec += 24 * 60 * 60

        # TODO: remove
        print(f"Time to wait: {time_to_wait_sec}")
        time_to_wait_sec = 5

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

        self._scheduling_counter += 1
        print(f"Scheduling watering: attempt {self._scheduling_counter}")

        initial_delay_sec = self._compute_initial_delay_sec(active_program)

        self._watering_thread_finished.clear()
        self._moisture_check_thread_finished.clear()

        self._watering_thread = threading.Thread(
            target=self._watering_task,
            args=(active_program, initial_delay_sec,),
            daemon=True
        )
        self._watering_thread.start()

        # self._moisture_check_thread = threading.Timer(
        #     interval=0,
        #     function=self._moisture_check_task,
        #     args=(active_program, 3600,)
        # )
        # self._moisture_check_thread.daemon = True
        # self._moisture_check_thread.start()

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
        print(f"Waiting for next watering: wait time {water_interval_sec}")

        while self._watering_thread_finished.wait(water_interval_sec):
            if self._watering_thread_finished.is_set():
                return

            print("Checking watering progrms active")

            if self._is_watering_programs_active:
                print("Watering programs active")

                self._watering_counter += 1
                print(f"Watering: attempt {self._watering_counter}")

                current_soil_moisture = self._moisture_controller.get_moisture_percentage()
                if current_soil_moisture < program.max_moisture:
                    print("Starting watering")
                    self._raspberry_controller.water_for_liters(program.quantity_l)

                    self.finished_counter += 1
                    print(f"Watering finished: count {self.finished_counter}")

            else:
                print("Watering programs not active")

            print(f"Waiting for next watering: wait time {water_interval_sec}")

    def _moisture_check_task(self, program, sleep_time_sec=600):
        while not self._moisture_check_thread_finished.is_set():
            self._moisture_check_thread_finished.wait(sleep_time_sec)
            if self._moisture_check_thread_finished.is_set():
                return

            if self._is_watering_programs_active:
                current_soil_moisture = self._moisture_controller.get_moisture_percentage()
                if current_soil_moisture < program.min_moisture:
                    print("Starting watering - low moisture")
                    self._raspberry_controller.water_for_liters(program.quantity_l)
                    print("Watering finished - low moisture")


    def set_on_receive_from_network_callback(self, _update_values_on_receive_from_network):
        self._gui_update_callback = _update_values_on_receive_from_network

    def _update_values_on_receive_from_network(
            self,
            doc_snapshot,
            changes,
            read_time
    ):
        print(f"Received new data from network in {read_time}")

        for change in changes:
            change_type = change.type
            changed_doc = change.document
            doc_id = changed_doc.id
            doc_data = changed_doc.to_dict()

            print(f"Change type: {change_type}")
            print(f"Changed doc id: {doc_id}")
            print(f"Changed doc data: {doc_data}")

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
