import time
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot
import utilities.api.item_ids as ids
import utilities.api.animation_ids as animation
import utilities.color as clr
import utilities.random_util as rd
import utilities.imagesearch as imsearch
import pyautogui as pag
from utilities.geometry import RuneLiteObject



class OSRSWDFishing(WillowsDadBot):
    def __init__(self):
        bot_title = "WillowsDad Fishing"
        description = """Fishes at supported locations."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 200
        self.take_breaks = True
        self.afk_train = True
        self.delay_min =0.37
        self.delay_max = .67
        self.style = "Cage"
        self.power_fishing = False
        self.fishing_tools = [ids.LOBSTER_POT]
        self.fishing_bait = []


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
                    self.fishing_tools = [ids.FLY_FISHING_ROD]
                    self.fishing_bait = [ids.FEATHER]
                elif options[option] == "Bait":
                    self.style = "Bait"
                    self.fishing_tools = [ids.FISHING_ROD]
                    self.fishing_bait = [ids.FISHING_BAIT]
                elif options[option] == "Harpoon":
                    self.style = "Harpoon"
                    self.fishing_tools = [ids.HARPOON, ids.DRAGON_HARPOON, ids.BARBTAIL_HARPOON]
                elif options[option] == "Net":
                    self.style = "Net"
                    self.fishing_tools = [ids.SMALL_FISHING_NET]
                elif options[option] == "Cage":
                    self.style = "Cage"
                    self.fishing_tools = [ids.LOBSTER_POT]
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

            try:
                # check if inventory is full
                if self.api_m.get_is_inv_full():
                    if not self.power_fishing:
                        self.walk_to_color(clr.YELLOW, 1)
                        self.bank_or_drop(deposit_slots)
                        self.check_equipment()
                        self.walk_to_color(clr.PINK, -1)
                    else:
                        self.bank_or_drop(deposit_slots)

                # Check if idle
                if self.api_m.get_is_player_idle():
                    self.log_msg("Fishing...")
                    self.go_fish()

                if self.is_fishing():
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


    def walk_to_color(self, color: clr, direction: int):
        """
        Walks to the bank.
        Returns: void
        Args:
            color: color of the tile to walk to
            direction: 1 for closest, -1 for furthest"""
        # find and click furthest or closest CYAN tile till "color" tile is found
        time_start = time.time()
        while True:
            if time.time() - time_start > 45:
                self.log_msg("We've been walking for 45 seconds, something is wrong...stopping.")
                self.stop()
            if found := self.get_nearest_tag(color):
                self.log_msg("Found next color.")
                break
            else:   # Below we are randomly choosing between the first or last 2 tiles in the list of tiles
                shapes = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)   # get all cyan tiles
                if shapes is []:
                    self.log_msg("No cyan tiles found, stopping.")
                    return
                shapes_sorted = sorted(shapes, key=RuneLiteObject.distance_from_rect_left)   # sort by distance from top left


                if len(shapes_sorted) == 1:
                    tile = shapes_sorted[0] if direction == 1 else shapes_sorted[-1]
                if (len(shapes_sorted) > 2):
                    if direction == 1:
                        tile = shapes_sorted[0] if rd.random_chance(.74) else shapes_sorted[1]
                    else:
                        tile = shapes_sorted[-1] if rd.random_chance(.74) else shapes_sorted[-2]

                self.mouse.move_to(tile.random_point(), mouseSpeed = "fast")
                self.mouse.click()
                time.sleep(self.random_sleep_length()*2)
        return
    
    
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
        self.deposit_ids = [ids.RAW_ANCHOVIES, ids.RAW_SHRIMPS, ids.RAW_LOBSTER, ids.RAW_TUNA, ids.RAW_SWORDFISH]

        if not self.power_fishing:
            self.face_north()
        
        # Setup Checks for axes and tagged objects
        self.check_equipment()

        if not self.get_nearest_tag(clr.YELLOW) and not self.get_nearest_tag(clr.PINK) and not self.power_fishing:
            self.log_msg("Did not see a bank(YELLOW) or a fishing spot (PINK) on screen, make sure they are tagged.")
            self.stop()
        if not self.get_nearest_tag(clr.CYAN) and not self.power_fishing:
            self.log_msg("Did not see any tiles tagged CYAN, make sure they are tagged so I can find my way to the bank.")
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
        return current_animation in fishing_animation_list
        

    def go_fish(self):
        """
        This will go fishing.
        Returns: void
        Args: None
        """
        self.is_runelite_focused()   # check if runelite is focused
        if not self.is_focused:
            self.log_msg("Runelite is not focused...")
        while True: 
            self.idle_time = time.time()
            if fishing_spot := self.get_nearest_tag(clr.PINK):
                self.mouse.move_to(fishing_spot.random_point())
                while not self.mouse.click(check_red_click=True):
                    if fishing_spot := self.get_nearest_tag(clr.PINK):
                        self.mouse.move_to(fishing_spot.random_point(), mouseSpeed = "fastest")
                time.sleep(self.random_sleep_length())
                break
            else:
                self.log_msg("No fishing spot found...")
                self.walk_to_color(clr.PINK, -1)
                if int(time.time() - self.idle_time) > 32:
                    self.adjust_camera(clr.PINK, 1)
                if int(time.time() - self.idle_time) > 60:
                    self.log_msg("No fishing spot found in 60 seconds, quitting bot.")
                    self.stop()


    def bank_or_drop(self, deposit_slots):
        """
        This will either bank or drop items depending on the power_fishing setting.
        Returns: void
        Args: None"""
        if not self.power_fishing:
            self.open_bank()
            time.sleep(self.random_sleep_length())
            self.check_deposit_all()
            self.deposit_items(deposit_slots, self.deposit_ids)
            time.sleep(self.random_sleep_length())
            self.close_bank()
            time.sleep(self.random_sleep_length())
        else:
            self.drop_all(skip_slots=[0])

    def check_equipment(self):
        """
        Stops script if no axe is equipped.
        Returns: none
        Args: None
        """
        if not self.api_m.get_if_item_in_inv(self.fishing_tools) and not self.api_m.get_is_item_equipped(self.fishing_tools):
            self.log_msg("No fishing tool or in inventory, please fix that...")
            self.stop()
        if self.style in ["Fly", "Bait"] and not self.api_m.get_if_item_in_inv(
            self.fishing_bait
        ):
            self.log_msg("No fishing bait in inventory...")
            self.stop()
        else:
            self.log_msg(f"Using {self.style}, and successfully found tools.")
        
