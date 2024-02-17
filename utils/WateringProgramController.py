import threading
import time
from datetime import datetime

from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.raspberry_controller import RaspberryController


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

    def perform_initial_setup(self):
        self.get_watering_programs()
        self.get_is_watering_programs_active()
        self.get_active_watering_program_id()

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
        return next((program for program in self._watering_programs if program.id == self._active_watering_program_id), None)

    def _compute_initial_delay_sec(self, program):
        current_time = datetime.now()
        start_of_day = datetime(current_time.year, current_time.month, current_time.day)
        seconds_passed_today = (current_time - start_of_day).total_seconds()

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
