import threading
import time
from datetime import datetime

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
        self._watering_programs = None
        self._active_watering_program_id = None
        self._is_watering_programs_active = None

        self.raspberry_id = getserial()
        self._pump_controller = RaspberryController().pump_controller
        self._moisture_controller = RaspberryController().moisture_controller

        self._watering_thread = None
        self._moisture_check_thread = None

        self._gui_update_callback = None

    def perform_initial_setup(self):
        self.get_watering_programs()
        self.get_is_watering_programs_active()
        self.get_active_watering_program_id()

        FirebaseController().add_listener_for_watering_programs_changes(
            self.raspberry_id,
            self._update_values_on_receive_from_network
        )

    def get_watering_programs(self):
        self._watering_programs = FirebaseController().get_watering_programs(self.raspberry_id)
        return self._watering_programs

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
        return next((program for program in self._watering_programs if program.id == self._active_watering_program_id), None)

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
        time_to_wait_sec = 10

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

        self._watering_thread = threading.Timer(
            interval=initial_delay_sec,
            function=self._watering_task,
            args=(active_program,)
        )
        self._watering_thread.daemon = True
        self._watering_thread.start()

        self._moisture_check_thread = threading.Timer(
            interval=0,
            function=self._moisture_check_task,
            args=(active_program, 3600,)
        )
        self._moisture_check_thread.daemon = True
        self._moisture_check_thread.start()

    def _cancel_running_tasks(self):
        if self._watering_thread is not None:
            self._watering_thread.cancel()

        if self._moisture_check_thread is not None:
            self._moisture_check_thread.cancel()

    def _watering_task(self, program):
        if self._is_watering_programs_active:
            current_soil_moisture = self._moisture_controller.get_moisture_percentage()
            if current_soil_moisture < program.max_moisture:
                print("Starting watering")
                self._pump_controller.start_watering_for_liters(program.quantity_l)

        self._watering_thread = threading.Timer(
            interval=self._compute_watering_interval_sec(program),
            function=self._watering_task,
            args=(program,)
        )
        self._watering_thread.daemon = True
        self._watering_thread.start()

    def _moisture_check_task(self, program, sleep_time_sec=600):
        if self._is_watering_programs_active:
            current_soil_moisture = self._moisture_controller.get_moisture_percentage()
            if current_soil_moisture < program.min_moisture:
                self._pump_controller.start_watering_for_liters(program.quantity_l)

        self._moisture_check_thread = threading.Timer(
            interval=sleep_time_sec,
            function=self._moisture_check_task,
            args=(program, sleep_time_sec,)
        )
        self._moisture_check_thread.daemon = True
        self._moisture_check_thread.start()

    def set_on_receive_from_network_callback(self, _update_values_on_receive_from_network):
        self._gui_update_callback = _update_values_on_receive_from_network

    def _update_values_on_receive_from_network(
            self,
            doc_snapshot,
            changes,
            read_time
    ):
        print(f"Received new data from network in {read_time}")

        # TODO: make more efficient by checking for changes, not just updating everything

        for change in changes:
            change_type = change.type
            changed_doc = change.document
            doc_id = changed_doc.id
            doc_data = changed_doc.to_dict()

            print(f"Change type: {change_type}")
            print(f"Changed doc id: {doc_id}")
            print(f"Changed doc data: {doc_data}")

        for doc in doc_snapshot:
            if doc.exists:
                updated_data = doc.to_dict()

                new_programs = None
                new_active_program_id = None
                new_is_watering_programs_active = None

                if "programs" in updated_data:
                    new_programs = [WateringProgram().fromDict(program) for program in updated_data["programs"]]

                if "activeProgramId" in updated_data:
                    new_active_program_id = str(updated_data["activeProgramId"])

                if "wateringProgramsEnabled" in updated_data:
                    new_is_watering_programs_active = bool(updated_data["wateringProgramsEnabled"])

                if new_programs is not None:
                    self._watering_programs = new_programs
                if new_active_program_id is not None:
                    self._active_watering_program_id = new_active_program_id
                if new_is_watering_programs_active is not None:
                    self._is_watering_programs_active = new_is_watering_programs_active

                if new_active_program_id is not None or new_programs is not None:
                    self._schedule_watering()

                if self._gui_update_callback is not None:
                    self._gui_update_callback(
                        new_programs=new_programs,
                        new_active_program_id=new_active_program_id,
                        new_is_watering_programs_active=new_is_watering_programs_active
                    )
                else:
                    print("No callback set for updating the GUI")
