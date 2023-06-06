import shutil
import time
from pathlib import Path
import utilities.api.item_ids as item_ids
import utilities.color as clr
import utilities.game_launcher as launcher
import utilities.random_util as rand
from model.bot import BotStatus
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from model.osrs.WillowsDad.WillowsDad_bot import WillowsDadBot


class OSRSWDCombat(WillowsDadBot, launcher.Launchable):

    bones_to_bury = [item_ids.BONES, item_ids.BIG_BONES, item_ids.DRAGON_BONES]

    def __init__(self):
        bot_title = "WD Combat"
        description = (
            "This bot kills NPCs. Position your character near some NPCs and highlight them. After setting this bot's options, please launch RuneLite with the"
            " button on the right."
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time: int = 10
        self.delay_min: int = 350
        self.delay_max: int = 500
        self.loot_items: str = ""
        self.hp_threshold: int = 12
        self.bury_bones = False

    def create_options(self):
        super().create_options()
        self.options_builder.add_text_edit_option("loot_items", "Loot items (requires re-launch):", "E.g., Coins, Dragon bones")
        self.options_builder.add_slider_option("hp_threshold", "Low HP threshold (0-100)?", 0, 100)
        self.options_builder.add_checkbox_option("bury_bones","Bury Bones?", [" "])

    def save_options(self, options: dict):
        super().save_options(options)
        for option in options:
            if option == "bury_bones":
                self.bury_bones = options[option] != []
            elif option == "hp_threshold":
                self.hp_threshold = options[option]

            elif option == "loot_items":
                self.loot_items = options[option]
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f'Loot items: {self.loot_items or "None"}.')
        self.log_msg(f"Bot will eat when HP is below: {self.hp_threshold}.")
        self.log_msg("Options set successfully. Please launch RuneLite with the button on the right to apply settings.")

        self.options_set = True

    def main_loop(self):  # sourcery skip: low-code-quality
        self.setup()
        # Main loop
        while time.time() - self.start_time < self.end_time:

            runtime = int(time.time() - self.start_time)
            minutes_since_last_break = int((time.time() - self.last_break) / 60)
            seconds = int(time.time() - self.last_break) % 60
            percentage = (self.multiplier * .01)  # this is the percentage chance of a break
            bury_slots = self.api_m.get_inv_item_indices(self.bones_to_bury)
            self.roll_chance_passed = False

            try:
                # If inventory is full...
                if self.api_s.get_is_inv_full() and self.bury_bones:
                    self.log_msg("Inventory full. Burying bones...")
                    self.bury_bones_in_inventory(bury_slots)
                # While not in combat
                while self.api_m.get_is_player_idle():
                    # Find a target
                    target = self.get_nearest_tagged_NPC()
                    if target is None:
                        failed_searches += 1
                        if failed_searches % 10 == 0:
                            self.log_msg("Searching for targets...")
                        if failed_searches > 60:
                            # If we've been searching for a whole minute...
                            self.__logout("No tagged targets found. Logging out.")
                            return
                        time.sleep(1)
                        continue
                    failed_searches = 0

                    # Click target if mouse is actually hovering over it, else recalculate
                    self.mouse.move_to(target.random_point())
                    while not self.mouse.click(check_red_click=True):
                        target = self.get_nearest_tagged_NPC()
                        self.mouse.move_to(target.random_point(), mouseSpeed="fastest")
                        if "reach" in self.api_m.get_latest_chat_message().lower():
                            self.log_msg("Target is out of reach.")
                            targets = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
                            self.mouse.move_to(targets[int(rand.fancy_normal_sample(0,len(targets)-1))].random_point(), mouseSpeed="fastest")
                    time.sleep(3)
                
                # While in combat
                while self.has_hp_bar():
                    # Check to eat food
                    if self.get_hp() < self.hp_threshold:
                        self.__eat(self.api_s)
                    time.sleep(.5)

                # Loot all highlighted items on the ground
                if self.loot_items:
                    self.__loot(self.api_s)

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
        self.__logout("Finished.")

    def setup(self):
        super().setup()
        self.toggle_auto_retaliate(True)
        self.mouse.move_to(self.win.cp_tabs[3].random_point())
        self.mouse.click()

        self.failed_searches = 0

    def bury_bones_in_inventory(self, slot_list):
        """Buries all bones in inventory"""
        if len(slot_list) == 0:
            return
        
        for slot in slot_list:
            self.mouse.move_to(self.win.inventory_slots[slot].random_point())
            self.mouse.click()
            self.api_m.wait_til_gained_xp("Prayer", 3)
            time.sleep(self.random_sleep_length())

    def __eat(self, api: StatusSocket):
        self.log_msg("HP is low.")
        food_slots = api.get_inv_item_indices(item_ids.all_food)
        if len(food_slots) == 0:
            self.log_msg("No food found. Pls tell me what to do...")
            self.logout()
            self.stop()
            return
        self.log_msg("Eating food...")
        self.mouse.move_to(self.win.inventory_slots[food_slots[0]].random_point())
        self.mouse.click()

    def __loot(self, api: StatusSocket):
        """Picks up loot while there is loot on the ground"""
        while self.pick_up_loot(self.loot_items):
            if api.get_is_inv_full():
                return
            curr_inv = len(api.get_inv())
            self.log_msg("Picking up loot...")
            for _ in range(10):  # give the bot 5 seconds to pick up the loot
                if len(api.get_inv()) != curr_inv:
                    self.log_msg("Loot picked up.")
                    time.sleep(self.random_sleep_length())
                    break
                time.sleep(.5)

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
