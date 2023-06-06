from pathlib import Path
import time
import traceback
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot
import utilities.api.item_ids as ids
import utilities.api.animation_ids as animation
import utilities.color as clr
import utilities.random_util as rd
import utilities.imagesearch as imsearch
import pyautogui as pag
from utilities.geometry import RuneLiteObject



class OSRSWDSmithing(WillowsDadBot):
    def __init__(self):
        bot_title = "WD Smithing"
        description = """Smithing script for Edgeville furnace."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 200
        self.take_breaks = True
        self.afk_train = True
        self.delay_min =0.37
        self.delay_max = .67
        self.activity = "Smelting"
        self.ore = "Bronze"
        self.withdraw_locations = []


    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        super().create_options()
        self.options_builder.add_dropdown_option("activity", "Activity?", ["Smelting", "Smithing"])
        self.options_builder.add_dropdown_option("ore", "Ore?", ["Bronze","Iron", "Steel", "Mithril", "Adamant", "Rune"])

    def save_options(self, options: dict):  # sourcery skip: for-index-underscore
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)
        for option in options:
            if option == "activity":
                self.activity = options[option]
            elif option == "ore":
                self.ore = options[option]

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg(f"Bot will wait between {self.delay_min} and {self.delay_max} seconds between actions.")
        self.log_msg("Options set successfully.")
        self.options_set = True


    def main_loop(self):
        """
        Main bot loop. We call setup() to set up the bot, then loop until the end time is reached.
        """
        # Setup variables
        self.setup()
        # Main loop
        while time.time() - self.start_time < self.end_time:

            runtime = int(time.time() - self.start_time)
            minutes_since_last_break = int((time.time() - self.last_break) / 60)
            seconds = int(time.time() - self.last_break) % 60
            percentage = (self.multiplier * .01)  # this is the percentage chance of a break
            self.roll_chance_passed = False

            # I wrap the whole bot in a try catch so that if there is an exception, it will be caught and the bot will retry, or stop and print exception if it fails too many times
            try:

                # if empty or out of materials, bank
                if self.is_inv_empty() or self.api_m.get_first_occurrence(self.withdraw_ids) == []:
                    # walk to bank
                    if not self.is_bank_open():
                        self.walk_horizontal(1, clr.YELLOW)
                    self.bank()
                
                # if not empty, smelt
                if not self.is_inv_empty() and self.api_m.get_first_occurrence(self.withdraw_ids) != []:
                    self.work()
                
                # while working, check for breaks
                while imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("emptyslot.png"), self.win.inventory_slots[27]) is None:
                    if self.check_for_level_up(self.WILLOWSDAD_IMAGES.joinpath("level_up_smithing.png")) is True:
                        self.work()
                    self.check_break(runtime, percentage, minutes_since_last_break, seconds)
                    time.sleep(self.random_sleep_length())

                
            except Exception as e: # catch exceptions, no changes needed unless you don't want a try catch
                self.log_msg(f"Exception: {e}")
                self.loop_count += 1
                if self.loop_count > 5:
                    self.log_msg("Too many exceptions, stopping.")
                    self.log_msg(f"Last exception: {e}")
                    # print out stack trace
                    stack_trace = traceback.format_exc()
                    self.log_msg(stack_trace)
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
        self.logout()
        self.stop()
    

    def setup(self):
        """Sets up loop variables, checks for required items, and checks location.
            This will ideally stop the bot from running if it's not setup correctly.
            * To-do: Add functions to check for required items, bank setup and locaiton.
            Args:
                None
            Returns:
                None"""
        super().setup()
        
        self.deposit_ids = [ids.BRONZE_BAR, ids.IRON_BAR, ids.STEEL_BAR, ids.MITHRIL_BAR, ids.ADAMANTITE_BAR, ids.RUNITE_BAR]
        self.withdraw_ids = [ids.COPPER_ORE, ids.TIN_ORE, ids.IRON_ORE, ids.COAL, ids.MITHRIL_ORE, ids.ADAMANTITE_ORE, ids.RUNITE_ORE]
        self.smelt_image = self.WILLOWSDAD_IMAGES.joinpath(f"{self.ore}_option.png")
        self.face_north()

        # Open bank and check settings
        self.open_bank()
        self.check_bank_settings()
    

    def work(self):
        if self.activity == "Smithing":
            self.smith()
        elif self.activity == "Smelting":
            self.smelt()


    def smith(self):
        return
    

    def smelt(self):
        """Smelts bars.
            Args:
                None"""
        # walk to smelter
        self.walk_horizontal(-1, clr.PINK)

        if smelter := self.get_nearest_tag(clr.PINK):
            self.mouse.move_to(smelter.random_point())
            while self.mouse.click(check_red_click=True) is False:
                self.mouse.move_to(smelter.random_point())
        else:
            self.log_msg("No smelter found, tag smelter with pink.")
            self.stop()
        
        # wait for smelting interface to open
        ore_option = imsearch.search_img_in_rect(self.smelt_image, self.win.chat, confidence=.1)
        time_waiting = 0
        while ore_option is None:
            time.sleep(self.random_sleep_length())
            ore_option = imsearch.search_img_in_rect(self.smelt_image, self.win.chat)
            time_waiting += self.random_sleep_length()
            if time_waiting > 10:
                self.log_msg("Smelting interface did not open, stopping.")
                self.stop()
        self.mouse.move_to(ore_option.random_point())
        self.mouse.click()

    def bank(self):
        """Deposits inventory and withdraws required items.
            Args:
                None"""
        if not self.is_bank_open():
            self.open_bank()
        self.deposit_items(self.api_m.get_first_occurrence(self.deposit_ids))
        self.withdraw_items2(self.withdraw_locations)
        self.close_bank()


    def check_bank_settings(self):
        """Makes sure bank settings are set correctly.
            Args:
                None
            Returns:
                None"""
        if self.ore == "Bronze":
            # make sure user has withdraw x set to 14
            self.check_withdraw_x(14)
            self.check_bronze_settings()
    

    def check_bronze_settings(self):
        if copper_ore := imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("Copper_ore_bank.png"), self.win.game_view.scale(.66)):
            self.withdraw_locations.append(copper_ore)
        else:
            self.log_msg("Couldn't find copper ore in bank.")
            self.stop()
        # now save location of tin ore
        if tin_ore := imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("Tin_ore_bank.png"), self.win.game_view.scale(.66 )):
            self.withdraw_locations.append(tin_ore)
        else:
            self.log_msg("Couldn't find tin ore in bank.")
            self.stop()


    def walk_horizontal(self, direction: int, color: clr = None, timeout: int = 60, img: Path = None):
        """
        Walks towards or away from a specific color tile in game or image.
        Returns: void
        Args: 
            color: color of the tile to walk to
            direction: direction to walk to (towards 1, away -1)
            timeout: time to wait before stopping"""
        
        if color is None and img is None:
            self.log_msg("No stop condition. Add color or img path to stop walking.")
            self.stop()

        time_start = time.time()
        while True:
            # Check if the player needs to switch direction for a smoother walk when walking to the bank
            if img != None:
                if change_direction_img := imsearch.search_img_in_rect(img, self.win.minimap):
                    return

            # Stop walking if timeout is exceeded
            if time.time() - time_start > timeout:
                self.log_msg(f"We've been walking for {timeout} seconds, something is wrong...stopping.")
                self.stop()

            if color is not None:
                # Stop walking if the target color tile is found
                if found := self.get_nearest_tag(color):
                    break

            # Get all cyan tiles in the game view
            shapes = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)

            # Stop if no cyan tiles are found
            if len(shapes) == 0:
                self.log_msg("No cyan tiles found, stopping.")
                return

            reverse = direction != 1

            # Sort the cyan tiles based on their distance from the top-center
            if len(shapes) > 1:
                shapes_sorted = sorted(shapes, key=RuneLiteObject.distance_from_rect_left , reverse=reverse)
                self.mouse.move_to(shapes_sorted[int(rd.fancy_normal_sample(0,1))].scale(3,3).random_point(), mouseSpeed = "fastest")
            else:
                self.mouse.move_to(shapes[0].scale(3,3).random_point(), mouseSpeed = "fastest")

            # Click on the selected tile and wait for a random duration between 0.35 and 0.67 seconds
            self.mouse.click()
            time.sleep(self.random_sleep_length(.67, 1.24))

        return