import time
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot
import utilities.api.item_ids as ids
import utilities.api.animation_ids as animation
import utilities.color as clr
import utilities.random_util as rd
import utilities.imagesearch as imsearch
import pyautogui as pag


class OSRSWDFishing(WillowsDadBot):
    def __init__(self):
        bot_title = "WillowsDad Fishing"
        description = """Fishes at supported locations."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 60
        self.take_breaks = True
        self.afk_train = True
        self.delay_min =0.37
        self.delay_max = .67
        self.style = "Bait"
        self.power_fishing = False


    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        super().create_options()
        self.options_builder.add_dropdown_option("style", "What type of fishing?", ["Fly", "Bait", "Harpoon", "Net", "Cage"])
        self.options_builder.add_checkbox_option("power_fishing", "Power Fishing? Drops everything in inventory.", [" "])

    def save_options(self, options: dict):
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)
        for option in options:
            if option == "style":
                if options[option] == "Fly":
                    self.style = "Fly"
                elif options[option] == "Bait":
                    self.style = "Bait"
                elif options[option] == "Harpoon":
                    self.style = "Harpoon"
                elif options[option] == "Net":
                    self.style = "Net"
                elif options[option] == "Cage":
                    self.style = "Cage"
            elif option == "power_fishing":
                self.power_fishing = options[option] != []
            else:
                self.log_msg(f"Unexpected option: {option}")

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg(f"Bot will wait between {self.delay_min} and {self.delay_max} seconds between actions.")
        self.log_msg(f"Bot will{'' if self.power_fishing else ' not'} power chop.")
        self.log_msg(f"Bot will cut {options['style']} logs.")
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
            deposit_slots = self.api_m.get_inv_item_first_indice(self.deposit_ids)
            self.roll_chance_passed = False

            # check if inventory is full
            if self.api_m.get_is_inv_full():
                self.bank_or_drop(deposit_slots)

            # Check if idle
            if self.api_m.get_is_player_idle():
                self.log_msg("Fishing...")
                self.go_fish()

            if self.afk_train and self.is_fishing():

                if self.is_focused:
                    self.switch_window()
                self.sleep(percentage)

     
                
            # -- End bot actions --
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
        self.idle_time = 0
        self.deposit_ids = [ids.BIRD_NEST, ids.BIRD_NEST_5071, ids.BIRD_NEST_5072, ids.BIRD_NEST_5073, ids.BIRD_NEST_5074, ids.BIRD_NEST_5075, ids.BIRD_NEST_7413, ids.BIRD_NEST_13653, ids.BIRD_NEST_22798, ids.BIRD_NEST_22800, self.style]
        
        # Setup Checks for axes and tagged objects
        self.check_equipment()

        if not self.get_nearest_tag(clr.YELLOW) and not self.power_fishing:
            found = self.adjust_camera(clr.YELLOW)
            if not found:
                self.log_msg("Bank booths should be tagged with yellow, and in screen view. Please fix this.")
                self.stop()

        if not self.get_nearest_tag(clr.PINK):
            found = self.adjust_camera(clr.PINK)
            if not found:
                self.log_msg("Trees should be tagged with pink, and in screen view. Please fix this.")
                self.stop()
        
        self.check_bank_settings()


    def check_bank_settings(self):
        """Checks if the bank booth is set to deposit all items.
            Args:
                None
            Returns:
                None"""
        # self.open_bank()
        # self.close_bank()


    def is_fishing(self):
        """
        This will check if the player is currently woodcutting.
        Returns: boolean
        Args: None
        """
        # get the current player animation
        fishing_animation_list = [
            animation.FISHING_BARBARIAN_ROD, animation.FISHING_BARBTAIL_HARPOON, animation.FISHING_BIG_NET, animation.FISHING_CAGE,
            animation.FISHING_CRYSTAL_HARPOON, animation.FISHING_DRAGON_HARPOON, animation.FISHING_HARPOON, animation.FISHING_NET
            ]
        current_animation = self.api_m.get_animation_id()

        # check if the current animation is woodcutting
        if current_animation not in fishing_animation_list:
            return False
        return True
        

    def go_fish(self):
        """
        This will chop trees.
        Returns: void
        Args: None
        """
        self.is_runelite_focused()   # check if runelite is focused
        if not self.is_focused:
            self.log_msg("Runelite is not focused, switching window...")
            try:
                self.win.focus()
            except Exception:
                self.log_msg("Tried forcing focus, didn't work, will continue...")
            return

        while True: 
            self.idle_time = time.time()
            if fishing_spot := self.get_nearest_tag(clr.PINK):
                self.mouse.move_to(fishing_spot.random_point())
                self.check_text(fishing_spot, "Fishing", [clr.OFF_YELLOW])
                self.mouse.click()
                time.sleep(self.random_sleep_length())
                break
            else:
                self.log_msg("No fishing spot found...")
                time.sleep(self.random_sleep_length() * 3)
                if int(time.time() - self.idle_time) > 32:
                    self.adjust_camera(clr.PINK, 1)
                if int(time.time() - self.idle_time) > 60:
                    self.log_msg("No tree found in 60 seconds, quitting bot.")
                    self.stop()


    def bank_or_drop(self, deposit_slots):
        """
        This will either bank or drop items depending on the power_fishing setting.
        Returns: void
        Args: None"""
        if not self.power_fishing:
            end_time = time.time() + 5
            while time.time() < end_time:
                if not self.is_runelite_focused():   
                    self.log_msg("Inventory is full but runelight is not in focus, lets wait...")
                    time.sleep(self.random_sleep_length(.8, 1.2))
                    break
            self.open_bank()
            self.deposit_items(deposit_slots)
            self.close_bank()
        else:
            self.drop_all(skip_slots=[0])

    def check_equipment(self):
        """
        Stops script if no axe is equipped.
        Returns: none
        Args: None
        """
        fishing_tools = [ids.FISHING_ROD, ids.HARPOON, ids.FLY_FISHING_ROD,ids.SMALL_FISHING_NET, ids.LOBSTER_POT, ids.SMALL_FISHING_NET]
        fishing_bait = [ids.FISHING_BAIT, ids.FEATHER]

        if not self.api_m.get_if_item_in_inv(fishing_tools):
            self.log_msg("No fishing tool or bait in inventory...")
            self.stop()
        if self.style in ["Fly", "Bait"] and not self.api_m.get_if_item_in_inv(
            fishing_bait
        ):
            self.log_msg("No fishing bait in inventory...")
            self.stop()
        
