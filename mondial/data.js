/* ============================================================
   LE MONDIAL, POUR MARGOT — content
   Researched 10 July 2026 (quarterfinal week) by a small fleet
   of research agents; scores verified against FIFA/ESPN/Wikipedia.
   ============================================================ */

const MONDIAL = {
  asOf: "10 July 2026",

  tournament: {
    sub: "Three host countries, 48 teams, 104 matches — the biggest World Cup ever played. And all six of your teams are still alive.",
    prose: [
      `Every four years, almost every country on Earth sends its best eleven to the same party, and for a month the planet synchronizes its heartbeat. This edition — June 11 to July 19, 2026 — is the biggest ever: the first hosted by <strong>three countries at once</strong> (the United States, Canada and Mexico, across 16 cities), the first with <strong>48 teams</strong> instead of 32, and the first with 104 matches. It opened at the legendary Estadio Azteca in Mexico City — the only stadium on Earth to host three World Cup openings — and it ends Sunday <strong>July 19 at MetLife Stadium</strong>, just outside New York.`,
      `The format is a funnel. The 48 teams were split into twelve groups of four; everyone played three matches (win = 3 points, draw = 1), and 32 survived into the knockout rounds — where losing once means flying home, with extra time and the cruelty of penalty shootouts if a match won't settle itself. We are now at the quarterfinals: <strong>eight teams left</strong>, and improbably, all six teams in this guide are among them. The hosts are not: the USA, Canada and Mexico were all eliminated in the round of 16, so the party continues in their living room without them.`,
      `One more thing you should know, because the whole tournament vibrates with it: this is billed as the <em>last dance</em> for 39-year-old Lionel Messi of Argentina — many people's greatest player of all time — while France's Kylian Mbappé, the man he beat in the epic 2022 final, sits level with him at eight goals in the race for the Golden Boot (the top-scorer trophy). The bracket keeps them apart until the final. Football does not usually write scripts this good, and yet.`,
    ],
    bracketNote: `Read it like a family tree: France, Spain and Belgium live on the <strong>top half</strong>, Norway, England, Argentina and Switzerland on the <strong>bottom</strong> — so France and Argentina, the two finalists of 2022, can only meet again in the final on July 19. The semifinals are July 14 in Dallas (Bastille Day — <span class="fr">le destin ?</span>) and July 15 in Atlanta.`,
    storylines: [
      { q: "The fairytale: Norway", a: "At their first World Cup since 1998, Norway stunned five-time champions Brazil 2–1 in the round of 16 — Haaland scored twice in the last eleven minutes — to reach their first quarterfinal ever. A nation of 5.5 million has stopped functioning." },
      { q: "The Golden Boot duel", a: "Mbappé 8 goals, Messi 8, Haaland 7, Kane 6. Four superstars, all still alive, hunting the top-scorer trophy head-to-head. It could literally be decided in the final." },
      { q: "Messi's last dance", a: "At 39, Argentina's captain dragged the defending champions back from 2–0 down against Egypt with three goals in 13 minutes. Every match might be the last of the greatest career football has seen." },
      { q: "France, the machine", a: "The only team to win all six matches, never once needing extra time. The attack — Mbappé, Dembélé, Doué, Olise — is averaging nearly three goals a game while looking faintly bored." },
      { q: "Host heartbreak ×3", a: "The USA were demolished 4–1 by Belgium, Canada 3–0 by Morocco, Mexico edged 3–2 by England — none of the three host nations reached the last eight. Awkward silence in 16 stadiums." },
      { q: "The giants' graveyard", a: "Brazil out (to Norway!), Portugal out (Ronaldo's last World Cup ended by Spain, 0–1), Uruguay out in the groups. Meanwhile Switzerland quietly penalty-shootout-ed their way into the last eight without scoring." },
      { q: "Spain's strange perfection", a: "The great attacking stylists have not conceded a single goal in five matches — six consecutive World Cup clean sheets, a record no one saw coming. The flair team wins 1–0 now." },
    ],
  },

  bracket: {
    qfs: [
      { tag: "QF · 9 July · Boston", a: "France", b: "Morocco", scoreA: "2", scoreB: "0", winner: "a" },
      { tag: "QF · 10 July · Los Angeles", a: "Spain", b: "Belgium", scoreA: null, scoreB: null },
      { tag: "QF · 11 July · Miami", a: "Norway", b: "England", scoreA: null, scoreB: null },
      { tag: "QF · 11 July · Kansas City", a: "Argentina", b: "Switzerland", scoreA: null, scoreB: null },
    ],
    sfs: [
      { tag: "SF · 14 July · Dallas", a: "France", b: "Spain / Belgium" },
      { tag: "SF · 15 July · Atlanta", a: "Norway / England", b: "Argentina / Suisse" },
    ],
    final: { tag: "Final · 19 July · New York", a: null, b: null },
  },

  teams: [

    /* ================= FRANCE ================= */
    {
      id: "fra",
      name: "France",
      nickname: "Les Bleus — with le coq gaulois on the badge",
      accent: "var(--acc-fra)",
      flag: ["#0055A4", "#f6f3ec", "#EF4135"],
      coach: "Didier Deschamps",
      formation: "4-2-3-1",
      formationKey: "4-2-3-1",
      styleKeywords: ["lightning counters", "pragmatic defending", "tournament know-how"],
      ratings: { possession: 6, pressing: 6, counterAttack: 10, physicality: 8, flair: 9, defensiveSolidity: 8 },
      philosophy: [
        `Imagine a chess grandmaster who is happy to let you push your pawns forward all afternoon — because he knows that the moment you overreach, his queen crosses the entire board in one move and it's checkmate. That is France under Didier Deschamps, the granite-jawed coach who captained France to the 1998 title, has run the team since 2012, and has announced this World Cup is his farewell. Les Bleus rarely try to dazzle you with endless passing the way Spain does. They build a patient, almost stubborn defensive structure, invite the opponent forward, and then strike with terrifying speed — Kylian Mbappé sprinting into open grass is the most feared sight in world football. They've won all six games this tournament without ever needing extra time, often while barely seeming to break a sweat. It can look almost lazy. It is anything but: it's economy of effort, the way a great chef doesn't use forty ingredients when four perfect ones will do.`,
        `What makes France special isn't just tactics — it's the production line. No country on Earth grows footballers like France: the national academy at Clairefontaine and the concrete pitches of the banlieues churn out so much talent that France's <em>reserves</em> would make a World Cup semifinal on their own. Mbappé himself is a kid from Bondy, in Seine-Saint-Denis. This team is the face of modern France — sons of immigrants from Africa and the Caribbean alongside kids from Normandy, the <em>black-blanc-beur</em> ideal first celebrated when the 1998 team won it all at home. When Les Bleus win, it feels, for a moment, like the whole messy, glorious French project works.`,
        `The culture around the team is pure pragmatism with a wink of arrogance. Deschamps is endlessly criticized at home for being boring, for handbrake football, for wasting the most gifted squad ever assembled — and he just keeps winning. Think of French cuisine's two schools arguing forever: the critics want nouvelle cuisine, inventive and beautiful; Deschamps serves cassoulet — heavy, traditional, unfashionable, and absolutely guaranteed to fill you up. Three straight World Cup semifinals say the cassoulet is working.`,
      ],
      keyPlayers: [
        { name: "Mike Maignan", pos: "GK", posLabel: "Goalkeeper", club: "AC Milan", age: 31, why: "Nicknamed 'Magic Mike'. Clean sheets in all three knockout games — France have conceded just two goals all tournament, and he's a big reason why." },
        { name: "William Saliba", pos: "CB", posLabel: "Center-back", club: "Arsenal", age: 25, why: "A defender so calm and quick that strikers seem to bounce off an invisible force field. Part of the deepest stock of defenders any nation possesses." },
        { name: "Aurélien Tchouaméni", pos: "CDM", posLabel: "Defensive midfield", club: "Real Madrid", age: 26, why: "The team's bodyguard — he breaks up attacks before they become dangerous, the unglamorous job that lets the artists paint. Also the squad's resident intellectual." },
        { name: "Kylian Mbappé", pos: "LM", posLabel: "Left wing · captain", club: "Real Madrid", age: 27, num: 10, why: "The captain and the fastest famous person on the planet — watching him run is like watching a TGV overtake cyclists. Eight goals this tournament, and now France's all-time record scorer." },
        { name: "Désiré Doué", pos: "CAM", posLabel: "Attacking midfield", club: "Paris Saint-Germain", age: 21, why: "The kid. At 21, the newest jewel of the French production line — velvet touches and cheeky invention. Remember the name; he may own the 2030 World Cup." },
        { name: "Michael Olise", pos: "RM", posLabel: "Right wing", club: "Bayern Munich", age: 24, why: "The elegant one. Where Mbappé is speed, Olise is silk — a languid left-footed creator who seems to play in slow motion while everyone else panics." },
        { name: "Ousmane Dembélé", pos: "ST", posLabel: "Striker", club: "Paris Saint-Germain", age: 29, why: "The reigning Ballon d'Or holder and the tournament's great redemption story. Genuinely two-footed: defenders never know which way he'll go — honestly, neither does he. A hat-trick against Norway, the clincher against Morocco." },
        { name: "Marcus Thuram", pos: "ST", posLabel: "Super-sub striker", club: "Inter Milan", age: 28, bench: true, why: "The battering ram off the bench — and football royalty: his father Lilian was a hero of the 1998 win. Twenty-eight years later, the son chases the same trophy." },
      ],
      starPlayer: {
        name: "Kylian Mbappé",
        story: `Kylian Mbappé grew up in Bondy, a tower-block suburb northeast of Paris, where a mural of his face now covers an entire building: « Ville des possibles ». At 19 he scored in a World Cup final and won it (2018); at 23 he scored a hat-trick in the next final and still lost it, on penalties, to Messi's Argentina (2022). Now 27, captain, he is on a collision course with history: eight goals this tournament, level with Messi for the Golden Boot, and his 20 career World Cup goals sit one behind Messi's all-time record of 21. He scored against Morocco in the quarterfinal, then limped off with an ice pack on his ankle — an entire nation is currently monitoring that ankle like anxious parents with a newborn. If the bracket holds, Mbappé vs Messi in the final would be the sequel to the greatest match ever played, with the all-time record on the line.`,
      },
      path: {
        group: "I — won it with a perfect 3/3",
        matches: [
          { round: "Group · 16 June", fixture: "France 3–1 Senegal", note: "Mbappé scores twice and becomes France's all-time record scorer, passing Olivier Giroud." },
          { round: "Group · 22 June", fixture: "France 3–0 Iraq", note: "Routine. Mbappé ×2, Dembélé." },
          { round: "Group · 26 June", fixture: "France 4–1 Norway", note: "A Dembélé first-half hat-trick against tomorrow-maybe-opponents. Remember this one for the compare section." },
          { round: "Round of 32 · 30 June", fixture: "France 3–0 Sweden", note: "Mbappé ×2 in New Jersey — a preview of the final's stadium." },
          { round: "Round of 16 · 4 July", fixture: "France 1–0 Paraguay", note: "A Mbappé penalty — his 11th World Cup knockout goal, a record." },
          { round: "Quarterfinal · 9 July", fixture: "France 2–0 Morocco", note: "A rematch of the 2022 semifinal, same scoreline. Mbappé scored, then went off with a knock — <em>the ankle watch has begun</em>." },
          { round: "Semifinal · 14 July · Dallas", fixture: "France vs Spain-or-Belgium", note: "On Bastille Day. The fireworks would write themselves.", upcoming: true },
        ],
        status: `Alive, and arguably the favorite: six wins from six, never needing extra time, a third consecutive World Cup semifinal. Next: Dallas, July 14 — <strong>le quatorze juillet</strong> — against the winner of Spain–Belgium.`,
      },
      history: `France's World Cup story is a rollercoaster with two golden peaks. In 1998, hosting the tournament, a multicultural team led by the balletic Zinédine Zidane beat Brazil 3–0 in the final; a million people flooded the Champs-Élysées and Zidane's face was projected onto the Arc de Triomphe. In 2006 came operatic heartbreak — Zidane, in the last match of his career, headbutted an Italian defender and was sent off as France lost the final on penalties. Redemption arrived in 2018 with a new golden generation and a 19-year-old Mbappé: a second star above the rooster. In 2022 they lost the final to Argentina on penalties despite Mbappé scoring three — a 3–3 thriller many call the greatest final ever. Since 2018, no nation on Earth has been this consistently good.`,
      facts: [
        { q: "Bastille Day semifinal", a: "France's semifinal falls on July 14 — le quatorze juillet. If Les Bleus win on the national holiday, the fireworks will write themselves." },
        { q: "Why is the away kit green?!", a: "First green shirt in France's history: mint for the oxidized Statue of Liberty — France's 1886 gift to America — and copper trim for the metal she was born in. Nike calls it 'Liberté'. It's also the palette of this entire page." },
        { q: "The anthem", a: "Before every match the team belts out La Marseillaise, plausibly the most bloodthirsty anthem ever written ('let impure blood water our furrows!'). Sung by 60,000 people, it produces goosebumps regardless of allegiance." },
        { q: "Deschamps' exit", a: "He won the World Cup as France's captain (1998) and as coach (2018) — only the third man ever to do both — and retires after this tournament. One more trophy would be the most Hollywood exit imaginable." },
        { q: "The B-team joke", a: "France's talent pipeline is so absurd that stars like Camavinga didn't even make the 26. Pundits joke the French B-team would be a top-eight seed at this World Cup. They're only half joking." },
        { q: "Thuram, again", a: "Marcus Thuram chases the trophy his father Lilian won in 1998 — when Marcus was one year old. Same badge, same dream, 28 years apart." },
      ],
    },

    /* ================= BELGIUM ================= */
    {
      id: "bel",
      name: "Belgium",
      nickname: "Les Diables Rouges / De Rode Duivels — the Red Devils, in both national languages",
      accent: "var(--acc-bel)",
      flag: ["#2d2926", "#FDDA24", "#EF3340"],
      coach: "Rudi Garcia (yes — a Frenchman)",
      formation: "4-3-3",
      formationKey: "4-3-3",
      styleKeywords: ["one-pass magic", "wing speed", "slow starters, big finishers"],
      ratings: { possession: 6, pressing: 6, counterAttack: 9, physicality: 7, flair: 8, defensiveSolidity: 5 },
      philosophy: [
        `If Spain plays football like a chess grandmaster and Brazil like a samba band, Belgium plays it like a jazz quartet with one genius soloist. The team can look sleepy for long stretches — polite, patient, passing the ball around like dinner guests waiting for someone to open the wine — and then, in a heartbeat, Kevin De Bruyne spots a gap no one else on Earth can see, threads a pass through it, and Jérémy Doku or Romelu Lukaku turns that single note into a goal. Belgian football at its best is not about controlling the whole game; it's about the four or five seconds of improvised brilliance that decide it. This tournament has been exactly that: a frustrating draw with Egypt, a goalless yawn against Iran — then an eruption of twelve goals in three matches.`,
        `To understand the culture, think of Belgian cuisine: a small country wedged between France, the Netherlands and Germany that quietly does certain things better than all its bigger neighbors — chocolate, beer, frites (yes, fries are Belgian, whatever Parisians tell you). Football is the same. Eleven million people, fewer than Île-de-France, yet for years Belgium sat at number one in the world rankings. In the 2000s the country rebuilt its youth academies around skill, and out came a "Golden Generation" — De Bruyne, Lukaku, Courtois, Hazard — arguably the most talented group ever produced per capita by any nation. The tragedy, and the romance: they never won anything. They are football's great unfinished symphony.`,
        `One more layer: Belgium is famously divided between Dutch-speaking Flanders and French-speaking Wallonia, two communities that argue about nearly everything — except the Red Devils. The national team is the one institution where the whole country wears the same shirt; dressing-room talks often happen in English, as neutral ground. So when Belgium plays, it isn't just sport, it's the country's most successful unity project. And with De Bruyne at 35 playing his farewell World Cup, every match feels like the last encore of a beloved band — which is why their comebacks this summer have been so operatic.`,
      ],
      keyPlayers: [
        { name: "Thibaut Courtois", pos: "GK", posLabel: "Goalkeeper", club: "Real Madrid", age: 34, num: 1, why: "A two-meter wall, considered among the best keepers of his era. When Belgium's defense wobbles — which it does — he is the last-second miracle worker." },
        { name: "Youri Tielemans", pos: "CM", posLabel: "Midfield", club: "Aston Villa", age: 29, why: "The cool head. Scored the winning penalty against Senegal in the 125th minute — the latest goal in World Cup history — after a seven-minute video review. Imagine keeping your nerve through that." },
        { name: "Kevin De Bruyne", pos: "CAM", posLabel: "Playmaker · captain", club: "Napoli", age: 35, num: 7, why: "The conductor, playing his final World Cup. When he has the ball, expect something to happen within seconds." },
        { name: "Jérémy Doku", pos: "LW", posLabel: "Left wing", club: "Manchester City", age: 24, why: "The entertainer — a tiny, explosive winger who dribbles like the ball is glued to his shoe. Flew to London mid-tournament for the birth of his son, flew back, starred in the 5–1 over New Zealand." },
        { name: "Romelu Lukaku", pos: "ST", posLabel: "Striker", club: "Napoli", age: 33, why: "The battering ram with a soft heart: Belgium's all-time top scorer, built like a rugby player, speaks about six languages. His late goals turned this tournament around." },
        { name: "Charles De Ketelaere", pos: "RW", posLabel: "Forward", club: "Atalanta", age: 25, why: "The elegant heir, 'CDK' — a tall, graceful forward who glides rather than runs. Quiet in the groups, then two goals against the USA: the new generation announcing itself just as the old one says goodbye." },
        { name: "Leandro Trossard", pos: "LW", posLabel: "Forward (utility)", club: "Arsenal", age: 31, bench: true, why: "The Swiss Army knife — plays anywhere across the attack, scored twice in the New Zealand rout. Always in the right place; the kind of player coaches adore." },
      ],
      starPlayer: {
        name: "Kevin De Bruyne",
        story: `Picture a pale, unassuming red-headed man who looks more like a quiet accountant than a superstar — until the ball reaches his feet. Kevin De Bruyne, 35, is widely considered the finest passer of his generation: he strikes long, curling passes that land on a teammate's toe from 50 meters, the way a great chef plates a dish — precise, effortless-looking, impossible to copy. He has every club trophy imaginable and nothing with Belgium, the country he has carried since he was a teenager. He was there for all the heartbreaks — including the 2018 semifinal loss to France that Belgians still haven't forgiven. This is, by his own admission, his last World Cup; he even turned 35 during the group stage, two days after conducting the 5–1 demolition of New Zealand. Every pass he plays now in America is a farewell letter, and the whole of Belgium is reading over his shoulder.`,
      },
      path: {
        group: "G — won it, the hard way",
        matches: [
          { round: "Group · 15 June", fixture: "Belgium 1–1 Egypt", note: "A stodgy start — rescued by an own goal forced by Lukaku's run." },
          { round: "Group · 21 June", fixture: "Belgium 0–0 Iran", note: "A goalless yawn, with Doku out ill. Belgian fatalism levels: high." },
          { round: "Group · 26 June", fixture: "Belgium 5–1 New Zealand", note: "The awakening: Trossard ×2, De Bruyne, Lukaku, Saelemaekers." },
          { round: "Round of 32 · 1 July", fixture: "Belgium 3–2 Senegal (a.e.t.)", note: "Down 2–0 with minutes left, then Lukaku 86', Tielemans 89', and a Tielemans penalty at 124:44 — <em>the latest goal in World Cup history</em>, after a 7-minute VAR review." },
          { round: "Round of 16 · 6 July", fixture: "Belgium 4–1 USA", note: "De Ketelaere ×2, Vanaken, Lukaku — the host nation's dream, dismantled." },
          { round: "Quarterfinal · TODAY, 10 July", fixture: "Spain vs Belgium — Los Angeles", note: "The ultimate contrast: Spain haven't conceded all tournament; Belgium have scored 3+ in three straight games.", upcoming: true },
        ],
        status: `Alive and dangerous — they play Spain <strong>today</strong> at SoFi Stadium, Los Angeles (kickoff 3 p.m. ET, 9 p.m. in France). Spain are favorites. Belgium have been writing comeback operas all summer. Watch this one.`,
      },
      history: `Belgium's World Cup story is the tale of the eternal almost. Semifinalists in 1986, dismantled by a young Diego Maradona at his peak. Then decades of decency without glory — until the Golden Generation of the 2010s made Belgium everyone's clever pick. The peak was 2018: they knocked out mighty Brazil in a breathtaking quarterfinal, then lost the semifinal 1–0… to France, a wound that still stings in Brussels. They finished third, their best ever, but third was never the dream. Qatar 2022 was the nadir — the aging stars bickered and crashed out in the group stage. Which makes 2026 the redemption arc: same old heroes, one last ride, and suddenly they're in a quarterfinal scoring goals for fun. Belgium have never won the World Cup. Every neutral with a heart is watching.`,
      facts: [
        { q: "« Vous avez le seum »", a: "After France beat Belgium in the 2018 semifinal, French fans teased Belgians with 'vous avez le seum' ('you're salty'). Belgium's tourism board embraced the joke, and the two countries have been lovingly trolling each other since. The friendliest bitter rivalry in Europe." },
        { q: "The coach is French", a: "Rudi Garcia — ex-Lille, Roma, Marseille, Lyon — coaches Belgium. So whatever happens to Les Diables, a French brain is partly responsible. Margot, this is your loophole for supporting two teams." },
        { q: "Ceci n'est pas un maillot", a: "Belgium's away shirt is sky-blue with pink clouds, a tribute to the surrealist René Magritte — and inside the collar it reads 'Ceci n'est pas un maillot'. Widely called the most beautiful shirt of the tournament." },
        { q: "The latest goal ever", a: "Tielemans' penalty against Senegal went in at 124 minutes 44 seconds — the latest goal in World Cup history, after a seven-minute VAR soap opera. Belgian suffering is never brief." },
        { q: "Three anthems in one", a: "La Brabançonne has official versions in French, Dutch AND German — and the squad's dressing-room talks are often in English, the neutral language that offends neither Flemings nor Walloons." },
        { q: "No. 1 with no trophy", a: "For years Belgium — population 11 million — was ranked the #1 football nation on Earth without winning anything, a paradox Belgians discuss with the same fatalistic humor they apply to their weather." },
      ],
    },

    /* ================= SPAIN ================= */
    {
      id: "esp",
      name: "Spain",
      nickname: "La Roja — the Red One; historically La Furia Roja, the Red Fury",
      accent: "var(--acc-esp)",
      flag: ["#AA151B", "#F1BF00", "#AA151B"],
      coach: "Luis de la Fuente",
      formation: "4-3-3",
      formationKey: "4-3-3",
      styleKeywords: ["tiki-taka possession", "high press", "wing wizardry"],
      ratings: { possession: 10, pressing: 8, counterAttack: 6, physicality: 6, flair: 9, defensiveSolidity: 10 },
      philosophy: [
        `If most teams treat the ball like a hot potato — get it, get rid of it, hope for the best — Spain treats it like the family silver. Their whole idea, refined over twenty years, is beautifully simple: <em>if we have the ball, you can't score, and eventually you'll get so dizzy chasing it that you'll leave a door open</em>. The style has a name, "tiki-taka", which sounds like a nursery rhyme and looks like one too: hundreds of short passes, pop-pop-pop, players arranged in little triangles so the one with the ball always has two friends nearby. Watching it is less like sport and more like a jazz trio trading solos — everyone knows the standard, nobody knows tonight's version, and the pleasure is in the improvisation within the pattern.`,
        `The culture is just as distinctive. Many of these players grew up together at La Masia, Barcelona's famous academy, where children are taught from age ten that losing the ball is a small moral failure. That's why Spain can field a 19-year-old defender (Pau Cubarsí) who passes like a philosopher and an 18-year-old winger (Lamine Yamal) who plays with the cheek of a kid in a schoolyard: they were raised in the doctrine. Other countries have great chefs; Spain has a national gastronomy — a shared grammar of how the game should taste, passed down generations.`,
        `Here's the delicious twist of this World Cup: the team famous for feasts has been serving consommé. Spain has won ugly-beautiful — endless elegant passing, but matches finishing 1–0, 1–0, the winner sometimes arriving in the 91st minute, and <strong>not one single goal conceded in five games</strong>. It's chess played by poets: they still move the pieces gorgeously, but what wins games right now is that their king is never, ever in danger. And for you, Margot, there's a frisson: Spain are France's great stylistic rival and recent tormentor — the team that knocked Les Bleus out of Euro 2024. If both win their next match, they meet in the semifinal. On Bastille Day.`,
      ],
      keyPlayers: [
        { name: "Unai Simón", pos: "GK", posLabel: "Goalkeeper", club: "Athletic Club", age: 29, num: 23, why: "Has not fished a single ball out of his net all tournament. Five matches, zero conceded. Some nights he's nearly a spectator; when needed, a wall." },
        { name: "Pau Cubarsí", pos: "CB", posLabel: "Center-back", club: "FC Barcelona", age: 19, num: 22, why: "A 19-year-old with the calm of a 34-year-old, passing out from the back so cleanly he's practically an extra midfielder. The purest product of Barcelona's conveyor belt." },
        { name: "Rodri", pos: "CDM", posLabel: "Midfield anchor", club: "Manchester City", age: 30, num: 16, why: "The metronome. Touches the ball more than anyone and decides the tempo of the entire match. Won the 2024 Ballon d'Or — first Spanish man since 1960." },
        { name: "Pedri", pos: "CM", posLabel: "Midfield", club: "FC Barcelona", age: 23, num: 20, why: "The artist — glides past opponents as if they were traffic cones. Spaniards compare him to Iniesta, which is like a young French singer being compared to Piaf." },
        { name: "Dani Olmo", pos: "CAM", posLabel: "Attacking midfield", club: "FC Barcelona", age: 28, num: 10, why: "The clever connector between midfield and attack — and holder of the iconic number 10 everyone assumed would go to Yamal. Seniority has its privileges." },
        { name: "Lamine Yamal", pos: "RW", posLabel: "Right wing", club: "FC Barcelona", age: 18, num: 19, why: "The face of the tournament: an 18-year-old who dribbles like the ball is glued to his left foot and grins while doing it. Turns 19 on July 13 — possibly in a World Cup semifinal." },
        { name: "Nico Williams", pos: "LW", posLabel: "Left wing", club: "Athletic Club", age: 23, num: 17, why: "Yamal's best friend and partner in crime on the opposite wing — pure speed and joy, choreographed-handshake goal celebrations included." },
        { name: "Mikel Oyarzabal", pos: "ST", posLabel: "Striker", club: "Real Sociedad", age: 29, num: 21, why: "The quiet Basque having the tournament of his life: four goals, plus he scored the winner in the Euro 2024 final. The man for the big moment, minus the ego." },
      ],
      starPlayer: {
        name: "Lamine Yamal",
        story: `Here is a photograph worth knowing: in 2007, for a charity calendar, a 20-year-old Lionel Messi was photographed bathing a baby in a plastic tub. That baby was Lamine Yamal. Eighteen years later, the baby is the most electrifying footballer on Earth. Born in Catalonia to a Moroccan father and an Equatoguinean mother, raised in Barcelona's academy, Yamal plays the way children play in the street: dribbling first, apologizing never. France already knows him painfully well — at Euro 2024, the day before his 17th birthday, he curled an outrageous goal past the French goalkeeper in the semifinal. At this World Cup he wears 19, not 10 (a seniority rule gave the iconic number to Dani Olmo, and Yamal shrugged: the number doesn't dribble). He turns 19 on July 13. Spain is quietly hoping he'll celebrate by reaching a World Cup semifinal, and given how this summer is going, you wouldn't bet against the kid from the bathtub.`,
      },
      path: {
        group: "H — won it with 7 points",
        matches: [
          { round: "Group · 15 June", fixture: "Spain 0–0 Cape Verde", note: "The shock of week one: tiny Cape Verde's keeper Vozinha made seven saves on his World Cup debut." },
          { round: "Group · 21 June", fixture: "Spain 4–0 Saudi Arabia", note: "Normal service: Yamal, Oyarzabal ×2, and an own goal." },
          { round: "Group · 26 June", fixture: "Spain 1–0 Uruguay", note: "Álex Baena's shot fumbled in; two-time champions Uruguay, eliminated." },
          { round: "Round of 32 · 2 July", fixture: "Spain 3–0 Austria", note: "Oyarzabal ×2, Pedro Porro. Serene." },
          { round: "Round of 16 · 6 July", fixture: "Spain 1–0 Portugal", note: "A 91st-minute winner from Mikel Merino — the goal that ended 41-year-old Cristiano Ronaldo's last World Cup." },
          { round: "Quarterfinal · TODAY, 10 July", fixture: "Spain vs Belgium — Los Angeles", note: "The wall meets the flood: zero goals conceded vs twelve scored in three games.", upcoming: true },
        ],
        status: `Alive and among the favorites — they play Belgium <strong>today</strong> in Los Angeles. Five matches unbeaten, zero goals conceded: six consecutive World Cup clean sheets, a record. Win, and it's France in the semifinal.`,
      },
      history: `For most of the 20th century, Spain was football's great underachiever — a country mad about the game that always fell apart at tournaments (best World Cup: fourth place, 1950). Then, between 2008 and 2012, everything changed: a golden generation of small, brilliant passers won the Euro, then the 2010 World Cup — Iniesta's extra-time goal remains one of Spanish sport's holiest moments — then another Euro, the only nation ever to win three straight major tournaments. Tiki-taka didn't just win; it changed how the world thought football should be played. After a fallow decade, the second wave arrived: in 2024, led by a 16-year-old Yamal, Spain won the Euro again — beating France in the semifinal, sorry Margot — and they've marched into this quarterfinal without conceding a goal, chasing their second star.`,
      facts: [
        { q: "The anthem with no words", a: "Spain's 'Marcha Real' has NO official lyrics — one of a handful in the world. While the French belt out La Marseillaise, Spanish players just hum, hand on heart. Every few years someone proposes lyrics; every few years Spain politely declines." },
        { q: "Zero Real Madrid players", a: "For the first time in World Cup history, Spain's squad contains not a single Real Madrid player — imagine France showing up without anyone from PSG. Barcelona supplied nine." },
        { q: "The number 10 drama", a: "Everyone assumed teen superstar Yamal would get the iconic 10. Spain assigns numbers by seniority: Dani Olmo has more caps, Olmo got the 10, Yamal kept 19. No tantrum ensued. The number doesn't dribble." },
        { q: "The Yamal–France thing", a: "Yamal announced himself to the world with an outrageous goal against France in the Euro 2024 semifinal, at 16. French defenders reportedly still see it in their dreams. A semifinal rematch is one win away." },
        { q: "They ended Ronaldo", a: "Spain's round-of-16 win eliminated Portugal and closed the World Cup career of 41-year-old Cristiano Ronaldo, the first man to score at six World Cups. Ever tidy, Spain escorted a legend to the exit with a 91st-minute goal." },
        { q: "The baby photo", a: "2007: Messi, 20, bathes an infant in a plastic tub for a charity calendar. The infant: Lamine Yamal. The photo resurfaces every time Yamal does something magical — which is to say, weekly." },
      ],
    },

    /* ================= NORWAY ================= */
    {
      id: "nor",
      name: "Norway",
      nickname: "Løvene — the Lions; or simply Landslaget, 'the national team' (Norwegians are charmingly literal)",
      accent: "var(--acc-nor)",
      flag: ["#BA0C2F", "#f6f3ec", "#00205B", "#f6f3ec", "#BA0C2F"],
      coach: "Ståle Solbakken",
      formation: "4-3-3 (compact, counter-punching)",
      formationKey: "4-3-3",
      styleKeywords: ["avalanche counters", "compact block", "route one to Haaland"],
      ratings: { possession: 5, pressing: 7, counterAttack: 9, physicality: 8, flair: 6, defensiveSolidity: 7 },
      philosophy: [
        `Imagine a fjord in winter: calm, grey, apparently asleep — and then an avalanche. That is Norway. They do not try to hold the ball and stroke it around prettily the way Spain does. Norway is happy to let YOU have the ball. They sit in a compact, disciplined block — eleven men rarely more than 30 meters apart, like a shield wall — and wait. The moment they win it, everything accelerates: two or three vertical passes, a winger sprinting like a startled elk, and the ball arriving at the feet (or head) of Erling Haaland, a 1.95m striker built like a Norse god who scores almost every time he's given half a chance. From "asleep" to "goal" in eight seconds. It's not pretty in the middle; it's devastating at the end.`,
        `If French football is haute cuisine — reductions, technique, a sauce that took three days — Norwegian football is Nordic cooking: few ingredients, all of them exceptional, nothing wasted. The two exceptional ingredients are Haaland, the most ruthless finisher on Earth, and Martin Ødegaard, the Arsenal captain who plays the chef, finding passes nobody else sees. Norway's other national genius is instructive too: chess champion Magnus Carlsen, famous not for flashy sacrifices but for grinding opponents down and pouncing on a single mistake. This team plays exactly like Carlsen — patient, unglamorous, error-free, then one moment of tactical violence and the game is over.`,
        `Culturally, this run means everything. Norway is a country of 5.5 million where cross-country skiing is king and football was long a lovable sideshow; they hadn't qualified for a World Cup since 1998. An entire generation grew up watching other nations' parties through the window. Now they've crashed the party with the best striker in the world, having knocked out Brazil, and the country has essentially stopped functioning. There is no arrogance in Norwegian fandom — they sing, they cry, they can't quite believe they're here — which makes them, currently, the tournament's most huggable team.`,
      ],
      keyPlayers: [
        { name: "Ørjan Nyland", pos: "GK", posLabel: "Goalkeeper", club: "Free agent (ex-Sevilla)", age: 35, why: "The grandfather of the team and its unlikely folk hero — the oldest Norwegian ever at a World Cup, he saved a penalty against Brazil. Fairy tales sometimes pick the least glamorous protagonist." },
        { name: "Kristoffer Ajer", pos: "CB", posLabel: "Center-back", club: "Brentford", age: 28, why: "The defensive anchor — a huge, calm center-back doing the unglamorous work that lets everyone praise Haaland. Every avalanche needs a mountain behind it." },
        { name: "Patrick Berg", pos: "CDM", posLabel: "Defensive midfield", club: "Bodø/Glimt", age: 28, why: "The heartbeat in front of the defense, and football royalty at home: third generation of Bergs to captain Bodø/Glimt, a club north of the Arctic Circle where they play in the snow." },
        { name: "Martin Ødegaard", pos: "CAM", posLabel: "Playmaker · captain", club: "Arsenal", age: 27, num: 10, why: "The captain and the brain — famous at 15, signed by Real Madrid at 16. If Haaland is the hammer, Ødegaard is the hand that aims it." },
        { name: "Antonio Nusa", pos: "LW", posLabel: "Left wing", club: "RB Leipzig", age: 21, why: "The kid electric. His breathtaking curler against Ivory Coast opened Norway's first-ever knockout win. When he runs at defenders, entire stadiums inhale." },
        { name: "Andreas Schjelderup", pos: "RW", posLabel: "Right wing", club: "Benfica", age: 22, why: "The quiet assassin of the Brazil game — set up both of Haaland's goals in the historic 2–1. A tireless winger in the season of his life." },
        { name: "Erling Haaland", pos: "ST", posLabel: "Striker", club: "Manchester City", age: 25, num: 9, why: "The best pure goalscorer in the world and the entire reason Norwegian children currently refuse to go to bed. Seven goals, one behind Messi and Mbappé in the Golden Boot race." },
        { name: "Alexander Sørloth", pos: "ST", posLabel: "Super-sub striker", club: "Atlético Madrid", age: 30, bench: true, why: "A second 1.95m Viking off the bench. When Norway needs a late goal, Solbakken simply bombards the box with both giants. Subtle it is not; effective it is." },
      ],
      starPlayer: {
        name: "Erling Haaland",
        story: `Erling Braut Haaland is what happens when Scandinavia decides to 3D-print a goalscorer. Born in Leeds (his father played in the Premier League), raised in the farming town of Bryne among tractors and rain, he grew into a 1.95m striker who moves like a sprinter and finishes like an accountant closing a ledger — cold, exact, no sentiment. For Norway he has been almost comically decisive: 16 goals in qualifying, then at this World Cup a brace against Iraq, a brace against Senegal, the late winner against Ivory Coast, and — the night Norway will never forget — two goals in the last eleven minutes to knock out Brazil. Off the pitch he is gloriously odd: meditates, eats like a caveman, sleeps in blue-light-blocking glasses, celebrates goals in the lotus position. Tomorrow he faces England — the country of his birth — with a semifinal on the line. Norwegians would trade a fjord for it.`,
      },
      path: {
        group: "I — runners-up behind France",
        matches: [
          { round: "Group · 16 June", fixture: "Norway 4–1 Iraq", note: "Haaland ×2. The 28-year wait ends with a party." },
          { round: "Group · 22 June", fixture: "Norway 3–2 Senegal", note: "Haaland ×2 again, in a thriller." },
          { round: "Group · 26 June", fixture: "Norway 1–4 France", note: "The one blemish — a Dembélé hat-trick. Filed away for a possible final rematch." },
          { round: "Round of 32 · 30 June", fixture: "Norway 2–1 Ivory Coast", note: "Nusa's curler, Haaland's late winner — Norway's first-ever World Cup knockout victory." },
          { round: "Round of 16 · 5 July", fixture: "Norway 2–1 Brazil", note: "THE shock of the tournament. Haaland scores twice in the last eleven minutes; five-time champions Brazil, out. Norway, into the quarterfinals for the first time in history." },
          { round: "Quarterfinal · TOMORROW, 11 July", fixture: "Norway vs England — Miami", note: "Haaland against the country of his birth, for a semifinal.", upcoming: true },
        ],
        status: `Alive and dreaming: quarterfinalists for the first time in history, playing England <strong>tomorrow</strong> in Miami. Haaland (7 goals) sits one behind Messi and Mbappé in the Golden Boot race.`,
      },
      history: `Norway's World Cup story is short, strange, and suddenly glorious. Before 2026 they had qualified only three times. In 1994 came the cult era of the "Drillos", a wilfully unglamorous team briefly ranked second in the world. In 1998 in France came THE night: Norway 2, Brazil 1 in Marseille, a last-minute penalty toppling the reigning champions. And then… 28 years of silence, while the country cruelly produced two of the world's best players — Ødegaard and Haaland — with no stage to put them on. The drought broke spectacularly: eight wins from eight in qualifying, including a 4–1 demolition of Italy at the San Siro. And now, in 2026, history rhymes: once again Norway has beaten Brazil at a World Cup, and once again a nation of 5.5 million is staying up all night. This time, for the first time ever, they're in the final eight.`,
      facts: [
        { q: "Brazil have never beaten Norway", a: "Five-time world champions Brazil have played Norway five times across four decades: three Norwegian wins (including World Cups 1998 and 2026) and two draws. The yellow giants simply cannot solve the polite people from the fjords." },
        { q: "'Your boys took a hell of a beating!'", a: "When Norway beat England in 1981, commentator Bjørge Lillelien lost his mind live on air: 'Lord Nelson! Winston Churchill! Maggie Thatcher — your boys took a hell of a beating!' If Norway win tomorrow, you will hear it quoted ten million times." },
        { q: "The name on the shirt", a: "Haaland's shirt reads 'Braut Haaland' — Braut is the family farm near Bryne. In Norway your name tells you which patch of land you belong to; even the world's most futuristic striker carries his farm on his back." },
        { q: "The coach who came back", a: "Ståle Solbakken was clinically dead for seven minutes after a cardiac arrest in training in 2001. Revived, fitted with a pacemaker, he turned to coaching. The man leading Norway's greatest fairy tale literally returned from the dead for it." },
        { q: "Only France beat them", a: "Norway's only defeat this tournament is 4–1 to France in the group. If both keep winning, the rematch would be the final itself. Margot's loyalties: pre-shredded." },
        { q: "Viking marketing", a: "Norway's away kit is all black with Viking patterns on the sleeves — the federation officially says it channels the country's 'Viking mentality'. The marketing department has never been so literal." },
      ],
    },

    /* ================= ENGLAND ================= */
    {
      id: "eng",
      name: "England",
      nickname: "The Three Lions — heraldry borrowed from England's medieval (and rather French) kings",
      accent: "var(--acc-eng)",
      flag: ["#f6f3ec", "#CE1124", "#f6f3ec"],
      coach: "Thomas Tuchel (yes — a German)",
      formation: "4-2-3-1 (a 3-2-5 in disguise)",
      formationKey: "4-2-3-1",
      styleKeywords: ["possession control", "set-piece menace", "knockout grit"],
      ratings: { possession: 9, pressing: 7, counterAttack: 6, physicality: 7, flair: 7, defensiveSolidity: 6 },
      philosophy: [
        `Imagine a country that invented a game, wrote its rulebook in a London pub in 1863, exported it to the entire planet — and then spent the next century watching everyone else get better at it. That is the exquisite agony of English football. The English gave the world le football the way the French gave the world cuisine, and every four years the whole nation convinces itself, half-joking and half-praying, that the trophy is finally "coming home." When you hear 70,000 England fans singing <em>It's coming home, football's coming home</em>, you're not hearing arrogance — you're hearing a love song about heartbreak, written in 1996, about thirty years of hurt that has since become sixty.`,
        `On the pitch in 2026, though, this England is something new. Under Thomas Tuchel — a German engineer of a coach, which for England is a bit like France hiring an English chef to run a three-star kitchen — the old anxious, hopeful chaos has been replaced by chess. England pass, and pass, and pass, strangling opponents with possession the way a python doesn't bother biting. The full-backs sneak into midfield when England have the ball, so a four-man defense quietly becomes a wall of five attackers up front — a magic trick performed in plain sight, ninety times a match. If Brazil play jazz, Tuchel's England play a Bach fugue: every voice knows exactly when to enter.`,
        `And yet the old English soul keeps bursting through the structure, which is what makes them irresistible right now. Against Mexico, in the deafening cauldron of the Azteca, they went down to ten men for the last forty minutes and simply refused to break — that's the other pillar of English football: rain-soaked, sleeves-rolled-up defiance, the belief that you can suffer your way to glory. Precision German architecture on top, stubborn English heart underneath. It has carried them to within three wins of only their second star.`,
      ],
      keyPlayers: [
        { name: "Jordan Pickford", pos: "GK", posLabel: "Goalkeeper", club: "Everton", age: 32, num: 1, why: "Loud, theatrical, spring-loaded, at his third World Cup. A penalty-shootout specialist — which, given England's tragic history with penalties, makes him a national security asset." },
        { name: "Marc Guéhi", pos: "CB", posLabel: "Center-back", club: "Manchester City", age: 25, why: "A calm, elegant defender whose club teammate is… Erling Haaland, the very striker he must handcuff in the quarterfinal. Awkward training-ground reunion incoming." },
        { name: "Declan Rice", pos: "CDM", posLabel: "Defensive midfield", club: "Arsenal", age: 27, num: 4, why: "The midfield bodyguard. Breaks up attacks and restarts England's passing machine — the player you only notice when he's missing, which is the highest compliment for the role." },
        { name: "Elliot Anderson", pos: "CDM", posLabel: "Midfield", club: "Nottingham Forest", age: 23, why: "The tournament's quiet revelation: a young passer who dictates England's rhythm alongside Rice — and the first Forest player at a World Cup for England in 36 years." },
        { name: "Jude Bellingham", pos: "CAM", posLabel: "Attacking midfield", club: "Real Madrid", age: 23, num: 10, why: "England's swaggering young prince, who plays with movie-star confidence. He scored twice in 98 seconds against Mexico — blink and you missed the whole show." },
        { name: "Bukayo Saka", pos: "RM", posLabel: "Right wing", club: "Arsenal", age: 24, num: 7, why: "A darting winger with a permanent smile, so beloved he's nicknamed 'Starboy'. His dribbling terrifies left-backs everywhere." },
        { name: "Marcus Rashford", pos: "LM", posLabel: "Left wing", club: "Barcelona (loan)", age: 28, num: 11, why: "Blazing-fast, reborn in Spain, scored in the opening win over Croatia — and a national hero off the pitch for his campaign feeding poor schoolchildren." },
        { name: "Harry Kane", pos: "ST", posLabel: "Striker · captain", club: "Bayern Munich", age: 32, num: 9, why: "The captain and goal machine — six goals this tournament, now England's greatest-ever World Cup scorer. When England need a goal, everyone in the stadium looks at the same man." },
      ],
      starPlayer: {
        name: "Harry Kane",
        story: `Harry Kane, 32, is England's captain and all-time record scorer — yet for most of his career he was football's unluckiest man, a collector of near-misses. Margot, here's the part you'll enjoy: France broke his heart. In the 2022 quarterfinal against Les Bleus, Kane scored one penalty, then blazed a second over the bar, and England went home. He left for Bayern Munich chasing silverware, finally won a league title, and arrived at this World Cup — his third as captain — like a man settling accounts with destiny. Six goals in five games: a double against Croatia, the header against Panama that carried him past Gary Lineker as England's greatest World Cup scorer, two late rescue goals against DR Congo (passing Pelé's World Cup tally), and the ice-cold penalty that sank Mexico in the Azteca. Tomorrow in Miami he duels Erling Haaland — the sport's two great goal machines, face to face, one match from a semifinal.`,
      },
      path: {
        group: "L — won it with 7 points",
        matches: [
          { round: "Group · 17 June", fixture: "England 4–2 Croatia", note: "Kane ×2, Bellingham, Rashford. A statement." },
          { round: "Group · 23 June", fixture: "England 0–0 Ghana", note: "72% possession, 19 shots, zero goals. The most England scoreline imaginable." },
          { round: "Group · 27 June", fixture: "England 2–0 Panama", note: "Kane's header makes him England's all-time World Cup record scorer, passing Gary Lineker." },
          { round: "Round of 32 · 1 July", fixture: "England 2–1 DR Congo", note: "A scare! Stunned in the 7th minute, rescued by Kane twice late — passing Pelé's World Cup tally with the winner." },
          { round: "Round of 16 · 5 July", fixture: "England 3–2 Mexico", note: "An instant classic at the Azteca: Bellingham twice in 98 seconds, a Kane penalty, a red card, a thunderstorm delay, and 40 minutes of ten-man defiance." },
          { round: "Quarterfinal · TOMORROW, 11 July", fixture: "Norway vs England — Miami", note: "Kane (6 goals) vs Haaland (7). The two great goal machines of the age, face to face.", upcoming: true },
        ],
        status: `Alive — they face Norway <strong>tomorrow night</strong> in Miami (11 p.m. in France). Billed everywhere as Kane vs Haaland. Winner reaches the semifinal against Argentina or Switzerland.`,
      },
      history: `England's World Cup story is a one-act triumph followed by sixty years of beautiful suffering. They invented the modern game, then loftily refused to enter the first World Cups at all. When they finally won, in 1966 at Wembley, Geoff Hurst scored the only hat-trick ever in a final. And then… nothing. Decades of operatic heartbreak: Maradona's 'Hand of God' in 1986, Gascoigne's tears in 1990, a penalty-shootout curse so reliable it became a national punchline. The near-misses piled up — a 2018 semifinal, the Euro 2020 final lost on penalties at Wembley itself, the 2022 quarterfinal against France (Kane's missed penalty — sorry to bring it up, Margot, but you were on the right side of that one), another lost Euro final in 2024. Which is why this 2026 run, engineered by a German coach of all people, has an entire nation holding its breath and trying very hard not to jinx it.`,
      facts: [
        { q: "The lions are… French?", a: "The three lions on England's badge come from the royal arms of the Plantagenets — like Richard the Lionheart, a king of England who spoke French and lived mostly in Aquitaine. England's proudest symbol is basically Norman heraldry. You're welcome." },
        { q: "A love song about losing", a: "England's unofficial anthem, 'Three Lions (Football's Coming Home)', is a 1996 pop song that celebrates LOSING — 'thirty years of hurt never stopped me dreaming.' The hurt is now at sixty years, and they still sing it with total sincerity." },
        { q: "The German taboo", a: "England hired Thomas Tuchel — a German — to end six decades of failure, roughly equivalent to France recruiting an English sommelier. It appears to be working, which the English find both thrilling and faintly embarrassing." },
        { q: "One star", a: "England's shirt carries a single gold star for 1966, with 'Happy and Glorious' stitched inside the collar. One star. France, of course, has two. Just saying." },
        { q: "Sweet Caroline??", a: "England fans have adopted Neil Diamond's 'Sweet Caroline' — an American crooner's 1969 ballad — as their victory song, bellowed by tens of thousands in American stadiums. Nobody can fully explain why. 'BAH BAH BAAAH!'" },
        { q: "The Haaland problem", a: "Norway's Haaland plays his club football at Manchester City alongside England defenders John Stones and Marc Guéhi — the very men assigned to stop him tomorrow. Football is a very small village." },
      ],
    },

    /* ================= ARGENTINA ================= */
    {
      id: "arg",
      name: "Argentina",
      nickname: "La Albiceleste — the White-and-Sky-Blue, defending champions of the world",
      accent: "var(--acc-arg)",
      flag: ["#74ACDF", "#f6f3ec", "#74ACDF"],
      coach: "Lionel Scaloni",
      formation: "4-3-3 (with Messi exempt from geography)",
      formationKey: "4-3-3",
      styleKeywords: ["Messi free role", "midfield swarm", "late-game garra"],
      ratings: { possession: 7, pressing: 7, counterAttack: 8, physicality: 7, flair: 9, defensiveSolidity: 6 },
      philosophy: [
        `Imagine a jazz band where every musician is classically trained, but the whole point of the concert is the moment the old soloist steps forward and improvises. That is Argentina. The team runs, presses and tackles with almost military discipline for one reason: to win the ball and hand it to Lionel Messi, the greatest improviser the sport has ever produced. Argentines have a phrase for their footballing ideal — <em>la nuestra</em>, "our way": football played with cunning, touch and a little mischief, learned not in academies but in the <em>potrero</em>, the dusty neighborhood lot where you nutmeg your friend and then remind him about it for a decade. Even the dribble has its own word, the <em>gambeta</em>, borrowed from tango — a dancer's swerve of the hips.`,
        `But don't mistake the artistry for softness. Argentina's other sacred word is <em>garra</em> — claw, grit. This team argues with referees, wastes time shamelessly, and treats every throw-in like a courtroom battle. Their goalkeeper, Emiliano "Dibu" Martínez, is the pantomime villain of world football: at penalty shootouts he chats with opposing kickers, dances on his line, gets into heads like a poker player. To the French this may ring a bell — it was Dibu's psychological warfare that broke French hearts in the 2022 final. Argentines see no contradiction between beauty and dark arts; to them football is like the asado, the great open-fire barbecue: unfussy, communal, cooked slowly, with total conviction that theirs is the best in the world.`,
        `What makes 2026 special is the ending being written in real time. Messi is 39, playing his record sixth World Cup, and every match may be the last time humanity watches him do this. The squad plays like sons protecting their father's legacy — twice this tournament they've stared at elimination and twice clawed back in the final minutes, as if collectively refusing to let the story end. When 70,000 Argentines sing <em>Muchachos</em> — a pop song rewritten by fans about Maradona watching from heaven and Messi's last dance — even neutrals get chills. You're not watching a team; you're watching a country's love letter.`,
      ],
      keyPlayers: [
        { name: "Emiliano 'Dibu' Martínez", pos: "GK", posLabel: "Goalkeeper", club: "Aston Villa", age: 33, num: 23, why: "The goalkeeper France loves to hate: a penalty-shootout showman who dances, trash-talks and saves everything. Behind the theatrics, one of the best shot-stoppers alive." },
        { name: "Cristian 'Cuti' Romero", pos: "CB", posLabel: "Center-back", club: "Tottenham", age: 28, num: 13, why: "Tackles like it's personal, every single time. His headed goal against Egypt started the great comeback. Pure garra." },
        { name: "Rodrigo De Paul", pos: "CM", posLabel: "Midfield", club: "Inter Miami", age: 32, num: 7, why: "Universally known as Messi's bodyguard — he followed him to Miami and follows him on the pitch, covering ten kilometers a game so the master never has to jog." },
        { name: "Enzo Fernández", pos: "CM", posLabel: "Midfield", club: "Chelsea", age: 25, num: 24, why: "The elegant metronome, best young player of the 2022 World Cup — and the hero of this one, scoring the stoppage-time winner against Egypt that saved the tournament." },
        { name: "Alexis Mac Allister", pos: "CM", posLabel: "Midfield", club: "Liverpool", age: 27, num: 20, why: "A red-headed Argentine with an Irish surname and the calmest brain on the pitch. He knits everything together." },
        { name: "Lionel Messi", pos: "RW", posLabel: "Free role · captain", club: "Inter Miami", age: 39, num: 10, why: "The greatest player in history, at his sixth and final World Cup. Eight goals — level with Mbappé at the top of the Golden Boot race — and newly the World Cup's all-time top scorer. Watch while you can." },
        { name: "Julián Álvarez", pos: "ST", posLabel: "Striker", club: "Atlético Madrid", age: 26, num: 9, why: "'La Araña' — the Spider — because he seems to have eight legs when he presses. Tireless, humble and lethal: he does Messi's running so Messi doesn't have to." },
        { name: "Lautaro Martínez", pos: "ST", posLabel: "Striker (rotation)", club: "Inter Milan", age: 28, num: 22, bench: true, why: "'El Toro' — the Bull. Inter Milan's captain finally scored his first World Cup goal this tournament, against Jordan, after years of near-misses." },
      ],
      starPlayer: {
        name: "Lionel Messi",
        story: `Once upon a time, a tiny boy from Rosario needed nightly hormone injections just to grow — his family couldn't afford them, so at 13 he crossed an ocean to Barcelona, where a club official sketched his first contract on a paper napkin. He became, by nearly universal agreement, the greatest footballer who ever lived: a small, left-footed magician who runs with the ball as if it were tied to his shoelaces. For years his own country held its love back, because he wasn't Maradona and hadn't won them anything. Then came the redemption arc: the 2021 Copa América, and finally the 2022 World Cup — where he beat France in perhaps the greatest final ever played and wept lifting the trophy. Everyone assumed that was the ending. Instead, at 39, at his record sixth World Cup, he refuses to leave the stage: a hat-trick against Algeria to pass Klose as the World Cup's all-time scorer, eight goals in five games, and — after missing a penalty against Egypt with elimination looming — an equalizer minutes later, because of course. Argentines sing that Maradona watches him from heaven. On current evidence, so does everyone else.`,
      },
      path: {
        group: "J — won it with a perfect 9 points",
        matches: [
          { round: "Group · 16 June", fixture: "Argentina 3–0 Algeria", note: "A Messi hat-trick, equalling Klose's all-time World Cup record of 16 goals." },
          { round: "Group · 22 June", fixture: "Argentina 2–0 Austria", note: "Messi ×2, the second in the 95th minute — making him the World Cup's outright all-time top scorer." },
          { round: "Group · 27 June", fixture: "Argentina 3–1 Jordan", note: "A Lo Celso free-kick, Lautaro's first-ever World Cup goal, then Messi off the bench — a goal in his 7th straight World Cup match." },
          { round: "Round of 32 · 3 July", fixture: "Argentina 3–2 Cape Verde (a.e.t.)", note: "Two frights and an extra-time escape — a Cape Verde own goal in the 111th spared Argentina the biggest upset in World Cup history." },
          { round: "Round of 16 · 7 July", fixture: "Argentina 3–2 Egypt", note: "Down 2–0 with 23 minutes left, Messi missing a penalty… then Romero 79', Messi 83', Enzo Fernández 90+2'. Three goals in 13 minutes. The champions refuse to die." },
          { round: "Quarterfinal · TOMORROW, 11 July", fixture: "Argentina vs Switzerland — Kansas City", note: "The defending champions against the tournament's quiet outsiders.", upcoming: true },
        ],
        status: `Alive and terrifying — the defending champions play Switzerland <strong>tomorrow</strong> in Kansas City, chasing the first back-to-back titles since Brazil in 1962. And note: France — already through to the semifinals — lurk on the <em>other</em> side of the bracket. The 2022 rematch is only possible in the final.`,
      },
      history: `Argentina's World Cup story is a three-act opera. Act one, 1978: a first title at home amid a blizzard of ticker-tape. Act two, 1986: a squat genius named Diego Maradona wins it almost single-handedly, scoring twice against England in one quarterfinal — first punching the ball in with his fist (the 'Hand of God'), then slaloming past six Englishmen four minutes later for the official Goal of the Century. Act three took 36 agonizing years, through lost finals in 1990 and 2014, until Qatar 2022 — where Messi finally lifted the trophy after a delirious 3–3 final against France, decided on penalties despite a Mbappé hat-trick. Now they're trying to do what nobody has done in 64 years: win it twice in a row.`,
      facts: [
        { q: "France's great rival", a: "The 2022 final between these two (3–3, Argentina on penalties, despite Mbappé's hat-trick) is widely called the greatest football match ever played. If both keep winning, the rematch can only happen in the final, July 19." },
        { q: "The French connection", a: "Marseille alone employs three of these Argentines (keeper Rulli, defenders Balerdi and Medina), and left-back Tagliafico plays for Lyon. Ligue 1 is quietly everywhere in this squad." },
        { q: "Muchachos", a: "Argentine fans have an official tearjerker: 'Muchachos', a rewritten pop song about Maradona watching from heaven and Messi's last dance. Entire stadiums sing it; players regularly cry during it." },
        { q: "The mate ritual", a: "The players are inseparable from mate, a bitter herbal tea sipped from a gourd through a metal straw and passed around like communion. Argentina reportedly ships hundreds of kilos of the leaves to every World Cup." },
        { q: "The napkin contract", a: "Messi's first Barcelona contract was written on a paper napkin when he was 13. It sold at auction in 2024 for nearly one million dollars." },
        { q: "Street art on a shirt", a: "The away kit is covered in 'fileteado porteño' — the swirling gold-lined folk art of Buenos Aires shop signs and buses, a UNESCO-listed art form, now on a football shirt." },
      ],
    },

  ],

  quiz: {
    questions: [
      {
        q: "It's Saturday afternoon. In your ideal world, you are…",
        options: [
          { label: "At a museum, then a long lunch with strong opinions", teams: ["esp"] },
          { label: "Hiking somewhere cold, beautiful and slightly too quiet", teams: ["nor"] },
          { label: "At a big loud family dinner that ends in singing", teams: ["arg"] },
          { label: "At a pub quiz, taking it far too seriously", teams: ["eng"] },
        ],
      },
      {
        q: "Your working style, honestly?",
        options: [
          { label: "Plan everything. Control everything. Zero surprises.", teams: ["esp"] },
          { label: "Nothing until the deadline, then a burst of genius", teams: ["bel", "arg"] },
          { label: "Quiet efficiency — do less, win anyway", teams: ["fra"] },
          { label: "Grind, graft, never complain", teams: ["nor", "eng"] },
        ],
      },
      {
        q: "Pick a dessert.",
        options: [
          { label: "Crème brûlée — a classic, executed perfectly", teams: ["fra"] },
          { label: "A Belgian waffle with chocolate, obviously", teams: ["bel"] },
          { label: "Churros dipped in thick hot chocolate", teams: ["esp", "arg"] },
          { label: "Dessert? A cinnamon bun after the hike, maybe", teams: ["nor", "eng"] },
        ],
      },
      {
        q: "What do you value most in people?",
        options: [
          { label: "Style — how you do a thing matters as much as doing it", teams: ["esp", "fra"] },
          { label: "Passion — love loudly or go home", teams: ["arg"] },
          { label: "Humility — do the work, skip the fuss", teams: ["nor"] },
          { label: "Resilience — get up one more time than you fall", teams: ["eng", "bel"] },
        ],
      },
      {
        q: "And your relationship with hope?",
        options: [
          { label: "Hope is a strategy. Believe loudly, cry freely.", teams: ["arg"] },
          { label: "Cautious optimism — protect your heart, it's been hurt before", teams: ["bel", "eng"] },
          { label: "Quiet confidence. We've done the work.", teams: ["fra", "esp"] },
          { label: "We're just happy to be here! (…and then we win)", teams: ["nor"] },
        ],
      },
    ],
    results: {
      fra: `Bien sûr. You appreciate things done properly, without fuss — efficiency that looks like laziness and is actually mastery. You'll enjoy watching Mbappé run very fast while everyone else panics, and you already know all the words to La Marseillaise. Welcome home.`,
      bel: `You're drawn to the nearly-weres, the jazz soloists, the beautiful losers who might finally win. Belgium is football's great unfinished symphony, and you want to be there for the final movement. Bonus: their coach is French, so it barely counts as treason.`,
      esp: `You believe how you do a thing matters as much as doing it. Spain keeps the ball like family silver and plays chess with poets. Yes, they knocked France out of Euro 2024. Adopting them is spicy. You've always liked a little spice.`,
      nor: `You like underdogs, mountains, and quiet people who turn out to be devastating. Norway is the tournament's most huggable team: a nation of 5.5 million crying happy tears while a Norse god scores goals in the lotus position. Skål, Margot.`,
      eng: `You respect the grind: a team (and a country) that has suffered so operatically for so long that one trophy would heal a thousand pub arguments. 'It's coming home' is half joke, half prayer — and you've decided to believe it.`,
      arg: `You lead with your heart. Argentina is football as religion — Messi's last dance, a country that sings for 90 minutes straight, joy and despair in the same breath. If you're going to fall in love with this sport, fall all the way.`,
    },
  },
};
