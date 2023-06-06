import time
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot

import utilities.api.item_ids as ids
import utilities.color as clr
from utilities.geometry import RuneLiteObject
import utilities.random_util as rd
import pyautogui as pag
import utilities.imagesearch as imsearch
import random


class OSRSWDDegrimer(WillowsDadBot):
    def __init__(self):
        bot_title = "WD Degrimer"
        description = "Place this near a bank with ingredients and it will degrime your herbs."
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 100
        self.take_breaks = True
        self.afk_train = False
        self.delay_min =0.37
        self.delay_max = .67
        self.withdraw_ids = ids.GRIMY_GUAM_LEAF
        self.deposit_ids = ids.GUAM_LEAF
        self.herb_img = self.WILLOWSDAD_IMAGES.joinpath("Grimy_guam.png")

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        super().create_options()
        self.options_builder.add_dropdown_option("herb", "What herb to degrime?", ["Guam", "Marrentill", "Tarromin", "Harralander", "Ranarr", "Toadflax", "Irit", "Avantoe", "Kwuarm", "Snapdragon", "Cadantine", "Lantadyme", "Dwarf", "Torstol"])

    def save_options(self, options: dict):
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)
        for option in options:
            if option == "herb":
                if options[option] == "Guam":
                    self.withdraw_ids = ids.GRIMY_GUAM_LEAF
                    self.deposit_ids = ids.GUAM_LEAF
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Marrentill":
                    self.withdraw_ids = ids.GRIMY_MARRENTILL
                    self.deposit_ids = ids.MARRENTILL
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Tarromin":
                    self.withdraw_ids = ids.GRIMY_TARROMIN
                    self.deposit_ids = ids.TARROMIN
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Harralander":
                    self.withdraw_ids = ids.GRIMY_HARRALANDER
                    self.deposit_ids = ids.HARRALANDER
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Ranarr":
                    self.withdraw_ids = ids.GRIMY_RANARR_WEED
                    self.deposit_ids = ids.RANARR_WEED
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Toadflax":
                    self.withdraw_ids = ids.GRIMY_TOADFLAX
                    self.deposit_ids = ids.TOADFLAX
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Irit":
                    self.withdraw_ids = ids.GRIMY_IRIT_LEAF
                    self.deposit_ids = ids.IRIT_LEAF
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Avantoe":
                    self.withdraw_ids = ids.GRIMY_AVANTOE
                    self.deposit_ids = ids.AVANTOE
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Kwuarm":
                    self.withdraw_ids = ids.GRIMY_KWUARM
                    self.deposit_ids = ids.KWUARM
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Snapdragon":
                    self.withdraw_ids = ids.GRIMY_SNAPDRAGON
                    self.deposit_ids = ids.SNAPDRAGON
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Cadantine":
                    self.withdraw_ids = ids.GRIMY_CADANTINE
                    self.deposit_ids = ids.CADANTINE
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Lantadyme":
                    self.withdraw_ids = ids.GRIMY_LANTADYME
                    self.deposit_ids = ids.LANTADYME
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Dwarf":
                    self.withdraw_ids = ids.GRIMY_DWARF_WEED
                    self.deposit_ids = ids.DWARF_WEED
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
                elif options[option] == "Torstol":
                    self.withdraw_ids = ids.GRIMY_TORSTOL
                    self.deposit_ids = ids.TORSTOL
                    self.herb_img = self.WILLOWSDAD_IMAGES.joinpath(f"Grimy_{options[option].lower()}.png")
            else:
                self.log_msg(f"Unknown option: {option}")

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg(f"Bot will wait between {self.delay_min} and {self.delay_max} seconds between actions.")
        self.log_msg(f"Herb: {self.deposit_ids}.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        """
        When implementing this function, you have the following responsibilities:
        1. If you need to halt the bot from within this function, call `self.stop()`. You'll want to do this
           when the bot has made a mistake, gets stuck, or a condition is met that requires the bot to stop.
        2. Frequently call self.update_progress() and self.log_msg() to send information to the UI.
        3. At the end of the main loop, make sure to call `self.stop()`.

        Additional notes:
        - Make use of Bot/RuneLiteBot member functions. There are many functions to simplify various actions.
          Visit the Wiki for more.
        - Using the available APIs is highly recommended. Some of all of the API tools may be unavailable for
          select private servers. To see what the APIs can offer you, see here: https://github.com/kelltom/OSRS-Bot-COLOR/tree/main/src/utilities/api.
          For usage, uncomment the `api_m` and/or `api_s` lines below, and use the `.` operator to access their
          functions.
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
            deposit_slots = self.api_m.get_first_occurrence(self.deposit_ids)
            self.roll_chance_passed = False

            try:
                if len(self.api_m.get_inv_item_indices(self.withdraw_ids)) == 0:
                    while not self.is_bank_open():
                        self.open_bank()
                        time.sleep(self.random_sleep_length())
                    self.check_deposit_all()
                    self.deposit_items(deposit_slots, self.deposit_ids)
                    time.sleep(self.random_sleep_length())
                    self.supplies_left = self.withdraw_items(self.withdraw_paths)
                    time.sleep(self.random_sleep_length())
                    self.close_bank()

                # Check if idle
                else:
                    self.degrime_herb(self.afk_train, self.take_breaks)
                    if self.afk_train:
                        self.switch_window()
                        self.sleep(percentage)
                    if not self.is_focused:
                        self.switch_window()

            except Exception as e:
                self.log_msg(f"Exception: {e}")
                self.loop_count += 1
                if self.loop_count > 5:
                    self.log_msg("Too many exceptions, stopping.")
                    self.log_msg(f"Last exception: {e}")
                    self.stop()
                continue

            # -- End bot actions --
            # self.check_break(runtime, percentage, minutes_since_last_break, seconds, deposit_slots)
            self.loop_count = 0
            if self.take_breaks:
                self.check_break(runtime, percentage, minutes_since_last_break, seconds)
            current_progress = round((time.time() - self.start_time) / self.end_time, 2)
            if current_progress != round(self.last_progress, 2):
                self.update_progress((time.time() - self.start_time) / self.end_time)
                self.last_progress = round(self.progress, 2)
            if not self.supplies_left:
                self.log_msg("Finished.")
                self.stop()

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
        self.idle_time = 0
        self.herb = 0
        self.withdraw_paths = [self.herb_img]
        self.supplies_left = True
    

    def sleep(self, percentage):
        """Sleeps for a random amount of time between the min and max delay. While player is doing an action.
            Args:
                None
            Returns:
                None"""
        # initialize variables
        self.breaks_skipped = 0
        afk_time = 0
        afk__start_time = time.time() 
        
        # loop until no more items in inventory match the withdraw_ids
        while len(self.api_m.get_inv_item_indices(self.withdraw_ids)) != 0:
            # sleep for a random amount of time
            time.sleep(self.random_sleep_length(.65, 2.2))
            afk_time = int(time.time() - afk__start_time)
            # check if the focus is on the Runelite window
            self.is_runelite_focused()
            # calculate the number of breaks skipped
            self.breaks_skipped = afk_time // 15

        # if any breaks were skipped, update the percentage chance and multiplier
        if self.breaks_skipped > 0:
            self.roll_chance_passed = True
            self.multiplier += self.breaks_skipped * .25
            self.log_msg(f"Skipped {self.breaks_skipped} break rolls while afk, percentage chance is now {round(percentage * 100)}%")



    def degrime_herb(self, afk=False, breaks=False):
        """
        clean herbs by clicking on each item
        Returns:
            void
        Args:
            None
        """
        # Define inventory slot indices in custom "S" motion, top to bottom and then bottom to top
        s_motion_indices = [0, 4, 8, 12, 16, 20, 24, 25, 21, 17, 13, 9, 5, 1, 2, 6, 10, 14, 18, 22, 26, 27, 23, 19, 15, 11, 7, 3]

        # Get all items in inventory that match the withdraw_ids
        items = self.api_m.get_inv_item_indices(self.withdraw_ids)

        # Filter s_motion_indices to include only those indices that are in the items list
        s_motion_items = [index for index in s_motion_indices if index in items]

        # Move mouse to each item and click in the custom "S" motion
        for index in s_motion_items:
            self.mouse.move_to(self.win.inventory_slots[index].random_point(), mouseSpeed="fastest", knotsCount=0)
            self.mouse.click()
            # If the afk flag is set, return early to simulate an AFK state
            if afk:
                return

        # If the breaks flag is set, update the roll chance passed variable
        if breaks:
            self.roll_chance_passed = True