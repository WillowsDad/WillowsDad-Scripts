import time
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot

import utilities.api.item_ids as ids
import utilities.color as clr
from utilities.geometry import RuneLiteObject
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
import pyautogui as pag
import utilities.imagesearch as imsearch
import random


class OSRSWDUltraCompostMaker(WillowsDadBot):
    def __init__(self):
        bot_title = "WillowsDad Ultra Compost Maker"
        description = "Place this near a bank with ingredients and it will make ultra compost for you. Note: AFK doesn't always switch screens."
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 60
        self.take_breaks = True
        self.afk_train = True
        self.delay_min =0.37
        self.delay_max = .67

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        super().create_options()   # This line is required to ensure that the parent class's options are created.

    def save_options(self, options: dict):
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)  # This line is required to ensure that the parent class's options are saved.

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        """
        Main bot loop. We call setup() to set up the bot, then loop until the end time is reached.
        """
        # Setup APIs
        # api_m = MorgHTTPSocket()
        # api_s = StatusSocket()
        self.setup()
        # Main loop
        while time.time() - self.start_time < self.end_time:

            runtime = int(time.time() - self.start_time)
            minutes_since_last_break = int((time.time() - self.last_break) / 60)
            seconds = int(time.time() - self.last_break) % 60
            percentage = (self.multiplier * .01)  # this is the percentage chance of a break
            deposit_slots = self.api_m.get_inv_item_first_indice(self.deposit_ids)
            self.roll_chance_passed = False

            try:
                # Inventory finished, deposit and withdraw
                if len(self.api_m.get_inv_item_indices(ids.SUPERCOMPOST)) == 0:
                    self.open_bank()
                    time.sleep(self.random_sleep_length()/2)
                    self.check_deposit_all()
                    self.deposit_items(deposit_slots, self.deposit_ids)
                    self.sleep(self.random_sleep_length()/2)
                    suplies_left = self.withdraw_items(self.withdraw_paths[0])
                    if not suplies_left:
                        self.log_msg("Out of supplies, stopping.")
                        self.stop()
                    self.close_bank()
                self.make_compost()
                if self.afk_train and self.is_runelite_focused():
                    time.sleep(self.random_sleep_length() * 2)
                    self.switch_window()
                self.sleep(percentage)

            except Exception as e:
                self.log_msg(f"Exception: {e}")
                self.loop_count += 1
                if self.loop_count > 5:
                    self.log_msg("Too many exceptions, stopping.")
                    self.log_msg(f"Last exception: {e}")
                    self.stop()
                continue

            # -- End bot actions --
            self.loop_count = 0
            if self.take_breaks:
                self.check_break(runtime, percentage, minutes_since_last_break, seconds)
            current_progress = round((time.time() - self.start_time) / self.end_time, 2)
            if current_progress != round(self.last_progress, 2):
                self.update_progress((time.time() - self.start_time) / self.end_time)
                self.last_progress = round(self.progress, 2)

        self.update_progress(1)
        self.log_msg("Finished.")
        self.stop()

    def setup(self):
        """Sets up loop variables, checks for required items, and checks location.
            Args:
                None
            Returns:
                None"""
        super().setup()
        self.withdraw_ids = [ids.SUPERCOMPOST, ids.VOLCANIC_ASH]
        self.withdraw_paths = [self.WILLOWSDAD_IMAGES.joinpath("Supercompost_bank.png"), self.WILLOWSDAD_IMAGES.joinpath("Volcanic_ash_bank.png")]
        self.deposit_ids = [ids.ULTRACOMPOST]
        self.supercompost = 0
        self.text_box_ultracompost = self.WILLOWSDAD_IMAGES.joinpath("textboxultracompost.png")
    

    def sleep(self, percentage):
        """Sleeps for a random amount of time between the min and max delay. While player is doing an action.
            Args:
                None
            Returns:
                None"""
        self.breaks_skipped = 0
        afk_time = 0
        afk__start_time = time.time() 

        while len(self.api_m.get_inv_item_indices(ids.SUPERCOMPOST)) != 0:
            time.sleep(self.random_sleep_length(.65, 2.2))
            afk_time = int(time.time() - afk__start_time)
            self.breaks_skipped = afk_time // 15

        if self.breaks_skipped > 0:
            self.roll_chance_passed = True
            self.multiplier += self.breaks_skipped * .25
            self.log_msg(f"Skipped {self.breaks_skipped} break rolls while afk, percentage chance is now {round(percentage * 100)}%")

    
    def is_runelite_focused(self):
        """
        This will check if the runelite window is focused.
        Returns: boolean
        Args: None
        """
        # Get the currently focused window
        current_window = pag.getActiveWindow()

        # Check if the window title contains a certain keyword (e.g. "Google Chrome")
        if current_window is None:
            return False
        if "runelite" in current_window.title.lower():
            self.is_focused = True
            return True
        else:
            self.is_focused = False
            return False
    
    
    def random_sleep_length(self, delay_min=0, delay_max=0):
        """Returns a random float between min and max"""
        if delay_min == 0:
            delay_min = self.delay_min
        if delay_max == 0:
            delay_max = self.delay_max
        return rd.fancy_normal_sample(delay_min, delay_max)
    

    def make_compost(self):
        """
        Makes compost by click on each item and hitting space
        Returns:
            void
        Args:
            None
        """
        # get unique items in inventory
        unique_items = self.api_m.get_inv_item_first_indice(self.withdraw_ids)

        # move mouse to each item and click
        for item in unique_items:
            self.mouse.move_to(self.win.inventory_slots[item].random_point())
            self.mouse.click()
            time.sleep(self.random_sleep_length())

        item_found = imsearch.search_img_in_rect(self.text_box_ultracompost, self.win.chat)
        search_time = time.time()
        while not item_found:
            item_found = imsearch.search_img_in_rect(self.text_box_ultracompost, self.win.chat)
            if time.time() - search_time > 2:
                self.log_msg("Error finding ultracompost in chat box, stopping.")
                self.stop()
            time.sleep(.1)
        time.sleep(self.random_sleep_length())
        pag.press("space")