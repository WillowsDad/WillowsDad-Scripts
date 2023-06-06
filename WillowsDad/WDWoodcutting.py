import time
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot
import utilities.api.item_ids as ids
import utilities.api.animation_ids as animation
import utilities.color as clr
import utilities.random_util as rd
import utilities.imagesearch as imsearch
import pyautogui as pag


class OSRSWDWoodcutting(WillowsDadBot):
    def __init__(self):
        bot_title = "WD Woodcutting"
        description = """Chops wood and banks at supported locations."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 60
        self.take_breaks = True
        self.afk_train = True
        self.delay_min =0.37
        self.delay_max = .67
        self.log_type = ids.MAGIC_LOGS
        self.power_chopping = False
        self.dragon_special = False


    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        super().create_options()
        self.options_builder.add_dropdown_option("log_type", "What type of logs?", ["Normal", "Oak", "Willow", "Maple", "Yew", "Magic"])
        self.options_builder.add_checkbox_option("power_chopping", "Power Chopping? Drops everything in inventory.", [" "])
        self.options_builder.add_checkbox_option("dragon_special", "Use Dragon Axe Special?", [" "])

    def save_options(self, options: dict):
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)
        for option in options:
            if option == "log_type":
                if options[option] == "Normal":
                    self.log_type = ids.logs
                elif options[option] == "Oak":
                    self.log_type = ids.OAK_LOGS
                elif options[option] == "Willow":
                    self.log_type = ids.WILLOW_LOGS
                elif options[option] == "Maple":
                    self.log_type = ids.MAPLE_LOGS
                elif options[option] == "Yew":
                    self.log_type = ids.YEW_LOGS
                elif options[option] == "Magic":
                    self.log_type = ids.MAGIC_LOGS
            elif option == "power_chopping":
                self.power_chopping = options[option] != []
            elif option == "dragon_special":
                self.dragon_special = options[option] != []
            else:
                self.log_msg(f"Unexpected option: {option}")

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg(f"Bot will wait between {self.delay_min} and {self.delay_max} seconds between actions.")
        self.log_msg(f"Bot will{'' if self.power_chopping else ' not'} power chop.")
        self.log_msg(f"Bot will cut {options['log_type']} logs.")
        self.log_msg(f"Bot will{'' if self.dragon_special else ' not'} use dragon axe special.")
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
            deposit_slots = self.api_m.get_first_occurrence(self.deposit_ids)
            self.roll_chance_passed = False
            self.spec_energy = self.get_special_energy()
            try:
                # check if inventory is full
                if self.api_m.get_is_inv_full():
                    self.bank_or_drop(deposit_slots)

                # Check if idle
                if self.api_m.get_is_player_idle():

                    self.pick_up_nests()

                    if self.spec_energy >= 100 and self.dragon_special:
                        self.activate_special()
                        self.log_msg("Dragon Axe Special Activated")

                    self.log_msg("Chopping trees...")
                    self.chop_trees(percentage)

                if self.is_woodcutting():
                    if self.afk_train and self.is_runelite_focused():
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
        self.deposit_ids = [ids.BIRD_NEST, ids.BIRD_NEST_5071, ids.BIRD_NEST_5072, ids.BIRD_NEST_5073, ids.BIRD_NEST_5074, ids.BIRD_NEST_5075, ids.BIRD_NEST_7413, ids.BIRD_NEST_13653, ids.BIRD_NEST_22798, ids.BIRD_NEST_22800, self.log_type]
        
        # Setup Checks for axes and tagged objects
        self.check_axe()

        if not self.power_chopping:
            if not self.get_nearest_tag(clr.YELLOW):
                found = self.adjust_camera(clr.YELLOW)
                if not found:
                    self.log_msg("Bank booths should be tagged with yellow, and in screen view. Please fix this.")
                    self.stop()
            self.check_bank_settings()
            

        if not self.get_nearest_tag(clr.PINK):
            found = self.adjust_camera(clr.PINK)
            if not found:
                self.log_msg("Trees should be tagged with pink, and in screen view. Please fix this.")
                self.stop()
        


    def check_bank_settings(self):
        """Checks if the bank booth is set to deposit all items.
            Args:
                None
            Returns:
                None"""
        return
        # self.open_bank()
        # time.sleep(self.random_sleep_length())
        # self.close_bank()


    def pick_up_nests(self):

        if self.api_m.get_is_inv_full():
            return
        """Picks up loot while there is loot on the ground"""
        while self.pick_up_loot(["Bird nest", "Clue nest (easy)", "Clue nest (medium)","Clue nest (hard)","Clue nest (elite)"]):
            curr_inv = len(self.api_s.get_inv())
            self.log_msg("Picking up loot...")
            for _ in range(5):  # give the bot 5 seconds to pick up the loot
                if len(self.api_s.get_inv()) != curr_inv:
                    time.sleep(self.random_sleep_length())
                    break
                time.sleep(self.random_sleep_length(.8, 1.3))


    def is_woodcutting(self):
        """
        This will check if the player is currently woodcutting.
        Returns: boolean
        Args: None
        """
        # get the current player animation
        woodcutting_animation_list = [animation.WOODCUTTING_3A_AXE, animation.WOODCUTTING_BRONZE, animation.WOODCUTTING_IRON, animation.WOODCUTTING_STEEL, animation.WOODCUTTING_BLACK, animation.WOODCUTTING_MITHRIL, animation.WOODCUTTING_ADAMANT, animation.WOODCUTTING_RUNE, animation.WOODCUTTING_DRAGON]
        current_animation = self.api_m.get_animation_id()

        # check if the current animation is woodcutting
        return current_animation in woodcutting_animation_list
        

    def chop_trees(self, percentage):
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
            if tree := self.get_nearest_tag(clr.PINK):
                self.mouse.move_to(tree.random_point())
                self.mouse.click()
                time.sleep(self.random_sleep_length())
                break
            else:
                self.log_msg("No tree found, waiting for a tree to spawn...")
                if safety := self.get_nearest_tag(clr.CYAN):
                    self.mouse.move_to(safety.random_point())
                    self.mouse.click()
                    time.sleep(self.random_sleep_length())
                time.sleep(self.random_sleep_length() * 3)
                if int(time.time() - self.idle_time) > 32:
                    self.adjust_camera(clr.PINK, 1)
                if int(time.time() - self.idle_time) > 60:
                    self.log_msg("No tree found in 60 seconds, quitting bot.")
                    self.stop()


    def bank_or_drop(self, deposit_slots):
        """
        This will either bank or drop items depending on the power_chopping setting.
        Returns: void
        Args: None"""
        if not self.power_chopping:
            end_time = time.time() + 5
            while time.time() < end_time:
                if not self.is_runelite_focused():   
                    self.log_msg("Inventory is full but runelight is not in focus, lets wait...")
                    time.sleep(self.random_sleep_length(.8, 1.2))
                    break
            self.open_bank()
            time.sleep(self.random_sleep_length())
            self.check_deposit_all()
            self.deposit_items(deposit_slots, self.deposit_ids)
            time.sleep(self.random_sleep_length())
            self.close_bank()
        else:
            self.drop_all()


    def check_axe(self):
        """
        Stops script if no axe is equipped.
        Returns: none
        Args: None
        """
        axe_ids = [ids.BRONZE_AXE, ids.IRON_AXE, ids.STEEL_AXE, ids.BLACK_AXE, ids.MITHRIL_AXE, ids.ADAMANT_AXE, ids.RUNE_AXE, ids.DRAGON_AXE, ids.INFERNAL_AXE, ids.DRAGON_PICKAXE, ids.CRYSTAL_AXE]

        if not self.api_m.get_is_item_equipped(ids.DRAGON_AXE) and self.dragon_special:
            self.log_msg("You need dragon axe equipped according to your settings, quitting bot.")
            self.stop()
        time.sleep(self.random_sleep_length())
        if not self.api_m.get_is_item_equipped(
            axe_ids
        ) and not self.api_m.get_if_item_in_inv(axe_ids):
            self.log_msg("No axe in inventory, or equipped. Please get an axe and start script again")
            self.stop()
        
