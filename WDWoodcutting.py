import time
import utilities.api.item_ids as ids
import utilities.api.animation_ids as animation
import utilities.color as clr
from utilities.geometry import RuneLiteObject
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
import utilities.imagesearch as imsearch
import random
import pyautogui as pag
import threading


class OSRSWDWoodcutting(OSRSBot):
    """This bot will cut trees and bank the logs if the bank is tagged and within render distance.
    Assumes: 
        Axe is equipped, or in inventory
        Bank is tagged YELLOW
        Trees are tagged GREEN
        Trees and Bank are within screen view
    Settings:
        AFK Training: Will 'Alt + Tab' to another window anytime you are woodcutting.
        Take Breaks: Will roll a chance for a break every 15 seconds, chance increases by 1% each minute."""
    def __init__(self):
        bot_title = "WillowsDad Woodcutting"
        description = """Chops wood and banks at supported locations."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 60
        self.take_breaks = True
        self.afk_train = True
        self.power_chopping = False
        self.log_type = ids.MAGIC_LOGS
        self.delay_min =0.37
        self.delay_max = .67
        self.dragon_special = False

    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_dropdown_option("log_type", "What type of logs?", ["Normal", "Oak", "Willow", "Maple", "Yew", "Magic"])
        self.options_builder.add_checkbox_option("afk_train", "Train like you're afk on another tab?", [" "])
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_checkbox_option("power_chopping", "Power Chopping? Drops everything in inventory.", [" "])
        self.options_builder.add_checkbox_option("dragon_special", "Use Dragon Axe Special?", [" "])
        self.options_builder.add_slider_option("delay_min", "How long to take between actions (min) (MiliSeconds)?", 300,3000)
        self.options_builder.add_slider_option("delay_max", "How long to take between actions (max) (MiliSeconds)?", 650,3000)

    def save_options(self, options: dict):
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "afk_train":
                self.afk_train = options[option] != []
            elif option == "log_type":
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
            elif option == "delay_min":
                self.delay_min = options[option]/1000
            elif option == "delay_max":
                self.delay_max = options[option]/1000
            elif option == "dragon_special":
                self.dragon_special = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg(f"Bot will{'' if self.power_chopping else ' not'} power chop.")
        self.log_msg(f"Bot will cut {options['log_type']} logs.")
        self.log_msg(f"Bot will wait between {self.delay_min} and {self.delay_max} seconds between actions.")
        self.log_msg(f"Bot will{'' if self.dragon_special else ' not'} use dragon axe special.")
        self.log_msg("Options set successfully.")
        self.options_set = True

 
    class StoppableThread(threading.Thread):
        """Thread class with a stop() method. The thread itself has to check.
            Useful for looking for a tag while main thread is doing something else."""
        def __init__(self, target=None, args=()):
            super().__init__(target=target, args=args)
            self._stop_event = threading.Event()

        def stop(self):
            self._stop_event.set()

        def stopped(self):
            return self._stop_event.is_set()


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
            deposit_slots = self.api_m.get_inv_item_index(self.deposit_ids)
            self.roll_chance_passed = False
            self.spec_energy = self.get_special_energy()

            # check if inventory is full
            if self.api_m.get_is_inv_full():

                self.bank_or_drop(deposit_slots)

            # Check if idle
            if self.api_m.get_is_player_idle():

                self.pick_up_nests()

                if self.spec_energy >= 100 and self.dragon_special:
                    self.activate_special()

                self.chop_trees(percentage)

            if self.afk_train and self.is_woodcutting():

                self.go_afk(percentage)
     
                
            # -- End bot actions --
            self.check_break(runtime, percentage, minutes_since_last_break, seconds, deposit_slots)
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
        self.end_time = self.running_time * 60
        self.is_focused = self.is_runelite_focused()
        self.roll_chance_passed = False
        self.force_count = 0
        self.last_progress = 0
        self.idle_time = 0
        self.breaks_skipped = 0
        self.deposit_ids = [ids.BIRD_NEST, ids.BIRD_NEST_5071, ids.BIRD_NEST_5072, ids.BIRD_NEST_5073, ids.BIRD_NEST_5074, ids.BIRD_NEST_5075, ids.BIRD_NEST_7413, ids.BIRD_NEST_13653, ids.BIRD_NEST_22798, ids.BIRD_NEST_22800, self.log_type]
        self.start_time = time.time()
        self.last_break = time.time()
        self.multiplier = 1
        self.loop_count = 0
        self.api_m = MorgHTTPSocket()
        self.spec_energy = self.get_special_energy()
        self.last_runtime = 0

        if self.dragon_special:
            self.check_axe()
        

        if not self.get_nearest_tag(clr.YELLOW) and not self.power_chopping:
            found = self.adjust_camera(clr.YELLOW)
            if not found:
                self.log_msg("Bank booths should be tagged with yellow, and in screen view. Please fix this.")
                self.stop()

        if not self.get_nearest_tag(clr.PINK):
            found = self.adjust_camera(clr.PINK)
            if not found:
                self.log_msg("Trees should be tagged with pink, and in screen view. Please fix this.")
                self.stop()


    def activate_special(self):
        """Activates the special attack of the equipped weapon.
            Args:
                None
            Returns:
                None"""
        self.mouse.move_to(self.win.spec_orb.random_point())
        time.sleep(self.random_sleep_length(.8, 1.2))
        self.mouse.click()
        time.sleep(self.random_sleep_length())


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


    def bank_each_item(self, slot_list):
        """
        Clicks once on each unique item. 
        Bank must be open already.
        Deposit "All" must be selected.

        Args:
            slot_list: list of inventory slots to deposit items from
        Returns:
            None/Void
        """
        try_count = 0

        # Make sure bank is open
        if not self.is_bank_open():
            self.log_msg("Bank is not open, cannot deposit items. Quitting bot...")
            self.stop()

        # move mouse each slot and click to deposit all
        for slot in slot_list:
            self.mouse.move_to(self.win.inventory_slots[slot].random_point())
            time.sleep(self.random_sleep_length(.8, 1.3))
            if not self.mouseover_text(contains=["All"]):
                self.log_msg("Bank deposit settings are not set to 'Deposit All', or something is wrong, trying again")
                try_count += 1
            else:
                self.mouse.click()
                time.sleep(self.random_sleep_length())
            if try_count > 5:
                self.log_msg(f"Tried to deposit {try_count} times, quitting bot so you can fix it...")
                self.stop()

        # we now exit bank by sending the escape key
        if not self.get_nearest_tag(clr.PINK) and rd.random_chance(.78):
            pag.press("esc")
        self.random_sleep_length()
        
        return
    


    def is_bank_open(self):
        """Makes sure bank is open, if not, opens it
        Returns:
            True if bank is open, False if not
        Args:
            None"""
        Desposit_all_img = imsearch.BOT_IMAGES.joinpath("bank", "bank_all.png")
        end_time = time.time() + self.random_sleep_length()

        while (time.time() < end_time):
            if deposit_btn := imsearch.search_img_in_rect(Desposit_all_img, self.win.game_view):
                return True
            time.sleep(.1)
        return False
    

    def random_sleep_length(self, delay_min=0, delay_max=0):
        """Returns a random float between min and max"""
        if delay_min == 0:
            delay_min = self.delay_min
        if delay_max == 0:
            delay_max = self.delay_max
        return rd.fancy_normal_sample(delay_min, delay_max)


    def adjust_camera(self, color, timeout=4):
        """
        Adjusts the camera to look for a specific color. Times out after searching 4 seconds
        Args:
            color: color to look for
        Returns:
            None/Void"""
        random_x = random.randint(90, 180) 
        start_time = time.time() # lets make sure we don't wait too long

        # chance for x to be negative
        if random.randint(0, 1) == 1:
            random_x *= -1
        random_xy = (random_x, 0)  # tuple of random x and y

        # call the camera function on a new thread
        camera_thread = self.StoppableThread(target=self.move_camera, args=(random_xy))
        camera_thread.start()   

        while not self.get_nearest_tag(color):
            time_searching = time.time() - start_time

            if time_searching > timeout:
                self.log_msg(f"Could not find highlighted color in {timeout} seconds...")
                camera_thread.stop()    
                return False
            time.sleep(self.random_sleep_length(.35, .65))
        camera_thread.stop()
        time.sleep(self.random_sleep_length())
        return True
            

    def choose_bank(self):
        """
        Has a small chance to choose the second closest bank to the player.
            Returns: bank rectangle or none if no banks are found
            Args: None

        """
        if banks := self.get_all_tagged_in_rect(self.win.game_view, clr.YELLOW):
            banks = sorted(banks, key=RuneLiteObject.distance_from_rect_center)

            if len(banks) == 1:
                return banks[0]
            if (len(banks) > 1):
                return banks[0] if rd.random_chance(.74) else banks[1]
        else:
            self.log_msg("No banks found, trying to adjust camera...")
            self.adjust_camera(clr.YELLOW)
            return (self.choose_bank())


    def take_menu_break(self):  # sourcery skip: extract-duplicate-method
        """
        This will take a random menu break [Skills, Combat].]
        Returns: void
        Args: None
        """
        # random amount of seconds to teak a break
        break_time = random.uniform(1, 15)

        if rd.random_chance(.7):
            self.log_msg("Taking a Sklls Tab break...")
            self.mouse.move_to(self.win.cp_tabs[1].random_point())
            time.sleep(self.random_sleep_length())
            if self.mouseover_text(contains="Skills"):
                self.mouse.click()
                self.mouse.move_to(self.win.control_panel.random_point())
                time.sleep(break_time)

                # go back to inventory
                self.mouse.move_to(self.win.cp_tabs[3].random_point())
                time.sleep(self.random_sleep_length())
                if self.mouseover_text(contains="Inventory"):
                    self.mouse.click()
            else:
                self.log_msg("Skills tab not found, break function didn't work...")
                self.stop()
        else:
            self.log_msg("Taking an Equipment menu break...")
            self.mouse.move_to(self.win.cp_tabs[4].random_point())
            time.sleep(self.random_sleep_length())
            if self.mouseover_text(contains="Worn"):
                self.mouse.click()

                self.mouse.move_to(self.win.control_panel.random_point())
                time.sleep(break_time)

                # go back to inventory
                self.mouse.move_to(self.win.cp_tabs[3].random_point())
                if self.mouseover_text(contains="Inventory"):
                    self.mouse.click()

            else:
                self.log_msg("Combat tab not found, break function didn't work...")
                self.stop()
        return
    

    def take_random_break(self, minutes_since_last_break, deposit_slots):
        """This will randomly choose a break type and take it. The shorter time since last break, the more likely it is to be a menu break.
        Returns: void
        Args: minutes_since_last_break (int) - the number of minutes passed since the last break."""
        # break type is a random choice from list
        break_type = random.choice(["menu", "break"])

        if break_type == "menu":
            self.log_msg("Taking a menu break...")
            self.take_menu_break()

        if break_type == "break":
            self.log_msg("Taking a break...")

            # check if player is idle
            while not self.api_m.get_is_player_idle():
                self.log_msg("Player is not idle, waiting for player to be idle before taking break...")
                time.sleep(self.random_sleep_length(3,8))

            if minutes_since_last_break > 15:
                self.take_break(15, 120)
            else:
                self.take_break()


    def find_bank(self, deposit_slots):
        """
        This will bank all logs in the inventory.
        Returns: 
            void
        Args: 
            deposit_slots (int) - Inventory position of each different item to deposit.
        """
        search_tries = 1

         # Time to bank
        self.log_msg("Banking...")
        # move mouse one of the closes 2 banks

        bank = self.choose_bank()

        # move mouse to bank and click
        self.mouse.move_to(bank.random_point())
        time.sleep(self.random_sleep_length(.8, 1.2))

        # search up to 5 times for mouseover text "bank"
        while not self.mouseover_text(contains="Bank"):
            self.log_msg(f"Bank not found, trying again. Try #{search_tries}.")
            self.mouse.move_to(bank.random_point())
            time.sleep(self.random_sleep_length())

            if search_tries > 5:
                self.log_msg(f"Did not see 'Bank' in mouseover text after {search_tries} searches, quitting bot so you can fix it...")
                self.stop()
            search_tries += 1

        self.mouse.click()
        time.sleep(self.random_sleep_length())

        wait_time = time.time()
        while not self.api_m.get_is_player_idle():
            # if we waited for 10 seconds, break out of loop
            if time.time() - wait_time > 15:
                self.log_msg("We clicked on the bank but player is not idle after 10 seconds, something is wrong, quitting bot.")
                self.stop()
            time.sleep(self.random_sleep_length(.8, 1.3))
            
        # if bank is open, deposit all 
        self.bank_each_item(deposit_slots)

        return


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


    def switch_window(self):
        """
        This will switch the window to runelite.
        Returns: void
        Args: None
        """
        # Get the currently focused window
        current_window = pag.getActiveWindow()

        self.log_msg(f"Current window: {current_window.title}, switching now...")

        pag.hotkey("alt", "tab")
        time.sleep(self.random_sleep_length())

        new_window = pag.getActiveWindow()
        self.log_msg(f"Current window: {new_window.title}.")

        self.is_focused = "RuneLite" in new_window.title
        if current_window.title == new_window.title:
            self.log_msg("Window not switched, something is wrong, quitting bot.")
            self.stop()

        time.sleep(self.random_sleep_length())


    def is_woodcutting(self):
        """
        This will check if the player is currently woodcutting.
        Returns: boolean
        Args: None
        """
        # get the current player animation
        woodcutting_animation_list = [animation.WOODCUTTING_3A_AXE, animation.WOODCUTTING_BRONZE, animation.WOODCUTTING_IRON, animation.WOODCUTTING_STEEL, animation.WOODCUTTING_BLACK, animation.WOODCUTTING_MITHRIL, animation.WOODCUTTING_ADAMANT, animation.WOODCUTTING_RUNE, animation.WOODCUTTING_DRAGON]
        api_m = MorgHTTPSocket()
        current_animation = api_m.get_animation_id()

        # check if the current animation is woodcutting
        return current_animation in woodcutting_animation_list
        

    def check_break(self, runtime, percentage, minutes_since_last_break, seconds, deposit_slots):
        """
        This will roll the chance of a break.
        Returns: void
        Args:
            runtime: int
            percentage: float
            minutes_since_last_break: int
            seconds: int
            deposit_slots: list
            self.roll_chance_passed: boolean"""
        if runtime % 15 == 0 and runtime != self.last_runtime:
            if runtime % 60 == 0 or self.roll_chance_passed:   # every minute log the chance of a break
                self.log_msg(f"Chance of random break is {round(percentage * 100)}%")

            self.roll_break(
                percentage, minutes_since_last_break, seconds, deposit_slots
            )

        elif self.roll_chance_passed:
            self.log_msg(f"Chance of random break is {round(percentage * 100)}%")

            self.roll_break(
                percentage, minutes_since_last_break, seconds, deposit_slots
            )
        self.last_runtime = runtime



    def roll_break(self, percentage, minutes_since_last_break, seconds, deposit_slots):
        if (
            rd.random_chance(probability=percentage / (1 if self.afk_train else 4))   # when afk theres weird timing issues so we divide by 4 if not afk
            and self.take_breaks
        ):
            self.reset_timer(
                minutes_since_last_break, seconds, percentage, deposit_slots
            )
        self.multiplier += .25  # increase multiplier for chance of random break, we want + 1% every minute 
        self.roll_chance_passed = False



    def reset_timer(self, minutes_since_last_break, seconds, percentage, deposit_slots):
        self.log_msg(f"Break time, last break was {minutes_since_last_break} minutes and {seconds} seconds ago. \n Chance of random break was {round(percentage * 100)}%")

        self.last_break = time.time()   # reset last break time
        self.multiplier = 1    # reset multiplier

        self.take_random_break(minutes_since_last_break, deposit_slots)


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

        self.log_msg("Looking for a tree...")

        while True: 
            self.idle_time = time.time()
            if tree := self.get_nearest_tag(clr.PINK):
                self.mouse.move_to(tree.random_point())
                time.sleep(self.random_sleep_length())
                self.mouseover_text(contains="Chop")
                self.mouse.click()
                time.sleep(self.random_sleep_length())
                break
            else:
                self.log_msg("No tree found, waiting for a tree to spawn...")
                if not self.power_chopping:
                    self.adjust_camera(clr.PINK, 1)
                time.sleep(self.random_sleep_length() * 3)
            if int(time.time() - self.idle_time) > 40:
                self.log_msg("No tree found in 60 seconds, quitting bot.")
                self.stop()



    def go_afk(self, percentage):
        """
        This will go afk for a random amount of time.
        Returns: void
        Args: percentage
        """
        afk__start_time = time.time()  

        self.log_msg("Player is woodcutting, lets go afk...")
        if self.is_focused:
            self.switch_window()
        self.breaks_skipped = 0
        chopping_time = 0

        while self.is_woodcutting():
            time.sleep(self.random_sleep_length())
            chopping_time = int(time.time() - afk__start_time)
            self.is_runelite_focused()
            self.breaks_skipped = chopping_time // 15

        if self.breaks_skipped > 0:
            self.roll_chance_passed = True
            self.multiplier += self.breaks_skipped * .25
            self.log_msg(f"Skipped {self.breaks_skipped} break rolls while afk, percentage chance is now {round(percentage * 100)}%")


    def bank_or_drop(self, deposit_slots):
        if not self.power_chopping:
            end_time = time.time() + 5
            while time.time() < end_time:
                if not self.is_runelite_focused():   
                    self.log_msg("Inventory is full but runelight is not in focus, lets wait...")
                    time.sleep(self.random_sleep_length(.8, 1.2))
                    self.win.focus()
                    break
            self.find_bank(deposit_slots)
        else:
            self.log_msg("Inventory is full, dropping everything...")
            self.drop_all()


    def check_axe(self):
        """
        Stops script if no axe is equipped.
        Returns: none
        Args: None
        """
        if not self.api_m.get_is_item_equipped(ids.DRAGON_AXE):
            self.log_msg("You need dragon axe equipped according to your settings, quitting bot.")
            self.stop()
