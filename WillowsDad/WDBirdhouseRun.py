import datetime
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
import random



class OSRSWDBirdhouseRun(WillowsDadBot):
    def __init__(self):
        bot_title = "WD Birdhouse Run"
        description = """Will sign in and do birdhouse runs and then sign out."""
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 200
        self.take_breaks = True
        self.afk_train = True
        self.delay_min =0.37
        self.delay_max = .67
        self.loops = 10
        self.wait_time = 0
        self.birdhouse = self.WILLOWSDAD_IMAGES.joinpath("Yew_bird_house_bank.png")


    def create_options(self):
        """
        Use the OptionsBuilder to define the options for the bot. For each function call below,
        we define the type of option we want to create, its key, a label for the option that the user will
        see, and the possible values the user can select. The key is used in the save_options function to
        unpack the dictionary of options after the user has selected them.
        """
        self.options_builder.add_slider_option( "loops", "How many loops?", 1, 50)
        self.options_builder.add_slider_option("delay_min", "How long to take between actions (min) (MiliSeconds)?", 300,1200)
        self.options_builder.add_slider_option("delay_max", "How long to take between actions (max) (MiliSeconds)?", 350,1200)
        self.options_builder.add_slider_option("wait_time", "Wait time before first run (minutes)?", 0, 50)
        self.options_builder.add_dropdown_option("bird_house_type", "What type of bird house?", ["Oak", "Willow", "Maple", "Teak", "Mahogany", "Yew", "Magic", "Redwood"])

    def save_options(self, options: dict):  # sourcery skip: for-index-underscore
        """
        For each option in the dictionary, if it is an expected option, save the value as a property of the bot.
        If any unexpected options are found, log a warning. If an option is missing, set the options_set flag to
        False.
        """
        for option in options:
            if option == "loops":
                self.loops = options[option]
            elif option == "delay_min":
                self.delay_min = options[option]/1000
            elif option == "delay_max":
                self.delay_max = options[option]/1000
            elif option == "wait_time":
                self.wait_time = options[option]*60
            elif option == "bird_house_type":
                self.birdhouse = self.WILLOWSDAD_IMAGES.joinpath(f"{options[option]}_bird_house_bank.png")

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
        while self.count < self.loops:

            self.count += 1

            if self.get_run_energy() > 60:
                self.check_run()
            self.take_birdhouse_break()

            # lets make sure we're by bank before signing out
            self.wait_until_color(clr.YELLOW)

            self.logout()
            
            # sleeping for 56minutes to an hour
            self.log_msg(f"Run {self.count} of {self.loops} complete.")

            self.switch_window()

            self.take_break(3360, 3600)

            self.switch_window()

            self.sign_in()

            self.wait_until_color(clr.YELLOW)


            # print out how many runs we've done

                
            # -- End bot actions --
            self.update_progress(self.count / self.loops)

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
        self.get_UandP()
        self.count = 0

        if self.wait_time > 0:
            self.log_msg(f"Waiting {self.wait_time / 60} minutes before starting.")
            self.logout()
            self.take_break(self.wait_time, self.wait_time)
            self.sign_in()
            self.wait_until_color(clr.YELLOW)
            self.wait_time = 0


    def take_break(self, min_seconds: int = 1, max_seconds: int = 30, fancy: bool = False):
        """
        Takes a break for a random amount of time.
        Args:
            min_seconds: minimum amount of time the bot could rest
            max_seconds: maximum amount of time the bot could rest
            fancy: if True, the randomly generated value will be from a truncated normal distribution
                with randomly selected means. This may produce more human results.
        """
        self.log_msg("Taking a break...")
        if fancy:
            length = rd.fancy_normal_sample(min_seconds, max_seconds)
        else:
            length = random.uniform(min_seconds, max_seconds)
        length = round(length)
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=length)
        self.log_msg(f"Signing back in at {end_time.strftime('%I:%M:%S %p')}.", overwrite=True)
        time.sleep(length)
        self.log_msg(f"Done taking {length} second break.", overwrite=True)