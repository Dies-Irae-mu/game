"""
Utility functions and constants for handling character archetypes.
"""

# Dictionary of valid archetypes and their willpower regain conditions
ARCHETYPES = {
    'activist': {
        'name': 'Activist',
        'system': 'Regain Willpower when you successfully confront abuse, right wrongs, or reveal an actual conspiracy and, by doing so, bring it down.',
        'description': 'The world is broken. Help fix it. Speak truth to power, dig up secrets, call people out on their shit, and reveal your plans for a better world to anyone who will listen. While apathetic cowards sit back and tune out, you step up and do whatever needs doing. Sure, folks might consider you a pain in the ass, but at least you\'re making a difference! Action is your greatest strength. You\'re not one to sit things out. There\'s no time to waste on mindless self-indulgence and no room to stay scared of what might happen. The wolf\'s already halfway through the door, and you refuse to let that bastard win. Even so, your constant Outrage wears thin. There\'s never room to sit back and enjoy life. As far as you\'re concerned, complacency is a sin. Your fury\'s justified, of course, but it gets old all the same. Before you can truly Ascend, you\'ve got to balance righteous pyrotechnics with calm acceptance. Life never has been – and never will be – perfect. Finding a place of serenity within your storm is an essential part of your transcendence.'
    },
    'alpha': {
        'name': 'Alpha',
        'system': 'Regain a point of Willpower when you are able to force a rival to submit to your authority.',
        'description': 'The Alpha wants to be in charge. He demands respect and obedience, even submission. He may convince himself that he wants power for the greater good, or he may simply believe it is his natural birthright. Many leaders, from the streets to the boardroom, exemplify the Alpha Archetype. This Archetype is common among werewolves, from those who consider themselves the best choice for pack leader to those who attempt to rise to command septs or even tribes.'
    },
    'anarchist': {
        'name': 'Anarchist',
        'system': 'Regain a point of Willpower whenever you reject unnecessary rules, laws, or social norms and achieve success because of it.',
        'description': 'The Anarchist believes that the world would be a better place if every individual took responsibility for her own destiny and stayed out of everyone else\'s business. She lives her own rules and refuses to bend to higher powers or society.'
    },
    'architect': {
        'name': 'Architect',
        'system': 'Regain a point of Willpower whenever you establish something of importance or lasting value.',
        'description': 'The Architect has a sense of purpose even greater than herself. She is truly happy only when creating something of lasting value for others. People will always need things, and the Architect strives to provide at least one necessity. Inventors, pioneers, town founders, entrepreneurs, and the like are all Architect Archetypes. A Kindred Architect might seek to create new laws that affect her fellow undead, or she might aim to establish a new Anarch domain.'
    },
    'autocrat': {
        'name': 'Autocrat',
        'system': 'Regain a point of Willpower when you achieve control over a group or organization involving other individuals.',
        'description': 'The Autocrat wants to be in charge. He seeks prominence for its own sake, not because he has an operation\'s best interests at heart or because he has the best ideas (though he may certainly think so). He may genuinely believe others are incompetent, but ultimately he craves power and control. Dictators, gang leaders, bullies, corporate raiders, and their ilk are Autocrat Archetypes. A Kindred Autocrat may crave a title, or he may wish to be recognized as the leader of a coterie.'
    },
    'avant-garde': {
        'name': 'Avant-Garde',
        'system': 'The Avant-Garde regains Willpower every time she experiences something new and controversial.',
        'description': 'The Avant-Garde is a pioneer of invention. Unafraid to experiment and innovate, the Avant-Garde produces and supports whatever she can that is exciting and new. To her, being dead is no barrier to discovery and growth. The Avant-Garde is unafraid of controversy or what the neighbors might think. She despises bland repetition, and always seeks new experiences.'
    },
    'barterer': {
        'name': 'Barterer',
        'system': 'Regain a point of Willpower whenever you gain a significant commodity at a good price.',
        'description': 'The art of the deal is the art of life. The Barterer Archetype exults in getting something potent for a low price, and takes personal pride in being savvy enough to avoid bad deals and capitalize on good ones. For werewolves, this Archetype is most common among Theurges and others who broker deals with the spirit world, where the dance of chiminage and patronage is so significant.'
    },
    'beta': {
        'name': 'Beta',
        'system': 'Act as a supporter for your group\'s superior.',
        'description': 'Regain Willpower whenever your counsel proves beneficial for the group. Lose Willpower when the leader is proven inefficient.'
    },
    'benefactor': {
        'name': 'Benefactor',
        'system': 'Regain Willpower when you provide help that someone else desperately needs.',
        'description': 'It\'s a cruel world, but you make things easier. Generous sometimes to a fault, you supply whatever you can provide: money, advice, protection, maybe just a shoulder when someone really needs to cry. You can\'t just turn blind eyes to suffering and need. It\'s your moral duty to do whatever you can do to make things right. When things get tough, you call upon your inner White Knight and charge in, bringing gifts, guidance, and occasional force when nothing else will do. Altruism is all too rare, especially in the World of Darkness. Helping people is your pleasure. Magick, as far as you\'re concerned, is a tool for helping folks less fortunate than yourself. To do less is an abuse of the powers you possess. On the flipside, though, you often feel Obligation even when you\'re not actually needed. This, in turn, can become resentment – both on your part and on the parts of people who now feel, rightly or wrongly, that they owe you. Sometimes, you just need to back off, chill out, and let people do things for themselves. Martyrdom isn\'t always the best Path toward Ascension.'
    },
    'big-bad-wolf': {
        'name': 'Big Bad Wolf',
        'system': 'Regain a point of Willpower whenever someone recoils from you in horror or otherwise reacts in fear.',
        'description': 'The Big Bad Wolf craves fear. Not her own: the fear of others. She may delight in stalking humans, intimidating other Garou, or using fear as a weapon against the forces of the Wyrm. This Archetype is popular among Ragabash as well as Ahroun, and finds a home in most tribes, from the slasher urban legends of the Bone Gnawers to the righteous avengers of the Red Talons.'
    },
    'bon-vivant': {
        'name': 'Bon Vivant',
        'system': 'Regain a point of Willpower whenever you truly enjoy yourself and can fully express your exultation.',
        'description': 'The Bon Vivant knows that life — and unlife — is shallow and meaningless. As such, the Bon Vivant decides to enjoy her time on Earth. The Bon Vivant is not necessarily irresponsible. Rather, she is simply predisposed to having a good time along the way. Most Bon Vivants have low Self-Control ratings, as they are so given to excess. Hedonists, sybarites, and dilettantes are all examples of the Bon Vivant Archetype. A Kindred Bon Vivant may sire a brood of fawning childer, or he may spend his time gorging on the blood of drug abusers for the contact high.'
    },
    'bravo': {
        'name': 'Bravo',
        'system': 'The Bravo regains Willpower every time she beats someone down, verbally or physically.',
        'description': 'The Bravo is not incapable of pity or kindness; he just prefers to do things his way. Robbers, bigots, and thugs are all Bravo Archetypes. Werewolf Bravos are prone to bare their teeth at a moment\'s notice, and are frequently dismissive or even abusive of ordinary humans.'
    },
    'bureaucrat': {
        'name': 'Bureaucrat',
        'system': 'The Bureaucrat regains Willpower every time he uses the established rules to deal with a situation.',
        'description': 'The Bureaucrat works the system from within. He recognizes the need for regulations, forms, and ordered queuing. Patience and organization are typical strengths of the Bureaucrat, who follows every procedure. The Bureaucrat understands rules and red tape can stifle initiative, but only by working steadily via the correct channels can security be maintained.'
    },
    'capitalist': {
        'name': 'Capitalist',
        'system': 'Regain a point of Willpower whenever you make a successful \'sale\' of any \'commodity\'.',
        'description': 'You are the ultimate mercenary, realizing that there is always a market to be developed — anything can be a commodity. You have a keen understanding of how to manipulate both kine and Cainites into thinking that they need specific goods or services. Appearance and influence are everything when it comes to the big sale, though you\'ll use anything to your advantage. Salesmen, soldiers of fortune, and bootlickers all adhere to the Capitalist Archetype.'
    },
    'caregiver': {
        'name': 'Caregiver',
        'system': 'Regain a point of Willpower whenever you successfully protect or nurture someone else.',
        'description': 'Everyone needs a shoulder to cry on. A Caregiver takes her comfort in consoling others, and people often come to her with their problems. Vampires with Caregiver Archetypes often attempt, as best they can, to protect the mortals on whom they feed. Nurses, doctors, and psychiatrists are examples of potential Caregivers. Caregiver Kindred are often the type who — tragically — Embrace mortal loves they\'ve left behind in hopes of softening their loss, or even those who create situations of grief in order to ease it and thus validate themselves.'
    },
    'celebrant': {
        'name': 'Celebrant',
        'system': 'Regain a point of Willpower whenever you pursue your cause or convert another character to the same passion.',
        'description': 'The Celebrant has a cause, and she follows it not from grim necessity but from exuberant enthusiasm. Her passion may be battle, art, the game of politics, or any other endeavor that grants her sufficient strength to carry on. The enthusiasm of Garou Celebrants is all the more valuable in the face of the war against the Wyrm; the Archetype is popular among Galliards, and Galliards of other Archetypes love to stir up a Celebrant as well.'
    },
    'chameleon': {
        'name': 'Chameleon',
        'system': 'Regain a point of Willpower whenever you fool someone into thinking you\'re someone else.',
        'description': 'Independent and self-reliant, you carefully study the behavior and mannerisms of everyone you come in contact with so you can pass yourself off as someone else later. You spend so much time altering your mannerisms and appearance that your own sire may not even recognize you. Spies, con artists, drag queens, and impostors best represent the Chameleon.'
    },
    'child': {
        'name': 'Child',
        'system': 'Regain a point of Willpower whenever you manage to convince someone to help you with no gain to herself, or to nurture you.',
        'description': 'The Child is still immature in personality and temperament. He wants what he wants now, and often prefers someone to give it to him. Although he can typically care for himself, he would rather have someone cater to his capricious desires. Some Child Archetypes are actually innocent rather than immature, ignorant of the cold ways of the real world. Actual children, spoiled individuals, and some drug abusers are Child Archetypes. Kindred with the Child Archetype might have not yet fully reached an understanding of the world and have some characteristic such as cruelty, entitlement, sympathy, or hunger that is out of balancewith their other personality aspects, as they haven\'t yet reached the \'rounded\' state of adulthood. Note that a Child Archetype need not be a physical, literal child at the time of Embrace. Some people simply never grow up.'
    },
    'competitor': {
        'name': 'Competitor',
        'system': 'The Competitor regains Willpower every time he succeeds at a competitive challenge.',
        'description': 'The Competitor takes great excitement in the pursuit of victory. To the Competitor, every task is a new challenge to meet and a new contest to win. Indeed, the Competitor sees all interactions as some sort of opportunity for her to be the best — the best leader, the most productive, the most valuable, or whatever. Corporate raiders, professional athletes, and impassioned researchers are all examples of Competitor Archetypes. Kindred Competitors have any number of resources and accomplishments over which to assert themselves, from mortal herds and creature comforts to titles and prestige in Kindred society.'
    },
    'conformist': {
        'name': 'Conformist',
        'system': 'Regain a point of Willpower whenever the group or your supported leader achieves a goal due to your support.',
        'description': 'The Conformist prefers not to take charge, instead seeking security in letting others give orders that she can follow. The Conformist may be the \'beta\' or middle manager to the most dynamic personality in a social setting, or she may prefer to follow along with her pack, right or wrong. This isn\'t necessarily a weak Archetype; it can simply represent a desire to play a support role. Examples of Garou Conformists include tribal loyalists and packmates who enforce the pack leader\'s role.'
    },
    'conniver': {
        'name': 'Conniver',
        'system': 'The Conniver regains Willpower every time she convinces someone else to do something that benefits only her.',
        'description': 'Why work for something when you can trick somebody else into getting it for you? The Conniver always tries to find the easy way, the fast track to success and wealth. Some people call him a thief, a swindler, or less pleasant terms, but he knows that everybody in the world would do unto him if they could. He just does it first, and better. Criminals, con artists, salespeople, urchins, and entrepreneurs might be Connivers. Some would argue that all Kindred are Connivers in some sense, but those that have the Conniver archetype may be abusive to their childer and ghouls, or they may be more persuasive in gaining support for their machinations.'
    },
    'contrary': {
        'name': 'Contrary',
        'system': 'Regain Willpower whenever your inversion of expectations leads folks to realize how false those expectations had been.',
        'description': 'Inversion is an essential part of real life. For every rule, there must be exceptions. You live to turn things inside out, undercutting assumptions by showing their weak foundations. You\'re the Devil\'s Advocate, pointing out flaws by embodying the opposite of what folks expect. A successful Contrary displays Insight; your inversions succeed because they point to a deeper truth. If you\'re serious about this path (that is, if you\'re an actual Contrary, not simply an asshole), then you\'re a jester with a clue. That ability to see beyond appearances is extremely useful in the Awakened realm. And yet, your perpetual Subversion can be annoying, intrusive, and outright destructive. Certain assumptions really are true, and inverting them doesn\'t provide any particular wisdom. If you seriously want to reach beyond appearances, you have to realize that your own contrariness can be its own limitation. True wisdom comes through a balance between rejection and acceptance.'
    },
    'creep-show': {
        'name': 'Creep Show',
        'system': 'Regain a point of Willpower whenever someone recoils from you in horror or otherwise reacts in fear.',
        'description': 'You strive to shock and disgust those around you with gratuitous acts and ostentatiously \'evil\' mannerisms. You realize, of course, that it\'s all show and merely a way to intimidate and control others. Outsiders, on the other hand, think you are the Devil incarnate, and you revel in this image. Shock-rockers, rebellious teenagers, circus freaks, and the attention-starved exemplify the Creep Show Archetype.'
    },
    'critic': {
        'name': 'Critic',
        'system': 'Regain a point of Willpower whenever you find a flaw in a design or plan and then improve upon it.',
        'description': 'The Critic observes the world around her with a jaundiced eye, seeking out flaws and deficiencies. She experiences a special satisfaction in exploiting these weaknesses publically so that eventually the design will improve. Some critics feel it is their duty to push the world to be better.'
    },
    'crusader': {
        'name': 'Crusader',
        'system': 'Regain Willpower when you accomplish some great deed in the name of your higher goal.',
        'description': 'People need a hero, and you\'re there to fill that role. Driven by a higher purpose – religious conviction, moral ethics, a philosophical ideal – you strive for a better world. The sword you wield might be more symbolic than literal: a scientist or teacher can be a Crusader too. The struggle, though, is what defines you. A better future must be built upon the foundations of our flawed world, and your duty compels you to demolish the obstacles so that reconstruction can begin. Your admirable Zeal propels you through every challenge you face. Lesser souls might falter, but you will not. Fanaticism, though, is the mark of a Crusader. Your convictions leave little room for compromise. When everything looks like a nail, it\'s hard to stop hammering. Until and unless you learn to temper your enthusiasm and question your own assumptions, you\'re just chasing shadows of your own extremism.'
    },
    'cub': {
        'name': 'Cub',
        'system': 'Regain a point of Willpower whenever you manage to convince someone to nurture you, or to help you with no gain to herself.',
        'description': 'The Cub isn\'t ready to take responsibility. He\'s still immature, perhaps innocent, and tries to depend on others for protection and nurturing. Werewolves rarely keep the Cub Archetype for long — it tends to be stripped away by the vicious realities of their constant struggle. Still, some find themselves defaulting back to earlier behavior as a plea for help.'
    },
    'curmudgeon': {
        'name': 'Curmudgeon',
        'system': 'Regain a point of Willpower whenever someone does something specific and negative, just like you said they would.',
        'description': 'A Curmudgeon is bitter and cynical, finding flaws in everything and seeing little humor in life or unlife. He is often fatalistic or pessimistic, and has very little esteem for others. To the Curmudgeon, the glass is never more than half-full, though it may be damn near empty when other people are involved. Many Internet junkies, pop-culture fans, and Generation Xers are Curmudgeons. Kindred Curmudgeons see elder oppression or spoiled neonates running amok behind every development in undead society, and may or may not rise beyond acerbic grumbling to change any problems they perceive.'
    },
    'dabbler': {
        'name': 'Dabbler',
        'system': 'Regain Willpower whenever you find a new enthusiasm and drop your old one completely.',
        'description': 'The Dabbler is interested in everything but focuses on nothing. He flits from idea to idea, passion to passion, and project to project without actually finishing anything. Others may get swept up in the Dabbler\'s enthusiasm, and be left high and dry when he moves on to something else without warning. Most Dabblers have high Intelligence, Charisma, and Manipulation ratings, but not much in the way of Wits or Stamina. Toreador are often Dabblers, particularly those afflicted with the derisive sobriquet \'Poseurs.\''
    },
    'deviant': {
        'name': 'Deviant',
        'system': 'Regain a point of Willpower any time you are able to flout social mores without retribution.',
        'description': 'The Deviant is a freak, ostracized from society by unique tastes or beliefs that place her outside the mainstream. Deviants are not indolent rebels or shiftless \'unrecognized geniuses\'; rather, they are independent thinkers who don\'t quite fit in the status quo. Deviant Archetypes often feel that the world stands against them, and as such reject traditional morality. Some have bizarre tastes, preferences, and ideologies. Extremists, eccentric celebrities, and straight-up weirdoes are Deviant Archetypes. Kindred deviants may observe heretical or outlawed habits like diablerie or deference to elders, and they may well go Anarch or Autarkis instead of having to constantly defend their subversion of Traditions or Sect customs.'
    },
    'director': {
        'name': 'Director',
        'system': 'Regain a point of Willpower when you influence or aid a group or influential individual in the completion of a difficult task.',
        'description': 'To the Director, nothing is worse than chaos and disorder. The Director seeks to be in charge, adopting a \'my way or the highway\' attitude on matters of decision-making. The Director is more concerned with bringing order out of strife, however, and need not be truly \'in control\' of a group to guide it. Coaches, teachers, and many political figures exemplify the Director Archetype. Kindred Directors may be simple advocates of established codes, or they may prove instrumental in tearing down corrupt existing orders to make way for new leaders or factional movements.'
    },
    'enigma': {
        'name': 'Enigma',
        'system': 'The Enigma regains Willpower every time someone is confused by his actions, which later turn out to be worthwhile.',
        'description': 'Your actions are bizarre, puzzling, and inexplicable to everyone except yourself. Your strangeness may be a residual effect from your Embrace, or the most effective way for you to carry out your work. To the rest of the world, however, your erratic actions suggest that you\'re eccentric if not completely crazy. Conspiracy theorists, deep-cover agents, and Jyhad fanatics all live up to the Enigma Archetype.'
    },
    'explorer': {
        'name': 'Explorer',
        'system': 'The Explorer regains Willpower every time she discovers something previously unknown.',
        'description': 'The Explorer is possessed by wanderlust and the need for adventure. She views the Underworld as one rich prospect offering endless possibilities for discovery, and this in turn drives her constantly to seek out its limits. From the unknown spaces on the map to the boundaries of what can be done with Arcanoi, she always wants to find out what\'s around the next corner. What\'s done is done, and what matters is what comes next. Part of her worries there will one day be no new treasures to find, but those anxieties are brushed aside. There will always be new horizons to discover.'
    },
    'eye-of-the-storm': {
        'name': 'Eye of the Storm',
        'system': 'Regain a point of Willpower whenever a ruckus, riot, or less violent but equally chaotic phenomenon occurs around you.',
        'description': 'Despite your calm appearance, chaos and havoc seems to follow you. From burning cities to emotional upheaval, death and destruction circle you like albatrosses. For you, unlife is a never-ending trial with uncertainty around every corner. Gang leaders, political figures, and other influential individuals exemplify the Eye of the Storm Archetype.'
    },
    'fanatic': {
        'name': 'Fanatic',
        'system': 'Regain a point of Willpower whenever you accomplish some task that directly relates to your cause.',
        'description': 'The Fanatic\'s purpose consumes his existence. Nothing is as important as the higher goal, and frequently the end justifies all manner of means. Players who choose Fanatic Archetypes must select a cause for their characters to further. The Garou Nation has a long history of fanaticism, usually focusing on some particular aspect of the war against the Wyrm, such as bringing down the Black Spiral Dancers or unifying the tribes under one leader.'
    },
    'fatalist': {
        'name': 'Fatalist',
        'system': 'Regain a point of Willpower whenever someone does something specific and negative, just like you said they would.',
        'description': 'The Fatalist is relentlessly cynical and pessimistic, always concerned with the cloud rather than the silver lining. He may have once been idealistic, but he has lost those ideals after bitter experience. Many Garou are Fatalists, driven by an unhealthy focus on the inevitable decline of their kind and the looming doom of Apocalypse.'
    },
    'follower': {
        'name': 'Follower',
        'system': 'The Follower regains Willpower every time he demonstrates absolute loyalty under trying circumstances.',
        'description': 'The Follower recognizes an excellent leader and flourishes by supporting her. He offers advice from behind or beside the throne, his loyalty never in doubt. Freed from the responsibilities of command, he can function to best effect by putting his efforts at someone else\'s disposal. Always looking for a stronger personality to support, the Follower can be a loyal, capable ally, allowing a strong leader to be even more effective.'
    },
    'gallant': {
        'name': 'Gallant',
        'system': 'Regain a Willpower point whenever you successfully impress another person.',
        'description': 'The Gallant wants to be the center of attention. She basks in the attentive praise of others, though she may be perfectly happy drawing their scorn as well. As long as she\'s on center stage, it\'s all good. Many Galliards and Fianna are drawn to this archetype.'
    },
    'gambler': {
        'name': 'Gambler',
        'system': 'The Gambler regains Willpower every time she comes up against unwinnable odds and somehow emerges the victor.',
        'description': 'The Gambler risks it all just to feel a tiny spark of life again, upping the stakes in order to get the thrill of beating the odds. She\'s sure she can win when the chips are down, and that any setback\'s a temporary one. The thrill of existence is the risk of losing it all, and the rush when a bet pays off. She trusts her luck and skill equally, and will lay them on the line against anything Oblivion can come up with.'
    },
    'guru': {
        'name': 'Guru',
        'system': 'Regain a point of Willpower whenever someone seeks out your help in spiritual matters and your guidance moves that individual to an enlightened action.',
        'description': 'The Guru is a spiritual counselor, one who seeks wisdom for the purpose of passing it on. She values metaphysical insight highly, searching for her own enlightenment even as she attempts to bring others further along their own paths. The Guru\'s path may be peaceful, as with a Child of Gaia or Stargazer, but it may also be a blood-soaked spiritual road leading to Valhalla.'
    },
    'hacker': {
        'name': 'Hacker',
        'system': 'Regain Willpower when you detect a flaw in some important structure, system, or device, or else when you puzzle out a way to improve something that was supposedly designed well to begin with.',
        'description': 'Every system is a locked vault, and you\'ve got the keys. If you don\'t have ones that work, you\'ll make new ones – that\'s half the fun of life, after all! Puzzles excite you; limits just piss you off. Especially given the sheer amount of abuse that\'s built into any system, the world needs folks like you to tear down impediments and set reality free. Imagination is your greatest strength. You see things not as they are, but as they could be once you get done with them! Driven to dismantle existing systems and then put them together in interesting new shapes, you tend to pepper your compulsions with sincerely-held philosophy. You\'re not a vandal, for crying out loud – you\'re a visionary who refuses to accept shit sandwiches handed out as lunch. Sometimes, though, you go too far. Perversity leads you to tear apart things that weren\'t broken… things that may, in fact, have been better left alone. Although it might seem philosophically valid to tear down the wards on a wizard\'s lab, those wards might have been laid that way for reasons you didn\'t understand until it was a little too late.'
    },
    'idealist': {
        'name': 'Idealist',
        'system': 'Regain Willpower when your beliefs are tested to the breaking point yet do not fail.',
        'description': 'Cowards accept what is. You know how much better things will be once the flaws in the system have been purged. Guided by a great ideal – spiritual devotion, political philosophy, scientific theory, compassionate humanity – you refuse to remain shackled by defeatism. Your Ideal is correct. You know this to be true. Now is the time to bring it about. Once you do, everyone else will see just how wrong they\'ve been… and how right you are. Conviction is your life\'s blood. Whether you\'re a scientist chasing inspiration, a theorist assured that this theory cannot fail, a religious devotee, or some other sort of Idealist, you possess near-unshakable faith in your ideal – the kind of faith that shapes reality. Like most fanatics, though, you\'re Dogmatic to a fault. Blind to any potential flaws, you\'ll fight – sometimes literally – to assure the truth of your beliefs. All mages are idealists to a point; in your case, though, this devotion seems stifling. When (not if, when) reality falls short of your ideals, you might wind up depressed, violent, or – as with many Marauders – insane.'
    },
    'innovator': {
        'name': 'Innovator',
        'system': 'Regain Willpower when your inspiration leads to a helpful new breakthrough.',
        'description': 'There\'s always a better way. You spend your life looking for methods and inventions that improve on what has gone before. Sure, past achievements are wonderful enough… but if you just add this, shift that, approach the issue from this other angle instead, then you\'ll make a good thing that much better or fix an obvious flaw in a promising design. Creativity is your strong point. No practice, tool, or traditional method is too good for improvement, especially not at this crucial point in human evolution. Let other people follow the established paths – you\'re busy drawing up the next road toward a goal most folks don\'t even know exists. Your Restless Unorthodoxy, though, can get you in trouble. Especially if you belong to a sect or faction based on established results and protocols (the Technocracy, the Hermetic Order, the Akashayana, and so on), your innovations might be someone else\'s heresy. Many mages have been burnt at stakes both literal and symbolic for doing the things you do, and a missed step could make (an) ash of you.'
    },
    'jester': {
        'name': 'Jester',
        'system': 'The Jester regains Willpower every time he makes a dire situation lighter through comedy.',
        'description': 'The Jester knows the strongest weapon against Oblivion is humor. To laugh in the face of Oblivion is to deny it any power. Though the Jester\'s timing may not always be the best — the compulsion to make a joke out of everything can wreak havoc with trying to commune with one\'s Passions — their unflagging goof humor can be more infuriating to a ravening Spectre than a fully armed Centurion.'
    },
    'judge': {
        'name': 'Judge',
        'system': 'Regain a point of Willpower whenever you correctly solve a problem or when one of your arguments unites dissenting parties.',
        'description': 'The Judge perpetually seeks to improve the system. A Judge takes pleasure in her rational nature and ability to draw the right conclusion when presented with facts. The Judge respects justice, as it is the most efficient model for resolving issues. Judges, while they pursue the \'streamlining\' of problems, are rarely visionary, as they prefer proven models to insight. Engineers, lawyers, and doctors are often Judge Archetypes. Kindred Judges might gravitate toward enforcement roles in local society, or they might be a voice of reason in an otherwise radical coterie.'
    },
    'kid': {
        'name': 'Kid',
        'system': 'Regain Willpower when you bring out the nurturing side of someone who doesn\'t normally care much for other people.',
        'description': 'Either young in years or young at heart, you give the impression of needing to be taken care of by older, wiser folks. That impression may be deceiving, but you\'re glad to use it to your best advantage. You could be an actual child – somewhere between post-toddlerhood and late adolescence – or chronologically an adult with a childlike personality. Whatever your actual age might be, your concerns are simple, capricious, and typically self-involved. There\'s a kind of Innocence to you, and it provides the source of your strength. People want to protect that sense of wonder and hope and tend to offer you a compassion they might not feel toward other folks. The extreme of innocence, though, is Immaturity. Trusting too easily, acting too rashly, jumping into things without considering their potential consequences… you\'re guilty of all these things and more. You can slide from charming child to spoiled brat in the space between two heartbeats, and the traits that inspire people to take care of you can become infuriating as well. If and when you want to reach a higher state, you\'ll have to put certain childish things aside.'
    },
    'leader': {
        'name': 'Leader',
        'system': 'The Leader regains Willpower every time she assumes control of a situation.',
        'description': 'The Leader is a Various who knows she\'s the only one capable of doing what must be done. Incapable of just sitting by while things are done poorly, she\'ll step up and take charge when the situation demands it. A natural at giving orders, the Leader cares less about others\' feelings than she does about making sure things get done right.'
    },
    'loner': {
        'name': 'Loner',
        'system': 'Regain Willpower when you achieve some meaningful goal without help from anyone else, especially if your accomplishment benefits other people too.',
        'description': 'Fuck the world. Everything you need in life you\'ve got inside yourself. Even in the middle of a crowd, you\'re alone… or at least, you feel that way. People don\'t understand you, and you don\'t care enough to try to understand them. It\'s not that you\'re a sociopath or anything (although you just might be one) so much as it\'s that you just don\'t connect with that whole social animal thing at all. Self-Reliance is your blessing. You\'re so used to doing everything yourself that you rarely depend on another person\'s aid. Ascension, so far as you understand it, is a solitary task, so why bother asking for assistance with that goal? Trouble is, your Disconnection cuts you off from empathy and the wealth of human experience. Until and unless you let down the barriers and connect with other living things, you\'re doomed to a lonesome and limited existence.'
    },
    'machine': {
        'name': 'Machine',
        'system': 'Regain Willpower by performing spectacular acts of heartlessness and ruin.',
        'description': 'Heaven lacks glory without the threat of Hell. It\'s your noble chore, then, to be the Agent of Infamy. An obvious choice for Nephandic mages (though not, by a long shot, exclusive to their kind), this Archetype embodies unapologetic villainy. As Voltaire (the singer, not the philosopher) put it, \'It\'s so easy when you\'re evil\'… easy, fun, and satisfying! You Reveal Dark Truths that many people are afraid to face. When you show up, Pollyanna runs screaming for the hills. Your existence undercuts the comfortable lies of polite society. Anyone can play a hero, but a memorable villain is worth his weight in blood. The problem, of course, is that you\'re Depraved. There might be a heroic heel-turn in your future, but that\'s unlikely. Chances are, you\'re headed for the Cauls; if you haven\'t Fallen with the Nephandi already, you probably will soon enough.'
    },
    'mad-scientist': {
        'name': 'Mad Scientist',
        'system': 'Regain Willpower when you successfully bend the rules of your technomancer sect while still applying something that seems oddly like science (see the sidebar SCIENCE!!!, p.290) and manage to avoid invoking Paradox.',
        'description': 'Science is not a field for cowards and fools. You understand that technology expands only when brave souls such as yourself dare the unthinkable and push past the established norms of hidebound preconceptions. Yes, those cowards and fools do falter when they behold the scope of your temerity. Let them! Just as Vesalius defied taboos when he performed dissections or Galileo challenged the Church with his discoveries, so too must other visionaries stand firm and expand the reach of science… visionaries including, of course, yourself. You do, in fact, have Vision. It\'s probably your greatest strength. Pursing that vision despite all obstacles, you move the boundaries of reality through sheer determination. Problem is, you are Batshit Insane. There are reasons that other people have not dared the things you do or, if they have, that they\'re reviled names in the Halls of Infamy. The Technocracy, Virtual Adepts, and especially the Etherites might depend upon minds like yours, but they also keep a wary eye out for the times when you\'ll go too far – because you will.'
    },
    'martyr': {
        'name': 'Martyr',
        'system': 'Regain Willpower whenever you manage to make a noticeably positive difference in someone else\'s situation by giving deeply of yourself.',
        'description': 'It\'s your glory to sacrifice yourself for the greater good. Precisely what this greater good looks like is up to you. It\'s probably based on a religious creed – possibly, but not necessarily, Islam or Christianity. Then again, you may want to give your all for a secular cause you believe in, maybe a political ideology, a philosophical ideal, or simply the opportunity to be heroic in ways only you can perform. This sacrifice doesn\'t have to be fatal, though it\'ll probably wind up being terminal eventually. Until then, you tend to put yourself in a position to suffer so that someone else might thrive. Sacrifice is a mighty thing in magick. The willingness to surrender one\'s self to a greater end is one of the most obvious (and famous) Paths toward Ascension. That said, such Self-Deprecation can have unfortunate consequences far beyond simple hazards to your health. Martyrs tend to get on people\'s nerves, wind up being taken advantage of, and deal with abuse that has nothing to do with the greater good. Worse, perhaps, people like you often resent the beneficiaries of their sacrifice, many of whom might not want you to sacrifice yourself at all.'
    },
    'masochist': {
        'name': 'Masochist',
        'system': 'Regain one point of Willpower when your own suffering leads to some tangible gain for you.',
        'description': 'The Masochist exists to test his limits, to see how much pain he can tolerate before he collapses. He gains satisfaction in humiliation, suffering, denial, and even physical pain. The Masochist defines who he is by his capacity to feel discomfort — he rises each night only to greet a new pain. Certain extreme athletes, urban tribalists, and the clinically depressed exemplify the Masochist Archetype. Kindred Masochists might be overtly self-mortifying horrors who play to their Beast\'s self-destructive whims, or they may be ambitious taskmasters, as with a coterie leader who refuses to accept failure and pushes his own limits in his exacting schemes.'
    },
    'mediator': {
        'name': 'Mediator',
        'system': 'The Mediator regains Willpower every time she convinces others to compromise on a high-stakes disagreement.',
        'description': 'The Mediator knows how important compromise can be, and seeks to avoid conflict. She pursues give and take no matter who the parties are, knowing that unless both sides benefit, clashes can escalate to cataclysmic levels. While there\'s always the fear her involvement might makes things worse, she knows someone has to be the impassioned voice of reason when the stakes are so high.'
    },
    'mentor': {
        'name': 'Mentor',
        'system': "You've got knowledge and experience that can benefit other people, so you share it as freely as you can. This might involve having a single pupil, apprentice or protege, or it could involve several people learning what you have to teach. More than simply a teacher, though, you make a personal investment in your student's progress. An instructor can leave the classroom at the end of the day, but a Mentor's role might last for life. Dedication is your source of strength. It's important to you that other people share in what you have to offer. Because you care about the results, and probably about the students too, you'll put yourself out there in surprising ways. (See the Background: Mentor for certain effects of a mentor /student bond.) On the other hand, you can be Pedantic. Lecturing becomes  habit, with every circumstance providing an opportunity for more lessons. Occasionally, even the most accomplished teacher must step out from behind the podium. Your potential for Ascension depends in part upon humanity, and that's a hard thing to hang on to when you're always in the Professor role. (There's also a great potential to develop problematic and possibly unethical bonds with your protege, but that's an entirely different sort of lesson to learn.) ",
        'description': 'Regain Willpower when your guidance helps your pupil(s) accomplish something that had been beyond their reach before.'
    },
    'monster': {
        'name': 'Monster',
        'system': 'Regain Willpower by performing spectacular acts of heartlessness and ruin.',
        'description': 'Heaven lacks glory without the threat of Hell. It\'s your noble chore, then, to be the Agent of Infamy. An obvious choice for Nephandic mages (though not, by a long shot, exclusive to their kind), this Archetype embodies unapologetic villainy. As Voltaire (the singer, not the philosopher) put it, \'It\'s so easy when you\'re evil\'… easy, fun, and satisfying! You Reveal Dark Truths that many people are afraid to face. When you show up, Pollyanna runs screaming for the hills. Your existence undercuts the comfortable lies of polite society. Anyone can play a hero, but a memorable villain is worth his weight in blood. The problem, of course, is that you\'re Depraved. There might be a heroic heel-turn in your future, but that\'s unlikely. Chances are, you\'re headed for the Cauls; if you haven\'t Fallen with the Nephandi already, you probably will soon enough.'
    },
    'nihilist': {
        'name': 'Nihilist',
        'system': 'Regain a point of Willpower whenever you engage in self-destructive behavior.',
        'description': 'The Nihilist believes that life is without objective purpose or intrinsic value. Since nothing matters, the Nihilist feels morally free to indulge in whatever destructive passions she might crave at the moment.'
    },
    'optimist': {
        'name': 'Optimist',
        'system': 'The Optimist regains Willpower every time he discovers and champions the bright side to an otherwise grim event.',
        'description': 'The Optimist knows things could be a lot worse, but with a little effort they\'re going to get better. He sees the positive side of having survived death, and presses the realization on everyone. The Optimist vigilantly aims to keep spirits high, helping to show others that even in the Underworld, it\'s not just doom and gloom. This, in his opinion, is the best way to fight Oblivion and its sidekick, despair.'
    },
    'pedagogue': {
        'name': 'Pedagogue',
        'system': 'Regain one point of Willpower whenever you see or learn of someone who has benefited from the wisdom you shared with them.',
        'description': 'The Pedagogue knows it all, and desperately wants to inform others. Whether through a sense of purpose or a genuine desire to help others, the Pedagogue makes sure his message is heard — at length, if necessary. Pedagogue Archetypes may range from well-meaning mentors to verbose blowhards who love to hear themselves talk. Instructors, the overeducated, and \'veterans of their field\' are all examples of Pedagogue Archetypes. Kindred Pedagogues include watchdogs of the Traditions, ideological Anarchs, and perhaps even that rare soul seeking Golconda who wants company on the journey.'
    },
    'penitent': {
        'name': 'Penitent',
        'system': 'Regain Willpower whenever you are able to atone for past sins or help others avoid similar mistakes.',
        'description': 'The Penitent exists in a state of perpetual remorse. Whether her sin was real or imagined, she knows she has done wrong and must make up for it. Some take on great crusades to absolve themselves, while others choose a more personal path to redemption. The Penitent may be truly evil and searching for redemption, or may simply be wracked by guilt over perceived inadequacies.'
    },
    'perfectionist': {
        'name': 'Perfectionist',
        'system': 'Regain Willpower whenever you achieve something that meets your own exacting standards.',
        'description': 'The Perfectionist is never satisfied with "good enough." Everything must be just right, every detail must be perfect, and every flaw must be eliminated. While this can lead to impressive achievements, it can also lead to paralysis when perfection proves impossible. The Perfectionist may be driven by a genuine desire for excellence or by a deep-seated fear of failure.'
    },
    'plotter': {
        'name': 'Plotter',
        'system': 'Regain Willpower whenever a complex plan you orchestrated comes to fruition.',
        'description': 'The Plotter lives for the intricacies of a well-laid scheme. Simple solutions are beneath them - why use a hammer when you can create an elaborate Rube Goldberg machine? The Plotter finds joy in watching all the pieces fall into place, even if a simpler solution might have been more effective.'
    },
    'predator': {
        'name': 'Predator',
        'system': 'Regain Willpower whenever you successfully stalk and strike at prey, particularly if they never saw you coming.',
        'description': 'The Predator knows their place in the food chain - right at the top. They live for the thrill of the hunt and the satisfaction of the kill. Whether their hunting is literal or metaphorical, they approach their targets with the patience and precision of a natural hunter.'
    },
    'rebel': {
        'name': 'Rebel',
        'system': 'Regain Willpower whenever you successfully defy authority or undermine the status quo.',
        'description': 'The Rebel cannot abide authority. Whether their resistance is based on principle or simple contrariness, they find satisfaction in bucking the system and proving that rules are made to be broken. The Rebel may fight for a cause or simply for the thrill of defiance.'
    },
    'rogue': {
        'name': 'Rogue',
        'system': 'Regain Willpower whenever you trick someone and profit from it without getting caught.',
        'description': 'The Rogue lives by their wits and charm, always looking for the angle and the easy score. They take pride in their cleverness and ability to outmaneuver others, whether through cunning schemes or quick thinking. While not necessarily malicious, they have few qualms about bending rules or taking advantage of opportunities.'
    },
    'sadist': {
        'name': 'Sadist',
        'system': 'Regain Willpower whenever you inflict suffering upon others for your own satisfaction.',
        'description': 'The Sadist finds pleasure in the pain of others. Whether physical or emotional, the suffering they cause brings them a deep satisfaction. Some sadists are calculating and methodical, while others are more impulsive, but all share a fundamental drive to hurt others.'
    },
    'scientist': {
        'name': 'Scientist',
        'system': 'Regain Willpower whenever you discover something new through careful observation and testing.',
        'description': 'The Scientist approaches everything with analytical precision. They believe in the power of observation, experimentation, and empirical evidence. While they may work in traditional scientific fields, their methodical approach can apply to any area of study or interest.'
    },
    'sociopath': {
        'name': 'Sociopath',
        'system': 'Regain Willpower whenever you manipulate someone by pretending to feel emotions you don\'t actually experience.',
        'description': 'The Sociopath sees others as tools to be used and discarded. They understand emotions intellectually but don\'t experience them normally, instead using this understanding to manipulate others. They may be charming and charismatic, but it\'s all an act designed to get what they want.'
    },
    'soldier': {
        'name': 'Soldier',
        'system': 'Regain Willpower whenever you follow orders and complete a mission despite personal risk or reservations.',
        'description': 'The Soldier lives by a code of duty and discipline. Whether serving a literal military organization or simply approaching life with military precision, they find comfort and purpose in following orders and completing missions. The chain of command gives their life structure and meaning.'
    },
    'survivor': {
        'name': 'Survivor',
        'system': 'Regain Willpower whenever you overcome a life-threatening situation through your own cunning or endurance.',
        'description': "The Survivor endures against all odds. They've learned to rely on their instincts and resourcefulness to make it through another day. Whether facing physical dangers or emotional trials, they find strength in their ability to persist where others would falter."
    },
    'thrill_seeker': {
        'name': 'Thrill-Seeker',
        'system': 'Regain Willpower whenever you successfully take a dangerous risk that you didn\'t have to.',
        'description': 'The Thrill-Seeker lives for the rush of adrenaline. They seek out danger and excitement, often taking unnecessary risks just for the thrill of it. While this can lead to impressive achievements, it can also result in reckless behavior and unnecessary danger.'
    },
    'traditionalist': {
        'name': 'Traditionalist',
        'system': 'Regain Willpower whenever you maintain your principles in the face of significant opposition.',
        'description': 'The Traditionalist holds fast to established ways and values. They believe in the wisdom of the past and resist change for its own sake. While this can provide stability and continuity, it can also lead to stagnation and inflexibility.'
    },
    'trickster': {
        'name': 'Trickster',
        'system': 'Regain Willpower whenever you create chaos or confusion in an otherwise orderly situation.',
        'description': 'The Trickster delights in causing chaos and confusion. They may have a higher purpose in mind, using disorder to teach lessons or expose hypocrisy, or they may simply enjoy watching the world burn. Either way, they find satisfaction in disrupting the status quo.'
    },
    'visionary': {
        'name': 'Visionary',
        'system': 'Regain Willpower whenever you convince others to follow your dream or unique perspective.',
        'description': 'The Visionary sees what others cannot - or will not - see. They are driven by their unique perspective and their desire to make others understand their vision. Whether their insights are brilliant or mad (or both), they are compelled to share them with the world.'
    },
    'addict': {
        'name': 'Addict',
        'system': 'Become utterly fixated on one passion.',
        'description': 'Regain Willpower when you gorge yourself on a chosen passion.'
    },
    'adherent': {
        'name': 'Adherent',
        'system': 'Pledge yourself to one cause above everything else.',
        'description': 'Regain Willpower when you remain loyal to your cause despite hardships.'
    },
    'adjudicator': {
        'name': 'Adjudicator',
        'system': 'Work to solve problems that affect your surroundings.',
        'description': 'Regain Willpower whenever your attempts at providing solutions yield immediate results.'
    },
    'artist': {
        'name': 'Artist',
        'system': 'Try to reach others through your creations.',
        'description': 'Regain Willpower whenever you reach an audience through your works.'
    },
    'barbarian': {
        'name': 'Barbarian',
        'system': 'Keep your distance from civilization, trusting the old ways.',
        'description': 'Regain Willpower when you prove the value of your “barbaric” ways over civilization.'
    },
    'caretaker': {
        'name': 'Caretaker',
        'system': 'Shepherd those around you to safety.',
        'description': 'Regain Willpower when you avert a disaster for your flock.'
    },
    'coward': {
        'name': 'Coward',
        'system': 'Hide your true self from others.',
        'description': 'Regain Willpower when you reveal something about yourself without being rejected.'
    },
    'deviant': {
        'name': 'Deviant',
        'system': 'Reject traditional social mores for your own.',
        'description': 'Regain Willpower whenever you manage to flout social customs.'
    },
    'devil\'s-advocate': {
        'name': "Devil's Advocate",
        'system': 'Question the commands from your superiors.',
        'description': 'Regain Willpower when your questions reveal flaws in a plan or structure.'
    },
    'futurist': {
        'name': 'Futurist',
        'system': 'Pledge yourself to new concepts and ideals.',
        'description': 'Regain Willpower whenever you first come upon a progressive idea or object.'
    },
    'heretic': {
        'name': 'Heretic',
        'system': 'Refuse to accept a commonly held creed.',
        'description': 'Regain Willpower whenever you challenge commonly held convictions and convince others of your belief.'
    },
    'hunter': {
        'name': 'Hunter',
        'system': 'Always prepare yourself for the hunt.',
        'description': 'Regain Willpower whenever you outperform a rival or defeat your prey through cunning and patience.'
    },
    'maniac': {
        'name': 'Maniac',
        'system': 'Be compelled by internal voices to strange actions.',
        'description': 'Regain Willpower whenever you fulfill a goal of the voices that goes against your immediate self-interests.'
    },
    'meddler': {
        'name': 'Meddler',
        'system': 'Constantly try to interfere in others\' affairs to aid them.',
        'description': 'Regain Willpower when your interference proves beneficial despite protests.'
    },
    'melancholic': {
        'name': 'Melancholic',
        'system': 'Feel ennui at all that you have lost.',
        'description': 'Regain Willpower whenever you cause others to question their cursed natures.'
    },
    'omega': {
        'name': 'Omega',
        'system': 'Accept your place at the bottom rung of your group.',
        'description': 'Regain Willpower whenever you achieve a deed worthy of recognition.'
    },
    'outsider': {
        'name': 'Outsider',
        'system': 'Define yourself by things you do not participate in.',
        'description': 'Regain Willpower whenever you learn something about yourself through decisions made by others.'
    },
    'paragon': {
        'name': 'Paragon',
        'system': 'Embody straightforwardness and simplicity.',
        'description': 'Regain Willpower whenever your straightforward approach proves more successful than deception.'
    },
    'penitent': {
        'name': 'Penitent',
        'system': 'Strive to do penance for your sins.',
        'description': 'Regain Willpower whenever you achieve absolution for a grievance.'
    },
    'quaestor': {
        'name': 'Quaestor',
        'system': 'Yearn to answer life\'s questions.',
        'description': 'Regain Willpower whenever you reach a concise life lesson that could become a rule of thumb.'
    },
    'reluctant-reborn': {
        'name': 'Reluctant Reborn',
        'system': 'Struggle with accepting your new life.',
        'description': 'Gain one permanent point of Willpower upon realizing and accepting the truth about what you have become, then choose a new Nature.'
    },
    'seer': {
        'name': 'Seer',
        'system': 'Glimpses of the future haunt you.',
        'description': 'Regain Willpower whenever your visions reveal an enigma or offer greater insights.'
    },
    'stoic': {
        'name': 'Stoic',
        'system': 'Maintain composure under all circumstances.',
        'description': 'Regain Willpower when you overcome setbacks and losses without succumbing to strong emotions.'
    },
    'tycoon': {
        'name': 'Tycoon',
        'system': 'Constantly plot to expand your resources.',
        'description': 'Regain Willpower whenever your plans yield maximum influence and profit.'
    },
    'vigilante': {
        'name': 'Vigilante',
        'system': 'Succeed in vengeance against a chosen target.',
        'description': 'Regain Willpower when you significantly hurt your target.'
    },
    'wanderer': {
        'name': 'Wanderer',
        'system': 'Never stay in one place and avoid attachments.',
        'description': 'Regain one Willpower point whenever you complete your purpose in a place, then move on, leaving no loose ends.'
    },
    'defender': {
        'name': 'Defender',
        'system': 'Protect something over yourself.',
        'description': 'Regain Willpower when you successfully defend your charge.'
    },
    'prophet': {
        'name': 'Prophet',
        'system': 'Insight is your greatest strength. Prophets tend to see things that are hidden to most people: secrets, omens, visions of the future, and so forth. Even if you lack the blessing/ curse of prophecy, few mysteries escape your sight. Ruthlessness is the traditional flaw of prophets. Driven by their vision of Truth, such people tend to be impatient, fanatical, and defiant of mortal power. You\'ll probably score lots of points for guts, but you might find those guts roasting on a spit in some ruler\'s torture garden. True prophets often meet unhappy ends... and they tend to take their followers down with them when they go.',
        'description': 'Regain Willpower when you speak Truth to power and inspire a successful change.'
    },
    'entertainer': {
        'name': "Entertainer",
        'system': "Life sucks. Good thing you're here to brighten things up! Maybe you're a satirist, kicking holes in the delusions surrounding you; or an actor, speaking for the folks who've forgotten what they needed to say. You could express the yearning that other people feel but cannot articulate, or simply bring a smile when joy is hard to find. Whatever it is that you do, though, it transcends mere silliness. Although you're not as driven as, say, the Artist described above, you are an artist too, revealing truth through entertainment. You're Fun and Entertaining to be around - important gifts when folks are fighting for their lives. Beyond that, you inspire people to look past despair and find beauty and humor even in ugly situations. Ego, however, is your biggest hurdle. Doing what you do, it's pretty easy to get lost in your own illusions of importance. Now, you need a strong ego in order to put yourself out there day after day; unless you learn to balance it with authentic self-reflection and restraint, however, you're just setting yourself up to be a punch line somewhere down the road. Ascension demands more than artistic sensibilities. To transcend your limitations, you need to swallow your ego and accept that you can't always be the star. ",
        'description': "Regain Willpower when your work makes some significant change in the lives of people around you."
    },
    'guardian': {
        'name': "Guardian",
        'system': "Shepherding the weak through the Valley of Darkness, you are truly your brother's keeper and the finder of lost children. You save your great vengeance and furious anger for those who would poison and betray your brothers, sisters, and so forth. Pop-culture quotations aside, you take your duty seriously_ someone, after all, needs to protect folks who cannot, or sometimes will not, protect themselves. In essence, this ideal  guides all Awakened factions; even the Fallen, in their twisted way, often justify themselves by claiming to be guardians of a rejected world. Courage is your calling card. It takes guts to do what you do, and by all the Gods, you've got fortitude to spare. Admirable though it may be, your dedication to Self-Sacrifice could be your Achilles' heel. Lots of would-be Guardians wind up ground into mulch by constant conflict. A knight needs battle, true enough; but until she learns when to stop fighting - to step aside, perhaps, and let people defend themselves or else make their own decisions - a Guardian can become a martyr, a bully, or just one more monster in a world already full of them.",
        'description': "Regain Willpower when your actions directly save a weaker group or character from assured destruction."
    },
    'heretic': {
        'name': "Heretic",
        'system': "Grab your chainsaw and line up the sacred cows! Whatever your companions regard as 'orthodox' and proper is, to you, anathema. Perhaps you follow a confrontational approach to your culture's institutions; or you undermine authorities that you consider to be corrupt. You could introduce a decidedly unconventional change to an established tradition (or Tradition), or revere a path or godhead that most folks consider to be 'evil.' Linguistically, heretic combines implications of choice, belief, and the act of taking something valuable. Whether your heresy is religious, philosophical, political, or some mixture of them all, you refuse to accept the popular (and perhaps demanded) creed. Integrity drives you. After all, if you did not possess immense (often dangerous) degrees of integrity, you would simply go with the flow, not resist it the way you do. And yet, that Iconoclasm could get you_ and other people_ killed. That is, after all, what often happens to heretics. Folks don't like to have their cherished beliefs overturned, and so as you run through life's market flipping over tables in the name of your belief, remember that one of those tables could very well land on top of you.",
        'description': "Regain Willpower whenever you challenge a commonly held conviction and manage to change people's minds about that belief."
    },
    'romantic': {
        'name': "Romantic",
        'system': "In a world filled with ugliness, you seek and find beauty. Said beauty could be tragic (as detailed under the entries for Romance and Tragedy in this book's Chapter Five section Storytelling, Genre, and Mage, pp. 285-286), but that sense of melancholy makes it pure. High drama is your heartbeat. Passion is your joy. In the words of Patti Smith, you 'seek pleasure_ seek the nerves under your skin.' This quest is often painful, but that pain tells you you're alive. That Passion provides your deepest strength. When other folks hesitate, you plunge in, reveling in the raw excitement of life's dance. Enchanted by that dance, you can be pretty Careless about its effects. Like the original Romantics, your excesses hurt a lot of people. Eventually, you'll need to develop a greater sense of responsibility and moderation if you ever wish to Ascend.",
        'description': "Regain Willpower when you throw yourself into a gloriously ruinous affair or reveal life's howling beauty to a previously hesitant soul."
    },
    'zealot': {
        'name': "Zealot",
        'system': "A flipside to the Heretic, you pursue your beliefs with extreme enthusiasm. Moderation, to you, is weakness - a true believer will do pretty much anything for the cause! Whatever your cause may be - a political philosophy, a theological creed, a social movement, whatever matters most to you - it's something that inspires and guides your behavior, associations, activities and, most importantly, your focus: the beliefs, practices, and instruments through which you shape your magickal feats. Obviously, the player for a zealot mage must determine, in detail, what his character believes in, why he believes in it, how it shapes his personality, and what it takes to challenge and perhaps alter or destroy that belief. Zealots hold deeper convictions than even the average mage would hold, and so it's vital to know what those convictions might be.Conviction is your armor, shield, and sword. That steadfast confidence in your beliefs will stand with you when no one and nothing else will do.Such Extremity, however, can inspire abhorrent acts in the name of your beliefs. A zealot, after all, is by definition someone who will sacrifice anything and anyone for the cause. A zealot mage, in particular, can be a terrifying force. The Fallen, Mad, and Technocracy have plenty of uses for such people, and even the supposedly moderate Traditions and Disparates have embers who'd sooner kill a busload of kids than step back on their convictions.",
        'description': "Regain Willpower whenever your deeply held beliefs are proved right through your behavior."
    }
}

def validate_archetype(archetype_name: str) -> tuple[bool, str]:
    """
    Validate that an archetype exists and is valid.
    Returns (is_valid, error_message) tuple.
    """
    # Convert spaces to hyphens and lowercase for dictionary lookup
    lookup_key = archetype_name.lower().replace(' ', '-')
    if lookup_key not in ARCHETYPES:
        valid_archetypes = ', '.join(sorted([a['name'] for a in ARCHETYPES.values()]))
        return False, f"Invalid archetype. Valid archetypes are: {valid_archetypes}"
    return True, ""

def get_archetype_info(archetype_name: str) -> dict:
    """
    Get the full information for an archetype.
    Returns None if archetype doesn't exist.
    """
    # Convert spaces to hyphens and lowercase for dictionary lookup
    lookup_key = archetype_name.lower().replace(' ', '-')
    return ARCHETYPES.get(lookup_key) 