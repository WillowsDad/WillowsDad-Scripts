import time

import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot


class OSRSWDThieving(WillowsDadBot):
    def __init__(self):
        bot_title = "WillowsDad Thieving"
        description = "This bot will left-click pickpocket(men) or steal from ardougne cake stall. Just meant to run for a couple minutes for requirements. No support. Coin pouches expected in 1st slot."
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 20
        self.running_time = 200
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
        super().create_options()
        self.options_builder.add_dropdown_option("thieving_method", "Thieving Method?", ["Pickpocketing","Stalls"])

    def save_options(self, options: dict):
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)
        for option in options:
            if option == "thieving_method":
                self.thieving_method = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg("Options set successfully.")
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{'' if self.take_breaks else ' not'} take breaks.")
        self.log_msg(f"Bot will{'' if self.afk_train else ' not'} train like you're afk on another tab.")
        self.log_msg(f"Bot will wait between {self.delay_min} and {self.delay_max} seconds between actions.")
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
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:
            # -- Perform bot actions here --
            # Code within this block will LOOP until the bot is stopped.
            runtime = int(time.time() - self.start_time)
            minutes_since_last_break = int((time.time() - self.last_break) / 60)
            seconds = int(time.time() - self.last_break) % 60
            percentage = (self.multiplier * .01)  # this is the percentage chance of a break
            self.roll_chance_passed = False

            try:
                self.thieve()
                self.update_progress((time.time() - start_time) / end_time)



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
        super().setup()
        self.coin_pouch_count = 0

    def thieve(self):
        if self.thieving_method == "Pickpocketing":
            self.pickpocket()
        elif self.thieving_method == "Stalls":
            self.steal_from_stall()

    def pickpocket(self):

        if self.has_hp_bar():
            time.sleep(self.random_sleep_length(2.7, 4))

        victim = self.get_nearest_tagged_NPC()
        self.mouse.move_to(victim.scale(.5,.5).random_point())

        # while click is not red, move mouse and click
        while not self.mouse.click(check_red_click=True):
            self.mouse.move_to(self.get_nearest_tagged_NPC().scale(.5,.5).random_point())


        self.api_m.wait_til_gained_xp("Thieving", timeout=4)
        self.coin_pouch_count += 1

        if self.coin_pouch_count > 23 and rd.random_chance(0.3):
            self.mouse.move_to(self.win.inventory_slots[0].random_point())
            self.mouse.click()
            self.coin_pouch_count = 0
        elif self.coin_pouch_count > 27:
            self.mouse.move_to(self.win.inventory_slots[0].random_point())
            self.mouse.click()
            self.coin_pouch_count = 0

    def steal_from_stall(self):
        """This will look for pink tag and left click on it"""
        stall = self.get_nearest_tag(clr.PINK)

        if stall is None:
            time.sleep(self.random_sleep_length())
            return

        self.mouse.move_to(stall.random_point())

        while not self.mouse.click(check_red_click=True):
            stall = self.get_nearest_tag(clr.PINK)
            if stall is None:
                return
            self.mouse.move_to(stall.random_point())
        time.sleep(self.random_sleep_length(1.3, 1.5))

        if self.api_m.get_is_inv_full():
            self.drop_all()