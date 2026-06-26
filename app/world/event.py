import random

from app.player.character import BlackMage, Brawler, Monk, RogueArcher


class Events:
    def avoid_battle(self):
        run_chance = random.randint(1, 10)

        if run_chance > 5:
            print("You escaped in the nick of time. Live to fight another day.")
            return True

        print("You can't escape. It's time for battle!")
        return False

    def pick_character(self):
        print('''
You have four warriors to choose from who will adventure in the land of Ketlyv.

1. Ser Branoc, the Unbroken Crest


        /\_/\                 .-^^^^^^^^^-.                 /\_/\
   ____/ / \ \____        .-'  RHOM-GHAL  '-.        ____/ / \ \____
  /___  /___\  ___\______/___________________\______/___  /___\  ___\
      | |   | |      _.-' /\    /\    /\    /\ '-._      | |   | |
   ___|_|___|_|___.-'    /  \__/  \__/  \__/  \    '-.___|_|___|_|___
  /  /\   /\   /\ \    / /\  /\  /\  /\  /\ \    / /\   /\   /\  \
 /__/  \_/  \_/  \_\  /_/  \/  \/  \/  \/  \_\  /_/  \_/  \_/  \__\
 |                  \ |      .---------------.      | /                  |
 |   THE UNBROKEN    \|    .'  /\   /\   /\   '.    |/    THIRD GATE    |
 |      CREST         |   /   /  \_/  \_/  \    \   |      SENTINEL     |
 |                    |  |   / /\   /\   /\  \   |  |                   |
 |      /\    /\      |  |  /_/  \_/  \_/  \__\  |  |      /\    /\     |
 |_____/  \__/  \_____|  |       __________       |  |_____/  \__/  \____|
 \                  /   |      /  ______  \      |   \                   /
  \_________________/    |     /__/|    |\__\     |    \_________________/
        \                |     |  || /\ ||  |     |                /
         '---------------|     |__||_||_||__|     |---------------'
                         '--------\_||_/--------'
              .============ HONOR  DUTY  ENDURE ============.
               '============================================'

Exiled Sentinel of Rhom-Ghal

From the Iron-Spires of Rhom-Ghal comes a knight without a crest. Once Lord-Commander of the mountain vanguard, Branoc 
surrendered his name, rank, and homeland to spare the soldiers under his command. Now he wanders the outer kingdoms in 
scarred Deep-Iron plate, accepting no gold for his sword, only provisions and information. Behind the narrow grilles of 
his helm is no revenant or cursed immortal. Branoc is flesh and blood, sustained by the Rhom-Ghalian Lung, a punishing 
discipline that allows the mountain knights to fight through thin air, smoke, exhaustion, and pain. He carries 
Sunder-Spire, a massive Great-Flamberge forged from broken Deep-Iron. Its rippled edge tears through guards and 
chainmail, while Branoc’s weight and momentum turn every swing into a crushing advance.

He has entered the dungeon in search of a lost mark of the Third Gate, believing it may lead him to the scattered 
remnants of his fallen order. He does not know what waits beneath the stone.

Heavy Vanguard

Branoc is slow, durable, and difficult to interrupt. He controls space through sweeping attacks, heavy stagger, 
and relentless forward pressure.

Strengths: Defense, endurance, guard breaking, crowd control
Weaknesses: Speed, recovery time, limited mobility
Weapon: Sunder-Spire
Discipline: Rhom-Ghalian Lung

“Endurance is merely suffering with direction.”

2. Azhvielle, the Unconfessed

                                     o                                     
                                    (o)                                    
                                     |                                     
                                  .--^--.                                  
                               .-'  /|\  '-.                               
                             --<   / | \   >--                             
      |       |   .-------------------------------------.   |       |      
         \     /   .-'               |               '-.   \     /         
           \  / .-'      .-----------------------.      '-. \  /           
  <--------o----<=====>----/----<  .---.  >----\----<=====>----o-------->  
         |   |    /      /      .-'  |  '-.      \      \    |   |         
    <--------o----------<------<    (O)    >------>----------o-------->    
         |   |    \      \      '-.  |  .-'      /      /    |   |         
  <--------o----<=====>----\----<  '---'  >----/----<=====>----o-------->  
           /  \ '-.      '-----------------------'      .-' /  \           
         /     \   '-.               |               .-'   /     \         
      |       |   '-------------------------------------'   |       |      
      .--.             /\            |            /\             .--.      
    .'    |           /  \           |           /  \           |    '.    
   /      |          /    \          |          /    \          |      \   
  |       |         <      >         |         <      >         |       |  
   \      |          \    /          |          \    /          |      /   
   '.    /            \  /           |           \  /            \    .'   
      '--'      o-------\/-------o   +   o-------\/-------o      '--'      
           |       |         \       |       /         |       |           
           o-------o----------o------+------o----------o-------o           
           |       |          \      |      /          |       |           
              <|>     <|>          \    /          <|>     <|>             
              V       V             <O>             V       V              
                                     V                                     

Disputed Witch of the Ninth Court

From the vanished cities of Vharosyne comes a witch whom history cannot properly identify. Azhvielle appears across
contradictory records as Azhvielle of the Ninth Court or the Oakhaven Archivist among many more. 
Historians dispute whether these names describe one woman, several descendants, or a recurring legend. 

She served as a court witch, healer, archivist, tutor, and adviser to rulers whose kingdoms now survive only as 
footnotes. Countless centuries have left her cynical, practical, and thoroughly unimpressed by end divine kingdoms

Through ancient Vharosynian Causal Sorcery, Azhvielle commands fire, water, ice, air, earth, metal, lightning, smoke, 
and their combined forms. Every spell, however, may cause an unrelated anomaly elsewhere. A spark might trigger a 
distant landslide, while a volcanic eruption might merely give a stranger temporary musical talent. The scale of the 
spell offers no clue to the consequence.

Azhvielle therefore avoids magic whenever an ordinary solution exists, relying instead on experience, observation, and 
the Needle of Plain Iron.

The covenant bound within her soul also prevents her from invoking holy magic. Divine power recognizes something 
impossible inside her and attempts to tear it free.

She entered the dungeon after learning that a surviving Vharosynian record had been recovered below. She refuses to 
explain what it contains or why it bears her name.

Elemental Controller

Azhvielle offers immense elemental range and battlefield control, but every spell risks consequences beyond her sight.

Strengths: Elemental mastery, adaptability, battlefield control, ancient knowledge
Weaknesses: Unpredictable consequences, holy magic, mortal durability, reluctance to cast
Weapon: Needle of Plain Iron*
Discipline: Vharosynian Causal Sorcery

“Yes, I can solve this with magic. That does not make it sensible.”

3. Zhaivra Kelyth, the Uncontrolled Reagent

+-------------------------------------------------------------------------+
|                                  /\                                     |
|                  __             /  \                __                  |
|              __/  \___________/ /\ \___________/  \__                   |
|          __/      \         / /  \ \         /      \__                 |
|       _/    _/\_ \_______/ /____\ \_______/ _/\_    \_                  |
|     /_____/ /  \__________________________/  \ \_____\                  |
|                .---------------------------------------.                |
|              /                    /\                   \                |
|   __/\__    /                    /  \                   \      __/\__   |
|_/      \_  |                    / /\ \                     | _/      \_ |
|\_  /\  _/  |                   / /  \ \                    | \_  /\  _/ |
|  \/  \/    |                  /_/ /\ \_\                   |   \/  \/   |
|     ||     |                     /  \                      |     ||     |
|     ||     |     <\             / /\ \              />     |     ||     |
|   .[==].   |    <<\            / /  \ \            />>     |   .[==].   |
|   |:++:|   |   <<<\           <  /||\  >          />>>     |   |:++:|   |
|   |:++:|   |   << /            \/ || \/            \ >>    |   |:++:|   |
|    \__/    |     </               ||                 \>    |    \__/    |
|            |                      ||                       |            |
|            |                     /||\                      |            |
|            |                    /_||_\                     |            |
|             \                     ||                    /               |
|              \                    ||                   /                |
|                '------------------|+-------------------'                |
|                         \__________________|__________________/         |
|                .---------------------------------------.                |
|              /  THE FLAME THAT REFUSES ITS VESSEL     \                 |
|                '---------------------------------------'                |
+-------------------------------------------------------------------------+

Wandering Ashvein of Nhal Voryss

From the ever-burning arteries of Nhal Voryss comes an archer whose perfect shot moved an entire city. Zhaivra Kelyth 
once served the **Ashvein Survey**, a caste of alchemical rangers responsible for maintaining the volatile passages of 
the Hollow Colossus, the immense petrified organism within which her people built their civilization. Precise, 
analytical, and relentlessly prepared, she learned to read air currents through drifting mineral dust and identify 
combustible gases by the way they distorted distant light. She carries Sathren, a recurved bow grown from the bone-fiber 
of the Hollow Colossus and fitted with six internal reservoirs. A rotating thumb-ring coats each arrow with a selected 
compound moments before release, allowing Zhaivra to transform the battlefield one calculated reaction at a time. 

Zhaivra entered the dungeon after discovering traces of bone beneath a ruined surface monastery that appeared identical 
to the Hollow Colossus. She believes something buried within may explain what her homeland truly is and whether the 
First Turning can ever be undone.

Alchemical Marksman

Zhaivra is a deliberate ranged combatant who controls terrain through sequenced reactions, environmental manipulation, 
and carefully rationed ammunition. She rarely chooses the most destructive shot when a more efficient one will 
achieve the same result.

Strengths: Precision, battlefield control, armor disruption, environmental analysis
Weaknesses: Limited compounds, preparation requirements, changing weather, overreliance on calculation
Weapon: Sathren
Discipline: Ashvein Alchemy

“An arrow can strike exactly where you intended and still become the worst mistake of your life.”

4. Joruun Veyr, the Bloody Storm Monk

                                     ^                                     
                        ############/|\############                        
                  #######          /_|_\          #######                  
               ####     +++++++++_/ _^_ \_+++++++++     ####               
            ####   ++++++       .-~~~~~~-.        ++++++   ####            
         ####  +++++         .-'    __    '-.          +++++  ####         
       ###  ++++           .'    .-'  '-.    '.            ++++  ###       
      ##  +++             /    .'  .--.  '.    \              +++  ##      
    ### [=]              /    /   (  @ )   \    \               [=] ###    
   ##  ++                 \    \   '--'   /    /                  ++  ##   
   #  ++                    '.   '.__/\.'   .'                     ++  #   
  #  ++             /<<<<<<<<<<\    /  \     />>>>>>>>>>\           ++  #  
 ## ++         /\  /<<<<<<<<<<<<\  /    \    />>>>>>>>>>>>/\         ++ ## 
 #  +         /  \/<<<<<<<<<<<<<<\/      \   />>>>>>>>>>>/  \         +  # 
 #  +        / /   \<<<<<<<<<<<< /        \  \ >>>>>>>>>>>>/\ \       +  # 
 #  +       / /     \<<<<<<<<<< |          |  \ >>>>>>>>>>/  \ \      +  # 
 #  +        \ \                |   .--.   |               / /        +  # 
 ## ++        \ \                \  \__/  /               / /        ++ ## 
  #  ++        \/  __/\____/\____/\____/\____/\____/\__   \/        ++  #  
   #  ++         __/  \__/  \__/  \__/  \__/  \__/  \  \__         ++  #   
   ##  ++    _/~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\_     ++  ##   
    ### +++   /__\/\__/\__/\__/\__/\__/\__/\__/\__/\__/\/__\    +++ ###    
      ##  +++        vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv        +++  ##      
       ###  ++++       || ||||| |||||| ||||| || |||        ++++  ###       
         ####  +++++        || |   |||   | ||          +++++  ####         
            ####   ++++++           ||            ++++++   ####            
               ####     ++++++++++.----.+++++++++++     ####               
                  #######          |/\/|          #######                  
                        ###########|/\#|###########                        
                                  '----'                                   

Wandering Prophet of the Hollow Gale

From the storm-beaten Kharuun Shelf comes a monk of questionable holiness. Joruun Veyr wanders from village to village 
performing genuine miracles for donations, free drinks, and the attention of beautiful women. Beneath the flowing 
tan robes, dark spectacles, and rehearsed wisdom is a gifted Veyrathi martial artist with an equally impressive talent 
for gambling, deception, and getting thrown out of taverns. He carries **Sky-Needle**, an ash-wood shakujō fitted with 
copper collars and loose conductive rings. Through the **Law of the Single Current**, Joruun can generate wind, water, 
or lightning, but only one at a time. Existing rain, rivers, blood, and charged skies allow him to combine their effects 
through careful environmental control. Wind grants him speed and invisible pressure strikes. Water provides defense, 
reach, and crushing hydraulic force. Lightning delivers devastating bursts at severe physical cost.

He claims he entered the dungeon in pursuit of a sacred Veyrathi matter. His explanation changes depending on who asks, 
how much they are paying, and whether the nearest tavern is still open.

Elemental Skirmisher

Joruun is mobile, deceptive, and highly adaptable. He switches between three distinct combat forms and becomes 
increasingly dangerous when the environment supplies additional elements.

Strengths: Mobility, adaptability, battlefield control, burst damage
Weaknesses: Elemental transition windows, limited stamina, lightning recoil
Weapon: Sky-Needle
Discipline: Law of the Single Current

“The heavens provide the rain, the earth provides the grain, and the brewery provides salvation. Amen.”
        ''')

        choices = {
            "1": Brawler,
            "2": BlackMage,
            "3": RogueArcher,
            "4": Monk,
        }

        while True:
            character_choice = input(
                "Choose your character: 1 for Brawler, 2 for Black Mage, 3 for Rogue Archer, 4 for Monk: "
            ).strip()
            selected_character = choices.get(character_choice)

            if selected_character is None:
                print("That is not a valid character choice. Please try again.")
                continue

            player = selected_character()
            print(f"You have chosen the {player.name}!")
            return player
