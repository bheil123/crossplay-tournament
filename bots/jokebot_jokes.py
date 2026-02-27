"""
JokeBot Joke Database -- 300+ family-themed jokes for Crossplay tournament.

Each joke's setup trails off so the WORD played by JokeBot serves as the punchline.
The tournament runner prints the move on the next line, completing the joke.

Family members:
  Dad/Bill - overthinking Crossplay strategy, dad jokes, gadgets
  Mom - SF Giants, baseball, cooking, grandkids, beautiful long soft white hair
  Bill3 - tall, jokes, weightlifting, coding, Yelp, Subaru
  Patrick - hockey, video games, drinking milk, Skittles
  Katie - pottery, cooking, Berkeley, TESOL, language
  Madeleine - rescue animals, burlesque, music
  Julia - horses, Boulder, Cayl (fiance), bugs
"""

import random


# =============================================================================
# WORD-SPECIFIC JOKES
# Maps uppercase words -> list of joke dicts
# Each setup should end so the word naturally completes it
# =============================================================================

JOKES = {
    # --- A ---
    "ACE": [
        {"id": 0, "setup": "Mom struck out the side at the Giants fantasy camp. Dad said, 'You're an...'"},
        {"id": 1, "setup": "Bill3 reviewed a restaurant on Yelp so perfectly it got called an...'"},
    ],
    "AGE": [
        {"id": 0, "setup": "Dad tried to do a cartwheel at the park. Katie said, 'Act your...'"},
        {"id": 1, "setup": "Madeleine asked Mom how old her rescue cat was. Mom said, 'We don't talk about...'"},
    ],
    "AID": [
        {"id": 0, "setup": "Patrick fell off his chair reaching for the milk. Bill3 calmly dialed for first...'"},
    ],
    "AIR": [
        {"id": 0, "setup": "Madeleine performed a burlesque fan dance so dramatic she used up all the...'"},
        {"id": 1, "setup": "Patrick opened the fridge and just stood there. Mom said, 'Stop conditioning the...'"},
    ],
    "ALE": [
        {"id": 0, "setup": "Dad tried to brew his own beer with a new gadget. Katie said it tasted like ginger...'"},
    ],
    "ANT": [
        {"id": 0, "setup": "Julia found a bug in the yard and gave it a name. She said, 'This isn't just any bug, it's an...'"},
    ],
    "APE": [
        {"id": 0, "setup": "Patrick's hockey celebration dance looked less like a goal celly and more like an...'"},
    ],
    "APP": [
        {"id": 0, "setup": "Bill3 built something for his phone in one weekend. Dad called it an...'"},
    ],
    "ART": [
        {"id": 0, "setup": "Madeleine's burlesque costume was so elaborate, Katie said it wasn't a costume, it was...'"},
        {"id": 1, "setup": "Katie's pottery professor at Berkeley said her vase wasn't just a vase, it was...'"},
    ],
    "ATE": [
        {"id": 0, "setup": "Patrick opened the fridge, looked at the leftovers, and in 30 seconds flat, he...'"},
        {"id": 1, "setup": "Katie made a beautiful 5-course dinner. Patrick said, 'Great, I...'"},
    ],
    "AWE": [
        {"id": 0, "setup": "Mom caught a foul ball at the Giants game bare-handed. The whole section stared in...'"},
    ],
    "AXE": [
        {"id": 0, "setup": "Katie's pottery didn't survive the kiln. She said the project got the...'"},
    ],

    # --- B ---
    "BAD": [
        {"id": 0, "setup": "Patrick drank a gallon of milk before hockey practice. Coach said that was...'"},
        {"id": 1, "setup": "Dad told a dad joke so terrible, even Bill3 -- the family joke expert -- said it was...'"},
    ],
    "BAG": [
        {"id": 0, "setup": "Madeleine packed for a weekend trip with 6 suitcases. Katie brought one...'"},
        {"id": 1, "setup": "Patrick grabbed a whole bag of Skittles. Mom said, 'That's not a snack, that's a...'"},
    ],
    "BAR": [
        {"id": 0, "setup": "Bill3 walked into a gym and loaded 315 pounds on the bench press. He said, 'That's just the...'"},
    ],
    "BAT": [
        {"id": 0, "setup": "Mom hit a home run at the company softball game. She kissed her...'"},
        {"id": 1, "setup": "Madeleine rescued a creature from the attic. Dad said, 'That's not a cat, that's a...'"},
    ],
    "BET": [
        {"id": 0, "setup": "Dad calculated there was a 94.7% chance he'd win this game. Julia said, 'Wanna...'"},
    ],
    "BIG": [
        {"id": 0, "setup": "Bill3 had to duck through every doorway. Patrick said, 'Being that tall is honestly pretty...'"},
        {"id": 1, "setup": "Mom said the Giants were going to make a...'"},
    ],
    "BIT": [
        {"id": 0, "setup": "Madeleine's rescue chihuahua got a little too excited and...'"},
    ],
    "BITE": [
        {"id": 0, "setup": "Patrick took a piece of Katie's fresh bread. She said, 'ONE...'"},
    ],
    "BLANK": [
        {"id": 0, "setup": "Dad asked Patrick what he learned in school today. Patrick's face went...'"},
    ],
    "BLOCK": [
        {"id": 0, "setup": "Patrick tried to score on Bill3 in mini hockey but Bill3's wingspan threw up a...'"},
    ],
    "BOARD": [
        {"id": 0, "setup": "Dad stared at the Crossplay tiles for 20 minutes. Katie said, 'Dad, it's just a...'"},
    ],
    "BOLT": [
        {"id": 0, "setup": "Julia's horse spooked at a butterfly and took off like a...'"},
    ],
    "BONE": [
        {"id": 0, "setup": "Madeleine's rescue dog buried Dad's new gadget in the backyard. She said, 'He thought it was a...'"},
    ],
    "BOOK": [
        {"id": 0, "setup": "Katie was studying linguistics at Berkeley. Patrick picked up her textbook and said, 'This isn't a book, it's a...'"},
    ],
    "BOWL": [
        {"id": 0, "setup": "Patrick poured cereal and milk into the biggest container he could find. That's not a cup, that's a...'"},
        {"id": 1, "setup": "Katie threw the most gorgeous piece on the wheel. She called it a...'"},
    ],
    "BOX": [
        {"id": 0, "setup": "Madeleine's rescue cat ignored all the toys and sat in the...'"},
    ],
    "BRAVE": [
        {"id": 0, "setup": "Julia picked up a spider with her bare hands. Patrick screamed. She said, 'Don't be scared, be...'"},
    ],
    "BRIDE": [
        {"id": 0, "setup": "Cayl proposed to Julia in Boulder. She was going to be a...'"},
    ],
    "BUG": [
        {"id": 0, "setup": "Julia found a beetle in Boulder and wanted to keep it. Cayl said, 'That's a...'"},
        {"id": 1, "setup": "Bill3's code had a problem. He spent 4 hours finding the...'"},
    ],
    "BURN": [
        {"id": 0, "setup": "Katie left the sourdough in the oven too long. Patrick said, 'Nice...'"},
        {"id": 1, "setup": "Bill3 roasted Dad's Crossplay strategy so hard, Madeleine called it a sick...'"},
    ],

    # --- C ---
    "CAKE": [
        {"id": 0, "setup": "Mom baked a three-layer masterpiece for the grandkids. Patrick ate it before the frosting set. She said, 'That was not a snack, that was a...'"},
    ],
    "CALL": [
        {"id": 0, "setup": "The ump made a terrible strike three on Mom's favorite Giant. She screamed, 'That's a bad...'"},
    ],
    "CALM": [
        {"id": 0, "setup": "Julia was feeding carrots to her horse while everyone argued about Crossplay. She was totally...'"},
    ],
    "CAMP": [
        {"id": 0, "setup": "Patrick brought his Xbox to the wilderness. Dad said, 'This is supposed to be...'"},
    ],
    "CAN": [
        {"id": 0, "setup": "Julia asked if she could beat Dad at Crossplay. Mom said, 'Yes you...'"},
    ],
    "CAR": [
        {"id": 0, "setup": "Bill3 tried to fold his 6'4 frame into a compact. He said, 'I need a bigger...'"},
    ],
    "CARD": [
        {"id": 0, "setup": "Dad bought a new gadget for everyone's birthday instead of writing a...'"},
    ],
    "CAST": [
        {"id": 0, "setup": "Madeleine announced the roles for her living room burlesque show. 'And now, the...'"},
    ],
    "CAT": [
        {"id": 0, "setup": "Madeleine came home with another rescue. Dad said, 'Is that a dog or a...'"},
        {"id": 1, "setup": "Julia drew whiskers on Patrick's face while he slept. He woke up looking like a...'"},
    ],
    "CATCH": [
        {"id": 0, "setup": "Mom snagged a line drive at the Giants game. The guy next to her said, 'Nice...'"},
    ],
    "CHEF": [
        {"id": 0, "setup": "Mom's cooking was so good, the grandkids bowed and said, 'Thank you...'"},
    ],
    "CLASS": [
        {"id": 0, "setup": "Katie was teaching English to international students at Berkeley. She loved every...'"},
    ],
    "CLAY": [
        {"id": 0, "setup": "Katie came home from pottery class with her hands covered in...'"},
    ],
    "CLIMB": [
        {"id": 0, "setup": "Julia and Cayl went hiking in Boulder. He said, 'That's quite a...'"},
    ],
    "CODE": [
        {"id": 0, "setup": "Bill3 stayed up until 3 AM debugging. He said, 'I just need to fix one more line of...'"},
    ],
    "COLD": [
        {"id": 0, "setup": "Patrick drank milk straight from the fridge. Mom said, 'At least drink it...'"},
    ],
    "COOK": [
        {"id": 0, "setup": "Mom made Thanksgiving dinner for 12 people. Dad tried to help and she said, 'Too many people trying to...'"},
    ],
    "COOL": [
        {"id": 0, "setup": "Patrick scored a goal and did a celebration dance. Nobody was impressed. Bill3 said, 'Real...'"},
    ],
    "COW": [
        {"id": 0, "setup": "Patrick drinks so much milk, Madeleine said he might as well adopt a...'"},
    ],
    "CRAB": [
        {"id": 0, "setup": "Julia found a crustacean on a Boulder creek hike. She said, 'Cayl, look at this...'"},
    ],
    "CRASH": [
        {"id": 0, "setup": "Bill3's code compiled but the app immediately went...'"},
    ],
    "CRY": [
        {"id": 0, "setup": "The Giants lost in the bottom of the 9th. Mom didn't...'"},
    ],
    "CUP": [
        {"id": 0, "setup": "Katie made a beautiful ceramic mug on the wheel. Patrick used it to hold milk. She said, 'That's an art piece, not a...'"},
    ],
    "CUT": [
        {"id": 0, "setup": "Dad's dad joke was 20 minutes long. Julia said, 'Let me...'"},
    ],
    "CUTE": [
        {"id": 0, "setup": "Mom showed everyone photos of the grandkids for the 50th time. She said, 'Aren't they...'"},
    ],

    # --- D ---
    "DANCE": [
        {"id": 0, "setup": "Madeleine tried to teach Patrick burlesque moves. It looked less like art and more like a...'"},
    ],
    "DARK": [
        {"id": 0, "setup": "Patrick played video games until 3 AM. His room was completely...'"},
    ],
    "DEAL": [
        {"id": 0, "setup": "Julia offered to let Dad win at Crossplay for a trail ride. He said, 'That's a bad...'"},
    ],
    "DEEP": [
        {"id": 0, "setup": "Dad explained his 47-move Crossplay strategy. Patrick said, 'Wow, that's...'"},
    ],
    "DIG": [
        {"id": 0, "setup": "Madeleine's rescue dog destroyed the garden again. Katie said, 'Why does he always...'"},
    ],
    "DISH": [
        {"id": 0, "setup": "Mom cooked something amazing for the grandkids. Dad said, 'Now that's a...'"},
    ],
    "DOG": [
        {"id": 0, "setup": "Madeleine found another stray. Mom said, 'We already have 3 cats.' Madeleine said, 'But this one's a...'"},
        {"id": 1, "setup": "Dad told a dad joke so bad Julia said, 'You sound like a...'"},
    ],
    "DONE": [
        {"id": 0, "setup": "Mom pulled the roast out at the perfect moment. Patrick asked, 'Is it...'"},
        {"id": 1, "setup": "Dad spent 4 hours analyzing one Crossplay move. Mom said, 'Are you...'"},
    ],
    "DRAW": [
        {"id": 0, "setup": "Julia wanted to settle who was best at Crossplay. Dad said, 'It's a...'"},
    ],
    "DREAM": [
        {"id": 0, "setup": "Patrick said he'd make the NHL someday. Katie said in three languages, 'Keep living the...'"},
    ],
    "DRINK": [
        {"id": 0, "setup": "Patrick opened the fridge. Mom said, 'If you grab another milk, that's your 6th...'"},
    ],
    "DRIVE": [
        {"id": 0, "setup": "Bill3 took his Subaru up a dirt trail. Dad said, 'That's not a road, that's a...'"},
    ],
    "DROP": [
        {"id": 0, "setup": "Katie was carrying her best pottery piece to the kiln when Patrick ran by. She yelled, 'Don't make me...'"},
    ],
    "DRUM": [
        {"id": 0, "setup": "Madeleine added percussion to her burlesque number. She picked up a...'"},
    ],
    "DRY": [
        {"id": 0, "setup": "Dad's dad jokes at dinner were so unfunny, Bill3 said his humor was bone...'"},
    ],

    # --- E ---
    "EAR": [
        {"id": 0, "setup": "Dad whispered his Crossplay strategy so the opponents wouldn't hear. Julia leaned in with one...'"},
    ],
    "EAT": [
        {"id": 0, "setup": "Patrick came home from hockey and stared at the fridge. Mom said, 'You can't possibly still want to...'"},
    ],
    "EDGE": [
        {"id": 0, "setup": "Dad calculated he had a 2.3% advantage in the game. He called it his competitive...'"},
    ],
    "EGG": [
        {"id": 0, "setup": "Katie tried to teach Patrick to cook breakfast. He couldn't even crack an...'"},
    ],

    # --- F ---
    "FACE": [
        {"id": 0, "setup": "Patrick got a goal scored on him in hockey. Coach said, 'Don't lose...'"},
    ],
    "FAIL": [
        {"id": 0, "setup": "Dad's elaborate 12-move Crossplay plan backfired completely. Bill3 said, 'Epic...'"},
    ],
    "FAN": [
        {"id": 0, "setup": "Mom wore her Giants jersey, hat, socks, and face paint. Dad said, 'You're a big...'"},
        {"id": 1, "setup": "Madeleine pulled out the most enormous feather prop for her burlesque act. It was technically a...'"},
    ],
    "FAST": [
        {"id": 0, "setup": "Patrick finished a gallon of milk in one sitting. That was impressively...'"},
        {"id": 1, "setup": "Bill3 typed code so quickly, Dad said the keyboard was on...'"},
    ],
    "FAT": [
        {"id": 0, "setup": "Katie's sourdough loaf came out of the oven perfectly round and...'"},
    ],
    "FEATHER": [
        {"id": 0, "setup": "Madeleine's burlesque costume had so many plumes, she looked like she was wearing every...'"},
    ],
    "FIRE": [
        {"id": 0, "setup": "Katie's pottery kiln was at full blast. Patrick asked, 'Is the kitchen on...'"},
        {"id": 1, "setup": "Mom's fastball at the softball game was pure...'"},
    ],
    "FISH": [
        {"id": 0, "setup": "Madeleine wanted to rescue something from the pet store. Mom said, 'If it lives in water, it's a...'"},
    ],
    "FIT": [
        {"id": 0, "setup": "Patrick tried on his old hockey jersey. It didn't...'"},
        {"id": 1, "setup": "Bill3 tried to sit in the back of a compact car. He didn't...'"},
    ],
    "FLAT": [
        {"id": 0, "setup": "Katie's first attempt at pottery came out completely...'"},
    ],
    "FLY": [
        {"id": 0, "setup": "Mom caught a pop-up at the Giants game while holding a hot dog. Dad said, 'Nice...'"},
        {"id": 1, "setup": "Julia found a bug and told Cayl it was beautiful. He said, 'That's just a...'"},
    ],
    "FOOD": [
        {"id": 0, "setup": "Patrick opened every cabinet in the kitchen. He yelled, 'We have no...'"},
    ],
    "FOUL": [
        {"id": 0, "setup": "Mom disputed the ump's call at the Giants game. She said it was clearly...'"},
    ],
    "FOX": [
        {"id": 0, "setup": "Madeleine found a wild animal in the yard and wanted to keep it. Dad said, 'That's a...'"},
    ],
    "FREE": [
        {"id": 0, "setup": "Madeleine opened the rescue shelter cage and whispered, 'You're...'"},
    ],
    "FROG": [
        {"id": 0, "setup": "Julia found an amphibian on a Boulder hike and named it. Cayl said, 'That's a...'"},
    ],
    "FUN": [
        {"id": 0, "setup": "Dad bought a new gadget to track Crossplay statistics. Everyone stared at him. He said, 'What? This is...'"},
    ],
    "FURY": [
        {"id": 0, "setup": "Mom watched the Giants blow a 5-run lead. Her reaction was pure...'"},
    ],

    # --- G ---
    "GADGET": [
        {"id": 0, "setup": "Dad came home with another electronic device. Mom said, 'Not another...'"},
    ],
    "GALLOP": [
        {"id": 0, "setup": "Julia's horse took off across the field at a full...'"},
    ],
    "GAME": [
        {"id": 0, "setup": "Dad said, 'Crossplay isn't just a game, it's a...'"},
        {"id": 1, "setup": "Patrick paused his video to play Crossplay. He said, 'Fine, but this better be a good...'"},
    ],
    "GHOST": [
        {"id": 0, "setup": "Patrick's hockey team lost 8-0. He said he was playing like a...'"},
    ],
    "GIANT": [
        {"id": 0, "setup": "Mom's favorite baseball player hit a grand slam. She screamed, 'THAT'S MY...'"},
        {"id": 1, "setup": "Bill3 stood up and hit his head on the doorframe. Dad said, 'You're a...'"},
    ],
    "GIFT": [
        {"id": 0, "setup": "Katie made everyone handmade pottery for Christmas. Madeleine said, 'What a...'"},
    ],
    "GLAZE": [
        {"id": 0, "setup": "Katie spent hours getting the perfect finish on her pottery. She whispered, 'Now for the...'"},
    ],
    "GOAL": [
        {"id": 0, "setup": "Patrick scored in overtime and did a knee slide across the kitchen floor. He screamed, 'That's a...'"},
    ],
    "GOAT": [
        {"id": 0, "setup": "Julia won 5 Crossplay games in a row. Mom said, 'She's the...'"},
    ],
    "GOOD": [
        {"id": 0, "setup": "Patrick asked if his milk-chugging speed was a useful talent. Bill3 said, 'Not...'"},
    ],
    "GRAB": [
        {"id": 0, "setup": "Mom set cookies on the counter for the grandkids. She told Patrick, 'Don't you dare...'"},
    ],
    "GRAMMAR": [
        {"id": 0, "setup": "Katie corrected Patrick's text message in three languages. She said, 'It's all about...'"},
    ],
    "GREAT": [
        {"id": 0, "setup": "Dad won one game of Crossplay and called himself the greatest. Bill3 said, 'You're not great, you're just...'"},
    ],
    "GRILL": [
        {"id": 0, "setup": "Dad spent $800 on a new barbecue gadget. Mom said, 'You better learn to use that...'"},
    ],
    "GROUND": [
        {"id": 0, "setup": "Dad told a dad joke: 'What do you call a cow with no legs?' Bill3 already knew the punchline...'"},
        {"id": 1, "setup": "Madeleine's rescue dog dug up the entire yard. Mom said, 'There goes the...'"},
    ],
    "GYM": [
        {"id": 0, "setup": "Bill3 spent 2 hours lifting weights. Patrick spent 2 hours at the snack bar. Bill3 said, 'You know this is a...'"},
    ],

    # --- H ---
    "HACK": [
        {"id": 0, "setup": "Bill3 wrote a script to automate his Yelp reviews. Dad called it a...'"},
    ],
    "HAIR": [
        {"id": 0, "setup": "Mom's long soft white locks flowed in the wind at the Giants game. Dad said, 'Nice...'"},
    ],
    "HAND": [
        {"id": 0, "setup": "Mom caught a foul ball at the Giants game. She didn't even use a glove. Just her bare...'"},
    ],
    "HAT": [
        {"id": 0, "setup": "Patrick scored 3 goals in one game. Coach said, 'That's a...'"},
    ],
    "HAY": [
        {"id": 0, "setup": "Julia was feeding her horse at the barn in Boulder. Cayl said, 'That's a lot of...'"},
    ],
    "HEAT": [
        {"id": 0, "setup": "Katie cranked the pottery kiln to max. Madeleine said, 'Can you feel the...'"},
    ],
    "HEAVY": [
        {"id": 0, "setup": "Bill3 loaded another plate on the barbell. Patrick tried to lift it and said, 'That's...'"},
    ],
    "HERO": [
        {"id": 0, "setup": "Mom caught a foul ball heading for a kid at the Giants game. The stadium called her a...'"},
    ],
    "HIGH": [
        {"id": 0, "setup": "Bill3 reached the top shelf without a ladder. Everyone else needed a step stool. He said, 'Life is good up...'"},
    ],
    "HIT": [
        {"id": 0, "setup": "Mom's Giants were down by 3 in the 9th. She said, 'We just need one more...'"},
        {"id": 1, "setup": "Patrick checked someone into the boards in hockey. Ref said, 'Clean...'"},
    ],
    "HIVE": [
        {"id": 0, "setup": "Julia found a colony of bees on a Boulder hike and was fascinated. Cayl said, 'That's a...'"},
    ],
    "HOLE": [
        {"id": 0, "setup": "Madeleine's rescue dog dug through the fence. Dad looked at the yard and said, 'That's not a divot, that's a...'"},
    ],
    "HOME": [
        {"id": 0, "setup": "The Giants' batter crushed one over the wall. Mom jumped up screaming...'"},
        {"id": 1, "setup": "Patrick came back from hockey practice covered in mud. Mom said, 'Welcome...'"},
    ],
    "HOOF": [
        {"id": 0, "setup": "Julia's horse stomped impatiently at feeding time. She heard the...'"},
    ],
    "HORSE": [
        {"id": 0, "setup": "Julia moved to Boulder and the first thing she did was find a stable. She needed a...'"},
    ],
    "HOT": [
        {"id": 0, "setup": "Katie's pottery came out of the kiln. Patrick tried to pick it up. She screamed, 'It's still...'"},
    ],
    "HUG": [
        {"id": 0, "setup": "Madeleine's rescue dog knocked Dad over with affection. She said, 'He just wants a...'"},
    ],

    # --- I ---
    "ICE": [
        {"id": 0, "setup": "Patrick spent more time on the hockey rink than at school. Mom said, 'You're basically made of...'"},
    ],
    "IRE": [
        {"id": 0, "setup": "The Giants lost on a bad call. Mom's face was full of...'"},
    ],
    "IRON": [
        {"id": 0, "setup": "Bill3 pumped so much iron at the gym, Patrick said he was basically made of...'"},
    ],

    # --- J ---
    "JAM": [
        {"id": 0, "setup": "Mom made homemade preserves for the grandkids. Patrick ate the whole jar with a spoon. She said, 'That's not how you eat...'"},
    ],
    "JAR": [
        {"id": 0, "setup": "Katie's newest pottery project was meant to be a vase, but Dad said it looked more like a...'"},
    ],
    "JET": [
        {"id": 0, "setup": "Patrick drank three Red Bulls before hockey. He was moving like a...'"},
    ],
    "JOB": [
        {"id": 0, "setup": "Bill3 fixed a production bug at 2 AM. His boss said, 'Good...'"},
    ],
    "JOKE": [
        {"id": 0, "setup": "Dad tried his best dad joke during Crossplay. Everyone stared. He said, 'That was a...'"},
        {"id": 1, "setup": "Bill3 told a pun so bad even Dad was impressed. Patrick said, 'That's not a pun, that's a...'"},
    ],
    "JOY": [
        {"id": 0, "setup": "Madeleine adopted her 4th rescue animal. The look on her face was pure...'"},
    ],
    "JUDGE": [
        {"id": 0, "setup": "Katie entered her pottery in a competition. Patrick ate the entry form. She said, 'Don't you...'"},
    ],
    "JUICE": [
        {"id": 0, "setup": "Patrick ran out of milk. He had to drink something else. He grabbed the...'"},
    ],

    # --- K ---
    "KEEN": [
        {"id": 0, "setup": "Dad analyzed everyone's Crossplay stats before breakfast on his new gadget. Mom said, 'You're very...'"},
    ],
    "KEY": [
        {"id": 0, "setup": "Bill3 asked Dad what the secret to winning Crossplay was. He started a 30-minute lecture. Bill3 said, 'Just give me the...'"},
    ],
    "KICK": [
        {"id": 0, "setup": "Patrick tried to play soccer with a hockey stick. Coach said, 'Just use a...'"},
    ],
    "KILN": [
        {"id": 0, "setup": "Katie's pottery studio in Berkeley smelled like a volcano. Dad asked, 'Is that a furnace or a...'"},
    ],
    "KING": [
        {"id": 0, "setup": "Dad won 2 Crossplay games in a row and demanded a crown. Bill3 said, 'You're not a...'"},
    ],
    "KITE": [
        {"id": 0, "setup": "Julia's hat blew off on a windy Boulder trail ride. She said, 'There goes my...'"},
    ],

    # --- L ---
    "LAMP": [
        {"id": 0, "setup": "Katie made a ceramic light fixture on the potter's wheel. Patrick said, 'Is that a bowl or a...'"},
    ],
    "LATE": [
        {"id": 0, "setup": "Patrick showed up to hockey practice an hour behind schedule. Coach said, 'You're...'"},
    ],
    "LAUGH": [
        {"id": 0, "setup": "Dad made a dad joke during Crossplay. Nobody reacted. He said, 'Come on, at least...'"},
    ],
    "LEAD": [
        {"id": 0, "setup": "Mom's Giants were up by 7 in the 3rd inning. She said, 'That's a comfortable...'"},
    ],
    "LEMON": [
        {"id": 0, "setup": "Mom squeezed too much citrus into the recipe for the grandkids. Patrick took a sip and said, 'That's a...'"},
    ],
    "LIFT": [
        {"id": 0, "setup": "Bill3 asked Patrick to spot him at the gym. Patrick said, 'That's a lot of...'"},
    ],
    "LIGHT": [
        {"id": 0, "setup": "Madeleine's burlesque show needed better stage effects. She yelled, 'Someone get me a...'"},
    ],
    "LION": [
        {"id": 0, "setup": "Madeleine's rescue cat thought it was a big jungle predator. Dad said, 'That's not a housecat, that's a...'"},
    ],
    "LOAF": [
        {"id": 0, "setup": "Katie's fresh sourdough came out of the oven looking perfect. Patrick called it a...'"},
    ],
    "LOCK": [
        {"id": 0, "setup": "Patrick kept eating all the leftovers. Katie put a padlock on the fridge. She said, 'Time for a...'"},
    ],
    "LOG": [
        {"id": 0, "setup": "Bill3 checked the server output to debug his code. He needed to read the...'"},
    ],
    "LONG": [
        {"id": 0, "setup": "Mom's beautiful white hair reached past her shoulders. Katie said, 'It's so...'"},
    ],
    "LOST": [
        {"id": 0, "setup": "Dad's elaborate Crossplay strategy didn't work. Again. Mom said, 'You...'"},
    ],
    "LOVE": [
        {"id": 0, "setup": "Madeleine introduced her newest rescue puppy to the family. She said, 'It was...'"},
    ],
    "LUCK": [
        {"id": 0, "setup": "Julia drew all the blanks in Crossplay and played a 90-point bingo. Dad said, 'That's not skill, that's...'"},
    ],

    # --- M ---
    "MAD": [
        {"id": 0, "setup": "The ump called strike three on a pitch in the dirt. Mom was...'"},
    ],
    "MAP": [
        {"id": 0, "setup": "Dad made a diagram of all possible Crossplay strategies on his new tablet. Katie said, 'That's not a plan, it's a...'"},
    ],
    "MARE": [
        {"id": 0, "setup": "Julia found the perfect horse at a Boulder stable. She said, 'She's not just any horse, she's a...'"},
    ],
    "MASK": [
        {"id": 0, "setup": "Patrick's hockey goalie equipment was so big, Bill3 said he looked like he was wearing a...'"},
    ],
    "MEAL": [
        {"id": 0, "setup": "Mom cooked for 3 hours for the grandkids. Patrick finished it in 4 minutes. She said, 'That was supposed to be a...'"},
    ],
    "MESS": [
        {"id": 0, "setup": "Patrick's room after a video game marathon was a complete...'"},
        {"id": 1, "setup": "Madeleine's rescue animals rearranged the living room furniture. Mom called it a...'"},
    ],
    "MILK": [
        {"id": 0, "setup": "Patrick opened the fridge. There was only one thing he was looking for...'"},
        {"id": 1, "setup": "Everyone else had water with dinner. Patrick had a tall glass of...'"},
    ],
    "MISS": [
        {"id": 0, "setup": "Patrick took a slapshot and hit the glass instead of the net. That's a...'"},
    ],
    "MIX": [
        {"id": 0, "setup": "Madeleine combined burlesque choreography with her latest indie playlist. She called it a...'"},
    ],
    "MOLD": [
        {"id": 0, "setup": "Katie pressed clay into a shape on the wheel at her Berkeley studio. She called it a...'"},
    ],
    "MOON": [
        {"id": 0, "setup": "Julia and Cayl went stargazing in Boulder. She pointed up at the...'"},
    ],
    "MOTH": [
        {"id": 0, "setup": "Julia caught an insect fluttering around the porch light. She said, 'Look at this beautiful...'"},
    ],
    "MOVE": [
        {"id": 0, "setup": "Dad spent 40 minutes on his Crossplay turn. Katie said, 'Just make a...'"},
    ],
    "MUG": [
        {"id": 0, "setup": "Katie made a gorgeous ceramic drinking vessel. Patrick immediately filled it with milk. She said, 'That was supposed to be an art piece, not a...'"},
    ],
    "MUD": [
        {"id": 0, "setup": "Madeleine's rescue dog came inside after the rain covered in...'"},
    ],
    "MUSCLE": [
        {"id": 0, "setup": "Bill3 flexed after a PR at the gym. Patrick poked his arm and said, 'That's a...'"},
    ],

    # --- N ---
    "NAP": [
        {"id": 0, "setup": "Dad fell asleep during his own Crossplay strategy lecture. Patrick said, 'He's taking a...'"},
    ],
    "NEAT": [
        {"id": 0, "setup": "Bill3 organized his code into perfect modules. Dad said, 'That's...'"},
    ],
    "NEST": [
        {"id": 0, "setup": "Madeleine found baby birds in the yard and built them a...'"},
    ],
    "NET": [
        {"id": 0, "setup": "Patrick's slapshot went wide. Coach pointed and said, 'That thing over there is called the...'"},
    ],
    "NEW": [
        {"id": 0, "setup": "Madeleine came home with another rescue animal. Mom said, 'Oh no, not a...'"},
        {"id": 1, "setup": "Dad bought another gadget. Mom said, 'Not another...'"},
    ],
    "NIGHT": [
        {"id": 0, "setup": "Patrick played video games until dawn. He said it was still...'"},
    ],
    "NOISE": [
        {"id": 0, "setup": "Madeleine was practicing a new song at full volume. Patrick's headset couldn't block the...'"},
    ],
    "NOUN": [
        {"id": 0, "setup": "Katie was teaching English grammar to her TESOL students. She said, 'First, let's talk about the...'"},
    ],
    "NUT": [
        {"id": 0, "setup": "Dad tried to calculate the optimal Crossplay opening on his tablet. Bill3 said, 'You're a...'"},
    ],

    # --- O ---
    "OAK": [
        {"id": 0, "setup": "Dad wanted to build a bookshelf for his Crossplay strategy manuals. Katie said, 'Use...'"},
    ],
    "OAR": [
        {"id": 0, "setup": "The family canoe trip went sideways when Patrick dropped his...'"},
    ],
    "OAT": [
        {"id": 0, "setup": "Patrick put milk on everything. Even his morning bowl of...'"},
    ],
    "ODD": [
        {"id": 0, "setup": "Madeleine's burlesque-rescue-animal themed birthday party was admittedly a little...'"},
    ],
    "OLD": [
        {"id": 0, "setup": "Dad pulled out his college Scrabble set. Katie said, 'That thing is...'"},
    ],
    "OUT": [
        {"id": 0, "setup": "Mom watched the Giants pitcher throw strike three. She pumped her fist and yelled, 'You're...'"},
    ],
    "OVEN": [
        {"id": 0, "setup": "Mom's kitchen was 100 degrees while she cooked for the grandkids. Patrick walked in and said, 'Why is it so hot?' She pointed at the...'"},
    ],
    "OWL": [
        {"id": 0, "setup": "Julia spotted a nocturnal bird on a Boulder hike. She whispered, 'Look, an...'"},
    ],

    # --- P ---
    "PAN": [
        {"id": 0, "setup": "Katie reached for her favorite cooking tool. Patrick was using it as a hockey stick. She said, 'Give me back my...'"},
    ],
    "PASS": [
        {"id": 0, "setup": "Dad couldn't find a single good move in Crossplay. He had to...'"},
    ],
    "PAW": [
        {"id": 0, "setup": "Madeleine's rescue dog put his foot on Dad's gadget during a Crossplay analysis. She said, 'He's giving you a...'"},
    ],
    "PET": [
        {"id": 0, "setup": "Madeleine asked if she could get just one more rescue animal. Mom said, 'Absolutely no more...'"},
    ],
    "PHONE": [
        {"id": 0, "setup": "Dad bought the newest smartphone. Mom said, 'You just got a new gadget last week.' He said, 'That wasn't a gadget, it was a...'"},
    ],
    "PIE": [
        {"id": 0, "setup": "Mom baked something beautiful for the grandkids. Patrick guessed wrong and called it a cake. She said, 'It's a...'"},
    ],
    "PIG": [
        {"id": 0, "setup": "Patrick ate the entire Thanksgiving turkey. Bill3 called him a...'"},
    ],
    "PIN": [
        {"id": 0, "setup": "Madeleine's burlesque costume kept falling apart. She needed one more...'"},
    ],
    "PITCH": [
        {"id": 0, "setup": "Mom threw the first ball at the Giants charity game. The catcher said, 'Nice...'"},
    ],
    "PLAN": [
        {"id": 0, "setup": "Dad drew a 47-step Crossplay strategy on his tablet. Bill3 deleted it and said, 'Bad...'"},
    ],
    "PLATE": [
        {"id": 0, "setup": "Katie made a beautiful ceramic dish. Patrick immediately loaded it with Skittles. She said, 'It's not a candy...'"},
    ],
    "PLAY": [
        {"id": 0, "setup": "Dad asked who wanted to do Crossplay. Everyone groaned. He said, 'Come on, let's...'"},
    ],
    "PLUCK": [
        {"id": 0, "setup": "Madeleine rescued a chicken from the side of the road. Dad said, 'That takes...'"},
    ],
    "POINT": [
        {"id": 0, "setup": "Dad explained Crossplay scoring for 15 minutes. Julia said, 'What's the...'"},
    ],
    "POKE": [
        {"id": 0, "setup": "Julia kept tapping Dad's arm during his Crossplay turn. He said, 'Stop trying to...'"},
    ],
    "PONY": [
        {"id": 0, "setup": "Julia wanted a full-sized horse. Cayl said, 'Start with a...'"},
    ],
    "POT": [
        {"id": 0, "setup": "Katie threw clay on the wheel and started spinning. She was making a...'"},
    ],
    "POUR": [
        {"id": 0, "setup": "Patrick lifted the gallon of milk. Mom said, 'Carefully...'"},
    ],
    "PUCK": [
        {"id": 0, "setup": "Patrick's hockey teammates said he was better at drinking milk than handling a...'"},
    ],
    "PUN": [
        {"id": 0, "setup": "Dad told a wordplay joke. Bill3 groaned. Dad said, 'That's not a joke, it's a...'"},
    ],

    # --- Q ---
    "QUAKE": [
        {"id": 0, "setup": "Dad's reaction when Julia beat him at Crossplay made the whole table...'"},
    ],
    "QUEEN": [
        {"id": 0, "setup": "Madeleine walked out in her burlesque crown. Katie said, 'Drama...'"},
    ],
    "QUEST": [
        {"id": 0, "setup": "Patrick said finding Skittles at midnight was basically a heroic...'"},
    ],
    "QUICK": [
        {"id": 0, "setup": "Bill3 played his Crossplay move in 3 seconds flat. Dad spent 40 minutes. Bill3 said, 'Be...'"},
    ],
    "QUIET": [
        {"id": 0, "setup": "Dad was concentrating on his Crossplay move. Everyone was talking. He said, 'Please be...'"},
    ],
    "QUIT": [
        {"id": 0, "setup": "Dad was losing by 200 points. Bill3 said, 'You can always...'"},
    ],

    # --- R ---
    "RACE": [
        {"id": 0, "setup": "Patrick chugged a glass of milk in 4 seconds. Bill3 challenged him to a...'"},
    ],
    "RACK": [
        {"id": 0, "setup": "Bill3 put the weights back at the gym in perfect order. He said, 'Always re...'"},
    ],
    "RAIN": [
        {"id": 0, "setup": "The Giants game got delayed. Mom stared at the sky cursing the...'"},
    ],
    "RAINBOW": [
        {"id": 0, "setup": "Patrick sorted his Skittles by color and called it a...'"},
    ],
    "RAW": [
        {"id": 0, "setup": "Patrick tried to eat Katie's cookie dough before she baked it. She said, 'That's...'"},
    ],
    "REIN": [
        {"id": 0, "setup": "Julia's horse was getting excited. She pulled back on the...'"},
    ],
    "REVIEW": [
        {"id": 0, "setup": "Bill3 left a 2,000-word Yelp essay about a taco truck. Katie said, 'That's not a review, it's a...'"},
    ],
    "RIDE": [
        {"id": 0, "setup": "Julia saddled up her horse in Boulder. Cayl said, 'Enjoy the...'"},
        {"id": 1, "setup": "Bill3 took his Subaru off-road. Dad said, 'That's quite a...'"},
    ],
    "RING": [
        {"id": 0, "setup": "Cayl showed Julia a sparkly little box in Boulder. Inside was a...'"},
    ],
    "ROAST": [
        {"id": 0, "setup": "Mom put a beautiful piece of meat in the oven. Bill3 said, 'That or Dad's Crossplay strategy -- either way, it's a...'"},
    ],
    "ROCK": [
        {"id": 0, "setup": "Julia and Cayl went climbing near Boulder. She grabbed the...'"},
    ],
    "ROLL": [
        {"id": 0, "setup": "Mom's fresh bread came out of the oven for the grandkids. Patrick grabbed a...'"},
    ],
    "ROOM": [
        {"id": 0, "setup": "Patrick's bedroom after a video game marathon had no visible floor. Mom said, 'Clean your...'"},
    ],
    "RUN": [
        {"id": 0, "setup": "Mom's Giants scored on a wild pitch. She screamed, 'That's a...'"},
    ],
    "RUNT": [
        {"id": 0, "setup": "Madeleine adopted the smallest puppy at the shelter. She said, 'The...'"},
    ],

    # --- S ---
    "SADDLE": [
        {"id": 0, "setup": "Julia was getting ready for a trail ride. She reached for the...'"},
    ],
    "SAFE": [
        {"id": 0, "setup": "The Giants runner slid into home plate. Mom was on her feet screaming...'"},
    ],
    "SALT": [
        {"id": 0, "setup": "Katie's recipe called for a pinch. Patrick dumped in a cup of...'"},
    ],
    "SAVE": [
        {"id": 0, "setup": "Patrick's goalie made a diving stop. The crowd yelled, 'What a...'"},
    ],
    "SCORE": [
        {"id": 0, "setup": "Dad obsessively tracked every Crossplay game on his tablet. Mom said, 'Nobody cares about the...'"},
        {"id": 1, "setup": "Patrick's hockey team finally won. He screamed, 'What's the...'"},
    ],
    "SEAL": [
        {"id": 0, "setup": "Madeleine watched a marine animal documentary and said, 'I want to rescue a...'"},
    ],
    "SHARK": [
        {"id": 0, "setup": "Bill3 quietly destroyed everyone at Crossplay. Dad said, 'He's a...'"},
    ],
    "SHELF": [
        {"id": 0, "setup": "Katie's pottery collection outgrew the display. She needed another...'"},
    ],
    "SHINE": [
        {"id": 0, "setup": "Katie polished her glazed pottery until it had a perfect...'"},
    ],
    "SHOT": [
        {"id": 0, "setup": "Patrick wound up for the biggest slapshot of the game and... he took the...'"},
    ],
    "SING": [
        {"id": 0, "setup": "Madeleine started her new song for the burlesque number. She said, 'Watch me...'"},
    ],
    "SINK": [
        {"id": 0, "setup": "Patrick piled every dish in the kitchen. Mom pointed and said, 'They go in the...'"},
    ],
    "SIT": [
        {"id": 0, "setup": "Madeleine tried to train her rescue dog. The first command was...'"},
    ],
    "SKIP": [
        {"id": 0, "setup": "Patrick wanted to skip school for a hockey tournament. Mom said, 'You can't just...'"},
    ],
    "SLEEP": [
        {"id": 0, "setup": "Patrick played video games until 4 AM. His one weakness was...'"},
    ],
    "SLIDE": [
        {"id": 0, "setup": "Mom's Giants runner was heading home. She screamed, 'You better...'"},
    ],
    "SLOW": [
        {"id": 0, "setup": "Dad took 35 minutes for one Crossplay move. Patrick said, 'You're so...'"},
    ],
    "SMART": [
        {"id": 0, "setup": "Katie spoke 3 languages fluently. Dad said, 'That's suspiciously...'"},
    ],
    "SNACK": [
        {"id": 0, "setup": "Patrick reached for the Skittles after eating dinner. He said, 'I need a...'"},
    ],
    "SNORE": [
        {"id": 0, "setup": "Dad fell asleep explaining Crossplay strategy to Madeleine. She heard him...'"},
    ],
    "SONG": [
        {"id": 0, "setup": "Madeleine was composing something new for her burlesque act. She said, 'I just need the right...'"},
    ],
    "SOUP": [
        {"id": 0, "setup": "Mom made a beautiful broth from scratch. Patrick put milk in it. She said, 'That's not how you make...'"},
    ],
    "SPARK": [
        {"id": 0, "setup": "Madeleine's burlesque act had pyrotechnics this time. One tiny...'"},
    ],
    "SPELL": [
        {"id": 0, "setup": "Katie quizzed her TESOL students at Berkeley. She said, 'Can you...'"},
    ],
    "SPILL": [
        {"id": 0, "setup": "Patrick knocked over his glass of milk. For the third time today. Mom said, 'Another...'"},
    ],
    "SPIN": [
        {"id": 0, "setup": "Katie's pottery wheel was going full speed. She told Patrick, 'Don't touch it while it's in a...'"},
    ],
    "STABLE": [
        {"id": 0, "setup": "Julia found the perfect place to board her horse near Boulder. She said, 'This is a great...'"},
    ],
    "STAGE": [
        {"id": 0, "setup": "Madeleine converted the living room into a burlesque performance area. She called it a...'"},
    ],
    "STAR": [
        {"id": 0, "setup": "Bill3 won Crossplay for the 10th time. Patrick said, 'OK, you're a...'"},
    ],
    "STAY": [
        {"id": 0, "setup": "Madeleine told her rescue dog to sit, lie down, and...'"},
    ],
    "STEAL": [
        {"id": 0, "setup": "Mom's Giants runner took second base. She yelled, 'That's a...'"},
    ],
    "STICK": [
        {"id": 0, "setup": "Patrick broke another hockey implement. Mom said, 'That's the 4th...'"},
    ],
    "STOP": [
        {"id": 0, "setup": "Patrick was chugging milk straight from the jug. Mom walked in and yelled...'"},
    ],
    "STOVE": [
        {"id": 0, "setup": "Mom was cooking 4 things at once for the grandkids. Patrick asked, 'What's on the...'"},
    ],
    "STRIKE": [
        {"id": 0, "setup": "Mom watched the Giants pitcher throw a perfect fastball right down the middle...'"},
    ],
    "STRONG": [
        {"id": 0, "setup": "Bill3 deadlifted 405 pounds. Patrick tried and couldn't move the bar. He said, 'You're really...'"},
    ],
    "STUNT": [
        {"id": 0, "setup": "Madeleine added an acrobatic flip to her burlesque routine. Katie said, 'That's quite a...'"},
    ],
    "SUBARU": [
        {"id": 0, "setup": "Bill3 drove through 2 feet of snow like it was nothing. He said, 'That's the power of a...'"},
    ],
    "SWEEP": [
        {"id": 0, "setup": "Bill3 used all 7 tiles in Crossplay. Dad calculated it was a...'"},
    ],
    "SWEET": [
        {"id": 0, "setup": "Patrick poured Skittles into his cereal. Mom said, 'That's too...'"},
    ],

    # --- T ---
    "TACO": [
        {"id": 0, "setup": "Bill3 left a 5-star Yelp review for a food truck. His favorite item was the...'"},
    ],
    "TAG": [
        {"id": 0, "setup": "The Giants catcher caught the runner at home. Mom screamed, 'You're out!...'"},
    ],
    "TAIL": [
        {"id": 0, "setup": "Julia's horse swished away the flies with her...'"},
    ],
    "TALK": [
        {"id": 0, "setup": "Katie was explaining verb tenses in her Berkeley TESOL class. She said, 'Let's...'"},
    ],
    "TALL": [
        {"id": 0, "setup": "Bill3 stood next to Patrick for a photo. The height difference was absurdly...'"},
    ],
    "TANK": [
        {"id": 0, "setup": "Patrick's hockey team lost 12-0. He said, 'We didn't just lose, we...'"},
    ],
    "TAP": [
        {"id": 0, "setup": "Madeleine's burlesque routine included a little...'"},
    ],
    "TEACH": [
        {"id": 0, "setup": "Katie's TESOL students loved her classes at Berkeley. She was born to...'"},
    ],
    "TEAM": [
        {"id": 0, "setup": "Mom wore Giants gear head to toe and said, 'I'm supporting my...'"},
    ],
    "THROW": [
        {"id": 0, "setup": "Katie tried to teach Patrick pottery. He got clay everywhere. She said, 'Don't just...'"},
    ],
    "TILE": [
        {"id": 0, "setup": "Dad lovingly arranged his Crossplay letters in alphabetical order. He whispered, 'Every...'"},
    ],
    "TIME": [
        {"id": 0, "setup": "Dad spent 45 minutes on one Crossplay turn. Everyone yelled...'"},
    ],
    "TOAST": [
        {"id": 0, "setup": "Bill3 asked what bread's favorite party activity is. Dad said, 'Making a...'"},
        {"id": 1, "setup": "Mom burned the bread again while chasing a grandkid. Patrick said, 'I still want the...'"},
    ],
    "TOP": [
        {"id": 0, "setup": "Bill3 beat everyone at Crossplay again. He said, 'I'm on...'"},
    ],
    "TRADE": [
        {"id": 0, "setup": "Dad wanted to exchange his Crossplay tiles. Bill3 said, 'Bad...'"},
    ],
    "TRAIL": [
        {"id": 0, "setup": "Julia and Cayl went horseback riding in the mountains outside Boulder. They found a great...'"},
    ],
    "TRAP": [
        {"id": 0, "setup": "Katie hid the Skittles on a high shelf. Patrick still found them. She said, 'I need a better...'"},
    ],
    "TREAT": [
        {"id": 0, "setup": "Madeleine's rescue dogs heard the crinkle of a bag. They all came running for a...'"},
    ],
    "TRICK": [
        {"id": 0, "setup": "Patrick tried a spin move in hockey and fell on his face. Coach said, 'Nice...'"},
    ],
    "TRIP": [
        {"id": 0, "setup": "The whole family planned a vacation. Dad brought his Crossplay board. Mom said, 'It's a...'"},
    ],
    "TROT": [
        {"id": 0, "setup": "Julia's horse started at a walk, then picked up to a...'"},
    ],
    "TUNE": [
        {"id": 0, "setup": "Madeleine was humming something new for her burlesque number. She said, 'I can't get this...'"},
    ],
    "TURN": [
        {"id": 0, "setup": "Dad took forever analyzing his Crossplay tiles. Patrick yelled, 'It's your...'"},
    ],
    "TWIST": [
        {"id": 0, "setup": "Madeleine's burlesque act had an unexpected ending. She called it a plot...'"},
    ],
    "TYPE": [
        {"id": 0, "setup": "Bill3 was coding so fast his fingers were a blur. Katie said, 'Slow down, you don't need to...'"},
    ],

    # --- U ---
    "UMP": [
        {"id": 0, "setup": "Mom disagreed with every call at the Giants game. She wanted a new...'"},
    ],

    # --- V ---
    "VASE": [
        {"id": 0, "setup": "Katie's latest pottery piece was tall and elegant. She said, 'It's a...'"},
    ],
    "VERB": [
        {"id": 0, "setup": "Katie was drilling her TESOL students on conjugation. She said, 'Give me a...'"},
    ],
    "VET": [
        {"id": 0, "setup": "Madeleine's rescue animals needed checkups. She basically lived at the...'"},
    ],
    "VINE": [
        {"id": 0, "setup": "Madeleine's rescue parrot chewed through Mom's garden plant. It was a...'"},
    ],

    # --- W ---
    "WAIT": [
        {"id": 0, "setup": "Dad was on minute 38 of his Crossplay turn. Everyone said...'"},
    ],
    "WALK": [
        {"id": 0, "setup": "Madeleine's rescue dogs all needed to go outside. She said, 'Time for a...'"},
    ],
    "WALL": [
        {"id": 0, "setup": "Patrick hit a slapshot so hard it went through the garage...'"},
    ],
    "WARM": [
        {"id": 0, "setup": "Mom's fresh bread came out of the oven for the grandkids. She said, 'It's still...'"},
    ],
    "WATER": [
        {"id": 0, "setup": "Patrick was offered something to drink that wasn't milk. He said, 'I don't do...'"},
    ],
    "WHEEL": [
        {"id": 0, "setup": "Katie sat down at the pottery studio in Berkeley and started to spin the...'"},
    ],
    "WHIP": [
        {"id": 0, "setup": "Mom was making cream for the pie. She said, 'Someone help me...'"},
    ],
    "WILD": [
        {"id": 0, "setup": "Mom watched the Giants throw a pitch in the dirt. She yelled...'"},
    ],
    "WIN": [
        {"id": 0, "setup": "Dad finally beat Bill3 at Crossplay after 15 games. He screamed, 'FINALLY, A...'"},
        {"id": 1, "setup": "Mom's Giants clinched the division. She said, 'That's a...'"},
    ],
    "WINK": [
        {"id": 0, "setup": "Madeleine finished her burlesque number with a little...'"},
    ],
    "WIPE": [
        {"id": 0, "setup": "Patrick's milk mustache was enormous. Mom brushed her long white hair aside and handed him a napkin and said...'"},
    ],
    "WISH": [
        {"id": 0, "setup": "Julia made a wish while riding her horse through a Boulder meadow. She made a...'"},
    ],
    "WOLF": [
        {"id": 0, "setup": "Patrick ate dinner so fast, Katie said, 'You eat like a...'"},
    ],
    "WOOD": [
        {"id": 0, "setup": "Dad tried to build Katie a pottery shelf with a new power tool. He spent 6 hours staring at...'"},
    ],
    "WORD": [
        {"id": 0, "setup": "Katie was teaching vocabulary to her TESOL class. She said, 'Today's...'"},
    ],
    "WORK": [
        {"id": 0, "setup": "Bill3 asked Dad what Crossplay strategy was. Dad said, 'Hard...'"},
    ],
    "WRAP": [
        {"id": 0, "setup": "Mom's tortillas were perfectly round. Madeleine tried to make one and it looked like a modern art...'"},
    ],

    # --- X ---
    "XI": [
        {"id": 0, "setup": "Dad played a two-letter word for 40 points. Patrick said, 'That's not even a word, it's a...'"},
    ],

    # --- Y ---
    "YAWN": [
        {"id": 0, "setup": "Dad was explaining Crossplay scoring rules. Patrick let out a massive...'"},
    ],
    "YELL": [
        {"id": 0, "setup": "Mom disagreed with the ump at the Giants game. She started to...'"},
    ],
    "YELP": [
        {"id": 0, "setup": "Bill3 ate at a new restaurant and immediately pulled out his phone. He needed to leave a...'"},
    ],

    # --- Z ---
    "ZAP": [
        {"id": 0, "setup": "Bill3 beat Dad at Crossplay in 6 moves. Dad felt the...'"},
    ],
    "ZEAL": [
        {"id": 0, "setup": "Madeleine showed up to adopt another animal with incredible...'"},
    ],
    "ZERO": [
        {"id": 0, "setup": "Patrick's hockey team lost again. Final score: something to...'"},
    ],
    "ZONE": [
        {"id": 0, "setup": "Dad stared at the Crossplay board for 20 minutes without blinking. He was in the...'"},
    ],
    "ZOO": [
        {"id": 0, "setup": "Madeleine had so many rescue animals, the house was basically a...'"},
    ],
}


# =============================================================================
# TEMPLATE JOKES -- fallbacks for words not in the database
# {word} gets replaced with the actual word played
# =============================================================================

TEMPLATE_JOKES = [
    "Patrick looked at the board and whispered, '{word}.' Nobody laughed. Classic Patrick.",
    "Dad spent 47 minutes calculating the perfect move. Bill3 played {word} in 2 seconds flat.",
    "Katie whispered '{word}' while glazing a pot at Berkeley. It shattered. Coincidence? Probably.",
    "Madeleine said '{word}' was the name of her newest rescue animal.",
    "Mom said the Giants once won a game on a play called the '{word}.' Nobody fact-checked her.",
    "Patrick tried to say '{word}' but his mouth was full of Skittles.",
    "Bill3 left a Yelp review that just said '{word}.' It got 47 helpful votes.",
    "Dad's new gadget predicted this exact move: '{word}.' For once, the gadget was right.",
    "Madeleine choreographed an entire burlesque number around the word '{word}.'",
    "Mom baked a cake shaped like the word '{word}' for the grandkids. Patrick ate it before anyone saw.",
    "Patrick yelled '{word}!' during hockey practice. Coach was confused.",
    "Mom argued with the TV umpire and yelled, '{word}!' Dad changed the channel.",
    "Julia named her horse after the word '{word}.' Cayl was not consulted.",
    "Madeleine wrote a song with '{word}' as the chorus. It slaps.",
    "Dad made a 30-slide PowerPoint about why '{word}' was the optimal play.",
    "Katie put '{word}' on a ceramic tile at her Berkeley studio. It's in a gallery now. Probably.",
    "Patrick Googled '{word}' and got distracted by a video game ad. Typical.",
    "Mom said if the Giants had more '{word},' they'd win the World Series.",
    "Bill3 coded an app called '{word}.' It has 3 users. All family members.",
    "Madeleine dramatically revealed the word '{word}' from behind a feather fan.",
    "Dad told a dad joke about '{word}.' Nobody laughed. He laughed enough for everyone.",
    "Patrick said '{word}' reminded him of Skittles. Everything reminds Patrick of Skittles.",
    "Katie threw '{word}' on the pottery wheel. It became a bowl. Everything becomes a bowl.",
    "Mom compared '{word}' to a Giants double play. The analogy made no sense but she committed.",
    "Bill3 said, '{word}.' Then he won. His Subaru bumper sticker says the same thing.",
    "Madeleine's rescue hamster ran across the keyboard and typed '{word}.' Smarter than Patrick.",
    "Dad wrote '{word}' in his Crossplay journal. Page 847. He has a Crossplay journal.",
    "Katie explained what '{word}' means in 4 different languages. Patrick understood none of them.",
    "Mom named her fantasy baseball team 'The {word}s.' They're in first place.",
    "Julia found a bug in Boulder and named it '{word}.' Cayl wasn't surprised.",
]


def get_joke(word, told_set):
    """Return an untold joke for this word, or None if all told / no jokes exist."""
    candidates = JOKES.get(word.upper(), [])
    for joke in candidates:
        if (word.upper(), joke['id']) not in told_set:
            return joke
    return None


def get_template_joke(word):
    """Return a random template joke with the word substituted."""
    template = random.choice(TEMPLATE_JOKES)
    return template.format(word=word)
