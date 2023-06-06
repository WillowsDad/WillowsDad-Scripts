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



class OSRSWDTemplate(WillowsDadBot):
    def __init__(self):
        bot_title = "WDTemplate"
        description = """Template for you to copy and paste to create a script."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
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

    def save_options(self, options: dict):  # sourcery skip: for-index-underscore
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        super().save_options(options)
        for option in options:
            return # check options and assign to variables

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
                print("Starting bot actions") # bot actions go here
                
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