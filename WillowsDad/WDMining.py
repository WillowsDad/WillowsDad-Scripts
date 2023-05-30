import random
import time
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot
import utilities.api.item_ids as ids
import utilities.api.animation_ids as animation
import utilities.color as clr
import utilities.random_util as rd
import utilities.imagesearch as imsearch
import pyautogui as pag
from utilities.geometry import RuneLiteObject
import utilities.game_launcher as launcher
from pathlib import Path





class OSRSWDMining(WillowsDadBot):
    def __init__(self):
        bot_title = "WillowsDad Mining"
        description = """Mines at supported locations."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 200
        self.take_breaks = True
        self.afk_train = True
        self.delay_min =0.37
        self.delay_max = .67
        self.ores = ids.ores
        self.power_Mining = False
        self.Mining_tools = ids.pickaxes
        self.dragon_special = False
        self.location = "Mining Guild"


    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        super().create_options()
        self.options_builder.add_checkbox_option("power_Mining", "Power Mining? Drops everything in inventory.", [" "])
        self.options_builder.add_checkbox_option("dragon_special", "Use Dragon Pickaxe Special?", [" "])
        self.options_builder.add_checkbox_option("location", "Location?", ["Varrock East","Mining Guild"])

    def save_options(self, options: dict):
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)
        for option in options:
            if option == "power_Mining":
                self.power_Mining = options[option] != []
            elif option == "dragon_special":
                self.dragon_special = options[option] != []
            elif option == "location":
                self.location = options[option]
            else:
                self.log_msg(f"Unexpected option: {option}")

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg(f"Bot will wait between {self.delay_min} and {self.delay_max} seconds between actions.")
        self.log_msg(f"Bot will{'' if self.power_Mining else ' not'} power mine.")
        self.log_msg("Options set successfully.")
        self.options_set = True


    def launch_game(self):
    
        # If playing RSPS, change `RuneLite` to the name of your game
        if launcher.is_program_running("RuneLite"):
            self.log_msg("RuneLite is already running. Please close it and try again.")
            return
        
        settings = Path(__file__).parent.joinpath("WDMiner.properties")
        launcher.launch_runelite(
            properties_path=settings, 
            game_title=self.game_title, 
            use_profile_manager=True, 
            profile_name="WDMiner", 
            callback=self.log_msg)

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

            try:
                while not self.api_m.get_is_inv_full():
                    if self.api_m.get_run_energy() == 10000:
                        run = imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("run_enabled.png"), self.win.run_orb.scale(3,3))
                        if run is None:
                            self.mouse.move_to(self.win.run_orb.random_point())
                            self.mouse.click()
                            time.sleep(self.random_sleep_length())
                    if Mining_spot := self.get_nearest_tag(clr.PINK):
                        self.go_mining()
                        deposit_slots = self.api_m.get_first_occurrence(self.deposit_ids)
                    else:
                        self.walk_to_mine()


                if not self.power_Mining:
                    self.walk_to_bank()
                    self.bank_or_drop(deposit_slots)
                    self.check_equipment()
                    self.walk_to_mine()

                else:
                    self.bank_or_drop(deposit_slots)


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


    def walk_to_bank(self):
        if self.location[0] == "Varrock East":
            self.walk_vertical(img=self.WILLOWSDAD_IMAGES.joinpath("varrock_east_minimap.png"), direction=1)
            self.walk_horizontal(color=clr.YELLOW, direction=1)
        elif self.location[0] == "Mining Guild":
            self.walk_horizontal(color=clr.YELLOW, direction=1)



    def walk_to_mine(self):
        if self.location[0] == 'Varrock East':
            self.walk_diagonal(color=clr.PINK, direction=-1)
        elif self.location[0] == "Mining Guild":
            self.walk_horizontal(color=clr.PINK, direction=-1)
    
    
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
        self.deposit_ids = self.ores
        self.deposit_ids.extend([ids.UNCUT_DIAMOND, ids.UNCUT_DRAGONSTONE, ids.UNCUT_EMERALD, ids.UNCUT_RUBY, ids.UNCUT_SAPPHIRE, ids.UNIDENTIFIED_MINERALS])


        # Setup Checks for pickaxes and tagged objects
        self.check_equipment()

        if not self.power_Mining:
            self.face_north()

        if not self.get_nearest_tag(clr.YELLOW) and not self.get_nearest_tag(clr.PINK) and not self.power_Mining and not self.get_nearest_tag(clr.CYAN):
            self.log_msg("Did not see a bank(YELLOW) or a Mining spot (PINK) on screen, or a tile (CYAN) make sure they are tagged.")
            self.adjust_camera(clr.YELLOW)
            self.stop()
        if not self.get_nearest_tag(clr.CYAN) and not self.power_Mining:
            self.log_msg("Did not see any tiles tagged CYAN, make sure they are tagged so I can find my way to the bank.")
            self.stop()
        
        self.check_bank_settings()


    def face_north(self):
        """Faces the player north.
            Args:
                None
            Returns:
                None"""
        self.mouse.move_to(self.win.compass_orb.random_point(), mouseSpeed = "fastest")
        self.mouse.click()


    def check_bank_settings(self):
        """Checks if the bank booth is set to deposit all items.
            Args:
                None
            Returns:
                None"""
        # self.open_bank()
        # self.close_bank()


    def is_Mining(self):
        """
        This will check if the player is currently woodcutting.
        Returns: boolean
        Args: None
        """
        # get the current player animation
        Mining_animation_list = [animation.MINING_ADAMANT_PICKAXE, animation.MINING_BLACK_PICKAXE, animation.MINING_BRONZE_PICKAXE, animation.MINING_DRAGON_PICKAXE, animation.MINING_IRON_PICKAXE, animation.MINING_MITHRIL_PICKAXE, animation.MINING_RUNE_PICKAXE, animation.MINING_STEEL_PICKAXE]
        current_animation = self.api_m.get_animation_id()

        # check if the current animation is woodcutting
        return current_animation in Mining_animation_list
        

    def go_mining(self):
        """
        This will go Mining.
        Returns: void
        Args: None
        """
        self.breaks_skipped = 0
        afk_time = 0
        afk__start_time = time.time() 

        self.is_runelite_focused()   # check if runelite is focused
        if not self.is_focused:
            self.log_msg("Runelite is not focused...")
        while not self.api_m.get_is_inv_full(): 
            if self.get_special_energy() >= 100 and self.dragon_special:
                self.activate_special()
                self.log_msg("Dragon Pickaxe Special Activated")
            self.idle_time = time.time()
            afk_time = int(time.time() - afk__start_time)
            if Mining_spot := self.get_nearest_tag(clr.PINK):
                self.mouse.move_to(Mining_spot.random_point())
                while not self.mouse.click(check_red_click=True):
                    if Mining_spot := self.get_nearest_tag(clr.PINK):
                        self.mouse.move_to(Mining_spot.random_point())
                self.api_m.wait_til_gained_xp("Mining", timeout=int(self.random_sleep_length() * 20))

            else:
                if int(time.time() - self.idle_time) > 10:
                    if self.get_nearest_tag(clr.CYAN):
                        self.mouse.move_to(self.get_nearest_tag(clr.CYAN).random_point())
                        self.mouse.click()
                    time.sleep(self.random_sleep_length())
                if int(time.time() - self.idle_time) > 32:
                    self.adjust_camera(clr.PINK, 1)
                if int(time.time() - self.idle_time) > 60:
                    self.log_msg("No Mining spot found in 60 seconds, quitting bot.")
                    self.stop()
            self.breaks_skipped = afk_time // 15

        if self.breaks_skipped > 0:
            self.roll_chance_passed = True
            self.multiplier += self.breaks_skipped * .25
            self.log_msg(f"Skipped {self.breaks_skipped} break rolls while mining.")
        return


    def bank_or_drop(self, deposit_slots):
        """
        This will either bank or drop items depending on the power_Mining setting.
        Returns: void
        Args: None"""
        if not self.power_Mining:
            self.open_bank()
            time.sleep(self.random_sleep_length()/2)
            self.check_deposit_all()
            self.deposit_items(deposit_slots, self.deposit_ids)
            time.sleep(self.random_sleep_length()/2)
            self.close_bank()
        else:
            self.drop_all(skip_slots=self.api_m.get_inv_item_indices(self.Mining_tools))

    def check_equipment(self):
        """
        Stops script if no axe is equipped.
        Returns: none
        Args: None
        """
        if not self.api_m.get_if_item_in_inv(self.Mining_tools) and not self.api_m.get_is_item_equipped(self.Mining_tools):
            self.log_msg("No Mining tool or in inventory, please fix that...")
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
            if shapes is []:
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
    

    def walk_diagonal(self, direction: int, color: clr = None, timeout: int = 60, img: Path = None):
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
            if shapes is []:
                self.log_msg("No cyan tiles found, stopping.")
                return

            # Sort the cyan tiles based on their distance from the top-center
            if len(shapes) > 1:
                shapes_sorted = sorted(shapes, key=RuneLiteObject.distance_from_rect_top)
                self.mouse.move_to(shapes_sorted[-1 if direction == -1 else random.randint(0,1)].scale(3,3).random_point(), mouseSpeed = "fastest")
            else:
                self.mouse.move_to(shapes_sorted[-1 if direction == -1 else 0].scale(3,3).random_point(), mouseSpeed = "fastest")

            # Click on the selected tile and wait for a random duration between 0.35 and 0.67 seconds
            self.mouse.click()
            time.sleep(self.random_sleep_length(.67, 1.24))

        return
        
