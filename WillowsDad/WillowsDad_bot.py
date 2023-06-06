import datetime
import time
from model.osrs.osrs_bot import OSRSBot
import utilities.color as clr
from utilities.geometry import Rectangle, RuneLiteObject, Point
import utilities.random_util as rd
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
import utilities.imagesearch as imsearch
import random
import pyautogui as pag
import threading
from abc import ABCMeta, abstractmethod
from pathlib import Path
import utilities.game_launcher as launcher
from typing import Union, List


# New class WillowsDad_bot
class WillowsDadBot(OSRSBot, launcher.Launchable, metaclass=ABCMeta):
    """Willows Dad Bot class."""

    # Update the BOT_IMAGES path
    WILLOWSDAD_IMAGES = Path(__file__).parent.joinpath("WillowsDad_images")

    def __init__(self, bot_title, description) -> None:
        super().__init__(bot_title, description)


    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 360)
        self.options_builder.add_checkbox_option("afk_train", "Train like you're afk on another tab?", [" "])
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_slider_option("delay_min", "How long to take between actions (min) (MiliSeconds)?", 300,1200)
        self.options_builder.add_slider_option("delay_max", "How long to take between actions (max) (MiliSeconds)?", 350,1200)


    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "afk_train":
                self.afk_train = options[option] != []
            elif option == "delay_min":
                self.delay_min = options[option]/1000
            elif option == "delay_max":
                self.delay_max = options[option]/1000


    def launch_game(self):
    
        # If playing RSPS, change `RuneLite` to the name of your game
        if launcher.is_program_running("RuneLite"):
            self.log_msg("RuneLite is already running. Please close it and try again.")
            return
        
        settings = Path(__file__).parent.joinpath("WillowsDad.properties")
        launcher.launch_runelite(
            properties_path=settings, 
            game_title=self.game_title, 
            use_profile_manager=True, 
            profile_name="WillowsDad", 
            callback=self.log_msg)


    def setup(self):
        """Sets up loop variables, checks for required items, and checks location.
        This will ideally stop the bot from running if it's not setup correctly.
        * To-do: Add functions to check for required items, bank setup and locaiton.
        Args:
            None
        Returns:
            None"""
        self.start_time = time.time()
        self.end_time = self.running_time * 60
        self.is_focused = self.is_runelite_focused()
        self.roll_chance_passed = False
        self.last_progress = 0
        self.breaks_skipped = 0
        self.last_break = time.time()
        self.multiplier = 1
        self.loop_count = 0
        self.api_m = MorgHTTPSocket()
        self.api_s = StatusSocket()
        self.spec_energy = self.get_special_energy()
        self.last_runtime = 0
        self.safety_squares = self.get_all_tagged_in_rect(self.win.game_view ,clr.CYAN)
        self.deposit_all_red_button = None
        self.exit_btn = None



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


    def activate_special(self):
        """Activates the special attack of the equipped weapon.
            Args:
                None
            Returns:
                None"""
        self.mouse.move_to(self.win.spec_orb.random_point())
        self.mouse.click()
        time.sleep(self.random_sleep_length())



    def sleep(self, percentage):
        """Sleeps for a random amount of time between the min and max delay. While player is doing an action.
            Args:
                None
            Returns:
                None"""
        self.breaks_skipped = 0
        afk_time = 0
        afk__start_time = time.time() 

        while not self.api_m.get_is_player_idle():
            time.sleep(self.random_sleep_length(.65, 2.2))
            afk_time = int(time.time() - afk__start_time)
            self.is_runelite_focused()
            self.breaks_skipped = afk_time // 15

        if self.breaks_skipped > 0:
            self.roll_chance_passed = True
            self.multiplier += self.breaks_skipped * .25
            self.log_msg(f"Skipped {self.breaks_skipped} break rolls while afk, percentage chance is now {round((self.multiplier * .01) * 100)}%")


    def random_sleep_length(self, delay_min=0, delay_max=0):
        """Returns a random float between min and max"""
        if delay_min == 0:
            delay_min = self.delay_min
        if delay_max == 0:
            delay_max = self.delay_max
        return rd.fancy_normal_sample(delay_min, delay_max)
    
    def switch_window(self):
        """
        This will switch the window to runelite.
        Returns: void
        Args: None
        """
        # Get the currently focused window
        old_window = pag.getActiveWindow()

        pag.hotkey("alt", "tab")
        new_window = pag.getActiveWindow()

        self.log_msg(f"Switched to window: {new_window.title}.")

        self.is_focused = "RuneLite" in new_window.title
        if old_window.title == new_window.title:
            self.log_msg("Window not switched, something is wrong, quitting bot.")
            self.stop()

        time.sleep(self.random_sleep_length())


    def check_for_level_up(self, img: Path):
        """Checks if the player has leveled up. By looking for image in chat
            Args:
                img: Path
            Returns:
                boolean"""
        return bool(found := imsearch.search_img_in_rect(img, self.win.chat))


    def check_break(self, runtime, percentage, minutes_since_last_break, seconds):
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
            if runtime % 60 == 0:   # every minute log the chance of a break
                self.log_msg(f"Chance of random break is {round(percentage * 100)}%")

            self.roll_break(
                percentage, minutes_since_last_break, seconds
            )

        elif self.roll_chance_passed:
            self.log_msg(f"Chance of random break is {round(percentage * 100)}%")

            self.roll_break(
                percentage, minutes_since_last_break, seconds
            )
        self.last_runtime = runtime



    def roll_break(self, percentage, minutes_since_last_break, seconds):
        if (
            rd.random_chance(probability=percentage / (1 if self.afk_train else 4))   # when afk theres weird timing issues so we divide by 4 if not afk
            and self.take_breaks
        ):
            self.reset_timer(
                minutes_since_last_break, seconds, percentage
            )
        self.multiplier += .25  # increase multiplier for chance of random break, we want + 1% every minute 
        self.roll_chance_passed = False


    def check_deposit_all(self):
        """
        This will check if deposit all png is found, and select all if not.
        """
        # if we've already searched and found, return
        if not self.deposit_all_red_button:
            return
        # get the path of deposit_all_grey.png and red
        deposit_all_grey = self.WILLOWSDAD_IMAGES.joinpath("deposit_all_grey.png")
        deposit_all_red = self.WILLOWSDAD_IMAGES.joinpath("deposit_all_red.png")

        # if we find deposit all red in game view, return, else, find grey and click
        time_searching = time.time()
        while True:
            self.deposit_all_red_button = imsearch.search_img_in_rect(
                deposit_all_red, self.win.game_view.scale(scale_height=.2, scale_width=.5, anchor_y=.8)
            )
            if self.deposit_all_red_button:
                return   # We found deposit all is already selected, return.
            # We now check several times within 1 second for deposit all grey, if we find it, click it and return.
            elif deposit_all_grey_button := imsearch.search_img_in_rect(
                deposit_all_grey, self.win.game_view.scale(scale_height=.2, scale_width=.5, anchor_y=.8)
            ):
                self.mouse.move_to(deposit_all_grey_button.random_point())
                self.mouse.click()
                return
            if time.time() - time_searching > 1:
                self.log_msg("Could not verifty deposit all settings, double check those.")
                return
            time.sleep(.2)
                
        
    def reset_timer(self, minutes_since_last_break, seconds, percentage):
        self.log_msg(f"Break time, last break was {minutes_since_last_break} minutes and {seconds} seconds ago. \n Chance of random break was {round(percentage * 100)}%")

        self.last_break = time.time()   # reset last break time
        self.multiplier = 1    # reset multiplier

        self.take_random_break(minutes_since_last_break)


    def take_menu_break(self):
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
            self.mouse.click()
            self.mouse.move_to(self.win.control_panel.random_point())
            time.sleep(break_time)

            # go back to inventory
            self.mouse.move_to(self.win.cp_tabs[3].random_point())
            time.sleep(self.random_sleep_length())
            self.mouse.click()
        else:
            self.log_msg("Taking an Equipment menu break...")
            self.mouse.move_to(self.win.cp_tabs[4].random_point())
            time.sleep(self.random_sleep_length())
            self.mouse.click()

            self.mouse.move_to(self.win.control_panel.random_point())
            time.sleep(break_time)

            # go back to inventory
            self.mouse.move_to(self.win.cp_tabs[3].random_point())
            self.mouse.click()
        return
    

    def take_random_break(self, minutes_since_last_break):
        """This will randomly choose a break type and take it. The shorter time since last break, the more likely it is to be a menu break.
        Returns: void
        Args: minutes_since_last_break (int) - the number of minutes passed since the last break."""
        # break type is a random choice from list
        break_type = random.choice(["menu", "break"])

        if break_type == "menu":
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


    def switch_account(self):
        """
        Logs out and signs back in with a new account.
        Returns: void
        Args: None
        """
        new_user = self.user2 if self.current_user == self.user1 else self.user1
        self.logout()

        # if its after 10pm, sleep for 5-7 hours
        if datetime.datetime.now().hour >= 23:
            self.log_msg("Sleeping for 5-7 hours...")
            time.sleep(random.uniform(18000, 25200))

        # 20% chance to sleep for 20seconds to 10 minutes
        if rd.random_chance(.187):
            self.log_msg("Sleeping for a while...")
            time.sleep(random.uniform(20, 600))

        else: 
            time.sleep(self.random_sleep_length() * 3)

        if existing_user := imsearch.search_img_in_rect(
            self.WILLOWSDAD_IMAGES.joinpath("existing_user.png"),
            self.win.game_view,
        ):
            self.mouse.move_to(existing_user.random_point())
            self.mouse.click()
            time.sleep(self.random_sleep_length() / 2)

        # press tab to go to username field
        pag.press('tab')

        # hold backspace to delete current username
        for _ in range(len(self.current_user[0])):  # adjust the range as needed
            pag.press('backspace')
            time.sleep(self.random_sleep_length() / 3)

        # type in new username
        pag.write(new_user[0], interval=self.random_sleep_length() / 3)

        # press tab to go to password field
        pag.press('tab')

        # type in new password
        pag.write(new_user[1], interval=self.random_sleep_length() / 3)

        # press enter to login
        pag.press('enter')

        # wait for login
        time.sleep(self.random_sleep_length(8,12))
        if click_to_play := imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("click_to_play.png"), self.win.game_view):
            self.mouse.move_to(click_to_play.random_point())
            self.mouse.click()
        else:
            self.log_msg("Could not find click to play button, double check login.")
            self.stop()
        self.current_user = new_user
        time.sleep(self.random_sleep_length(1.5,2.5))
        return


    def is_inv_empty(self):
        """
        Checks if inventory is empty.
        Returns: bool
        """
        for i in range(len(self.win.inventory_slots)):
            slot_location = self.win.inventory_slots[i].scale(.5,.5)
            slot_img = imsearch.BOT_IMAGES.joinpath(self.WILLOWSDAD_IMAGES, "emptyslot.png")
            if slot := imsearch.search_img_in_rect(slot_img, slot_location):
                continue
            return False
        return True
    
    
    def is_inv_full(self):
        """
        Checks if inventory is full.
        Returns: bool
        """
        for i in range(len(self.win.inventory_slots)):
            slot_location = self.win.inventory_slots[i].scale(.5,.5)
            slot_img = imsearch.BOT_IMAGES.joinpath(self.WILLOWSDAD_IMAGES, "emptyslot.png")
            if slot := imsearch.search_img_in_rect(slot_img, slot_location):
                return False
        return True


    def open_bank(self):
        """
        This will bank all logs in the inventory.
        Returns: 
            void
        Args: 
            deposit_slots (int) - Inventory position of each different item to deposit.
        """
        # move mouse to bank and click while not red click
        bank = self.choose_bank()
        self.mouse.move_to(bank.random_point())
        while not self.mouse.click(check_red_click=True):
            bank = self.choose_bank()
            self.mouse.move_to(bank.random_point())

        wait_time = time.time()
        retried = False
        while not self.is_bank_open():
            if time.time() - wait_time > 20 and not retried:
                self.mouse.move_to(bank.random_point())
                while not self.mouse.click(check_red_click=True):
                    bank = self.choose_bank()
                    self.mouse.move_to(bank.random_point())
                retried = True
            # if we waited for 17 seconds, break out of loop
            if time.time() - wait_time > 60:
                self.log_msg("We clicked on the bank but bank is not open after 60 seconds, bot is quiting...")
                self.stop()
            time.sleep(self.random_sleep_length())
        return
    

    def check_text(self, object: RuneLiteObject, text, color : clr = None):
        """
        calls mouseover text in a loop
        Returns: void
        Args: None
        """
        if not isinstance(text, list):
            text = [text]

        time_searching = time.time()
        search_tries = 1

        while all(txt not in self.mouseover_text() for txt in text):
            time.sleep(self.random_sleep_length(.1, .2))

            if time.time() - time_searching > 2:
                self.mouse.move_to(object.random_point())

            if time.time() - time_searching > 4:
                msg = f"Did not see any of {text} in mouseover text after {search_tries} searches, quitting bot so you can fix it..."
                self.log_msg(msg)
                self.stop()

            search_tries += 1


    def choose_bank(self):
        """
        Has a small chance to choose the second closest bank to the player.
            Returns: bank rectangle or none if no banks are found
            Args: None

        """
        bank = self.get_nearest_tag(clr.YELLOW)

        time_searching = time.time()
        while not bank:
            bank = self.get_nearest_tag(clr.YELLOW)
            time.sleep(.2)
            if time.time() - time_searching > 2:
                self.log_msg("No banks found, trying to adjust camera...")
                if not self.adjust_camera(clr.YELLOW):
                    self.log_msg("No banks found, quitting bot...")
                    self.stop()
                return (self.choose_bank())
        return bank
    

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
            time.sleep(self.random_sleep_length(.1, .2))
        camera_thread.stop()
        time.sleep(self.random_sleep_length())
        return True


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


    def click_in_bank(self, item, amount=1):
        """
        Clicks on an item in the bank x times.
        Args:
            item (RuneLiteObject) - Item to click on
            amount (int) - Number of times to click on item
        Returns:
            void"""
        for _ in range(amount):
            self.mouse.move_to(item.random_point())
            if self.mouseover_text("Release", clr.OFF_WHITE):
                return False
            self.mouse.click()
            time.sleep(self.random_sleep_length())
            return True


    def withdraw_items2(self, items: Union[RuneLiteObject, List[RuneLiteObject]], count=1) -> bool:
        """
        Given a list of runelite items, clicks on them from their saved locations.
        Returns True if all items are found and clicked, False otherwise.
        Args:
            items: A RuneLiteObject or list of RuneLiteObjects representing the item images to search for in the bank.
            count: An integer representing the amount of items to withdraw. Default is 1.
        """
        if not isinstance(items, list):
            items = [items]
        for item in items:
            success = self.click_in_bank(item, count)
            if not success:
                self.log_msg(f"Could not find {item} in bank, mouseover check may have failed, or out of supplies")
                self.stop()
        return True


    def withdraw_items(self, items: Union[Path, List[Path]], count=1) -> bool:
        """
        Withdraws the correct amount of ingredients from the bank.
        Returns True if all items are found and clicked, False otherwise.
        Args:
            items: A Path object or list of Path objects representing the item images to search for in the bank.
            count: An integer representing the amount of items to withdraw. Default is 1.
        """
        def find_and_click(item_img: Path) -> bool:
            """Searches for an item image in the bank and clicks on it."""
            item_found = None
            time_looking_for_item = time.time() + 5
            while time.time() < time_looking_for_item and not item_found:
                # Try several times to find the item
                item_found = imsearch.search_img_in_rect(item_img, self.win.game_view.scale(scale_width=.5))
                if item_found:
                    break
            if not item_found:
                # If the item is not found, log an error message and return False
                self.log_msg(f"Could not find {item_img.stem} in bank, out of supplies...")
                return False
            else:
                # If the item is found, click on it and return True
                self.click_in_bank(item_found, count)
                return True

        # Convert the input to a list if it's a single Path object
        if isinstance(items, Path):
            items = [items]

        # Loop through each item and find/click it in the bank
        all_items_found = True
        for item_path in items:
            item_found = find_and_click(item_path)
            time.sleep(self.random_sleep_length())
            if not item_found:
                all_items_found = False

        # Return True if all items were found and clicked, False otherwise
        return all_items_found


    def deposit_items(self, slot_list, clicks=1):
        """
        Clicks once on each unique item to deposit all matching items in the inventory to the bank.
        Bank must be open already.
        Deposit "All" must be selected.
        Args:
            slot_list: list of inventory slots to deposit items from
        Returns:
            None/Void
        """
        if slot_list == -1:
            # If there are no items to deposit, log a message and return early
            self.log_msg("No items to deposit, continuing...")
            return
        if slot_list == 0:
            # If there's only one item, it is the first slot
            slot_list = [0]
        # Move the mouse to each slot in the inventory and click to deposit all matching items
        for slot in slot_list:
            self.mouse.move_to(self.win.inventory_slots[slot].random_point(), mouseSpeed = "fast")
            self.mouse.click()
            time.sleep(self.random_sleep_length())

        self.log_msg("Finished depositing items")
        return


    def face_north(self):
        """Faces the player north.
            Args:
                None
            Returns:
                None"""
        # Move the mouse to the compass orb and click it to face north
        self.mouse.move_to(self.win.compass_orb.random_point(), mouseSpeed = "fastest")
        self.mouse.click()


    def close_bank(self):
        """Exits the bank by clicking on the exit button, or pressing the esc key if the button is not found"""
        # Search for the exit button in the bank interface
        if not self.exit_btn:
            self.exit_btn = imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("bank_exit.png"), self.win.game_view.scale(scale_height=.2, scale_width=.5, anchor_y=0))

        # If the exit button is not found, press the esc key and check if the bank is closed
        time_searching = time.time()
        while not self.exit_btn:
            self.exit_btn = imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("bank_exit.png"), self.win.game_view.scale(scale_height=.2, scale_width=.5, anchor_y=1), confidence=.1)
            if time.time() - time_searching > 2:
                # If the exit button is still not found after 2 second, log an error message and stop the bot
                self.log_msg("Could not find bank exit button, pressing esc.")
                pag.press("esc")
                time.sleep(self.random_sleep_length())
                if not self.is_bank_open():
                    return
                self.log_msg("Closing bank failed, quitting bot...")
                self.stop()
            time.sleep(.2)

        # Click on the exit button to close the bank
        self.mouse.move_to(self.exit_btn.random_point())
        self.mouse.click()
        time.sleep(self.random_sleep_length())

        return



    def is_bank_open(self):
        """Checks if the bank is open, if not, opens it
        Returns:
            True if the bank is open, False if not
        Args:
            None"""
        # Define the image to search for in the bank interface
        deposit_all_img = self.WILLOWSDAD_IMAGES.joinpath("bank_all.png")

        # Set a time limit for searching for the image
        end_time = time.time() + 2

        # Loop until the time limit is reached
        while (time.time() < end_time):
            # Check if the image is found in the game view
            if deposit_btn := imsearch.search_img_in_rect(deposit_all_img, self.win.game_view.scale(scale_height=.2, scale_width=.5, anchor_y=.8)):
                return True

            # Sleep for a short time to avoid excessive CPU usage
            time.sleep(.2)

        # If the image was not found within the time limit, return False
        return False
    
    def check_withdraw_x(self, amount):
        if withdraw_grey := imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("deposit_x_grey.png"), self.win.game_view.scale(.5,.5, anchor_y=.75), confidence=.1):
            self.mouse.move_to(withdraw_grey.scale(.5,.5).random_point())
            self.sleep(self.random_sleep_length())
            if self.mouseover_text(f"{amount}", color=clr.OFF_WHITE):
                self.mouse.click()
            else:
                self.log_msg(f"Set withdraw amount to {amount}.")
                self.stop()
        elif withdraw_red := imsearch.search_img_in_rect(self.WILLOWSDAD_IMAGES.joinpath("deposit_x_red.png"), self.win.game_view.scale(.5,.5, anchor_y=.75)):
            self.mouse.move_to(withdraw_red.scale(.3,.3).random_point())
            self.sleep(self.random_sleep_length())
            if self.mouseover_text(f"{amount}", color=clr.OFF_WHITE):
                return
            self.log_msg(f"Set withdraw amount to {amount}.")
            self.stop()
        else:
            self.log_msg("Could not find withdraw x button using image search, please check code, report to developer.")
            self.stop()