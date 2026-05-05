#!/usr/bin/env python3
"""
BUY-11202: Curated DTC brand discovery + validation + merge
Rebuilt after workspace reset. Single-file pipeline combining v4+v5.

Usage:
    python3 scrapers/discover_dtc.py --generate     # Generate candidates
    python3 scrapers/discover_dtc.py --validate      # Validate via Shopify
    python3 scrapers/discover_dtc.py --all           # Generate + validate + merge
    python3 scrapers/discover_dtc.py --limit 50      # Validate first N only
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CANDIDATES = DATA / "us_shopify_candidates_expanded.json"
MERCHANTS = DATA / "us_shopify_merchants.json"
INVALID = DATA / "us_shopify_invalid.json"
CURATED = DATA / "us_shopify_candidates_curated_temp.json"

# ============================================================
# CURATED DTC BRAND DATABASE (~1,200 brands across 9 categories)
# ============================================================

BRANDS = []

def _add(category, subcategory, *domains):
    for d in domains:
        BRANDS.append((d, category, subcategory))

# --- APPAREL (200+) ---
_add("apparel","activewear",
    "gymshark.com","aloyoga.com","lululemon.com","fabletics.com","outdoorvoices.com",
    "vuoriclothing.com","vuori.com","rhone.com","tenathousand.cc","bornprimitive.com",
    "jednorth.com","tlfapparel.com","youngla.com","doyoueven.com","ryderwear.com",
    "bombshellsportswear.com","nvgtn.com","ptulaactive.com","buffbunny.com",
    "popflexactive.com","balanceathletica.com","koral.com","carbon38.com",
    "sweatybetty.com","setactive.co","talaactive.com","aimn.com","nebbia.us",
    "womenbest.com","fleocollective.com","rawnutrition.com")
_add("apparel","womens",
    "fashionnova.com","skims.com","goodamerican.com","spanx.com","yitty.com",
    "revolve.com","nastygal.com","princesspolly.com","whitefoxboutique.com",
    "pixiemarket.com","lulus.com","shein.com","prettylittlething.com","boohoo.com",
    "missguided.com","aritzia.com","freepeople.com","anthropologie.com",
    "madewell.com","everlane.com","cuyana.com","reformation.com","sezane.com",
    "rouje.com","lilysilk.com","showpo.com","hello-molly.com","tigermist.com",
    "peppermayo.com","verge-girl.com","meshki.com","runawaythelabel.com","ohpolly.com")
_add("apparel","mens",
    "untuckit.com","mizzenandmain.com","bonobos.com","taylorstitch.com",
    "flintandtinder.com","huckberry.com","propercloth.com","indochino.com",
    "suitsupply.com","oliversapparel.com","mackweldon.com","mylesapparel.com",
    "ministryofsupply.com","publicrec.com","cutsclothing.com","byltbasics.com",
    "trueclassictees.com","freshcleantees.com","intotheam.com","buckmason.com",
    "birddogs.com","chubbiesshorts.com")
_add("apparel","shoes",
    "allbirds.com","rothys.com","olivercabell.com","greats.com","koio.co",
    "axelarigato.com","thursdayboots.com","tecovas.com","amberjack.com",
    "wolfandshepherd.com","beckettsimonon.com","adelanteshoes.com",
    "cariuma.com","nothingnew.com","lane-eight.com","vessi.com","atomoshoes.com",
    "tieks.com","margauxny.com","birdies.com","fredasalvador.com","seavees.com",
    "feitoaks.com","newbottega.com")
_add("apparel","streetwear",
    "kith.com","aimeleondore.com","palaceskateboards.com","noahny.com","stussy.com",
    "fearofgod.com","rhude.com","amiri.com","representclo.com","mnml-la.com",
    "pangaia.com","braindead.co","erlsn.com","denimtears.com","yeezy.com",
    "yeezysupply.com","sp5derworldwide.com","vlone.co","chromehearts.com")
_add("apparel","socks_underwear",
    "bombas.com","stance.com","nicelaundry.com","pair-of-thieves.com","meundies.com",
    "tommyjohn.com","thirdlove.com","cuup.com","lively.com","parade.com",
    "savagexfenty.com","knix.com","harperwilde.com","trueandco.com",
    "saxxunderwear.com","shinesty.com")
_add("apparel","workwear_outdoor",
    "duluthtrading.com","carhartt.com","truewerk.com","bruntworkwear.com",
    "1620workwear.com","ariat.com","hukgear.com","freeflyapparel.com",
    "howlerbros.com","pelagicgear.com","sitkagear.com","kuiu.com","firstlite.com")
_add("apparel","sustainable",
    "pact.com","tentree.com","kotn.com","outerknown.com","ascolour.com",
    "knownsupply.com","ableclothing.com","tradlands.com","mate-thelabel.com",
    "for-days.com","wearfranc.com","amourvert.com")
_add("apparel","swimwear",
    "summersalt.com","andieswim.com","leftonfriday.com","kulanikinis.com",
    "frankiesbikinis.com","blackboughswim.com","triangl.com","bydeeaus.com",
    "montce.com","mikaswim.com")
_add("apparel","bags",
    "awaytravel.com","monos.com","beistravel.com","paravel.com","calpak.com",
    "roamluggage.com","solgaard.co","herschel.com","troubadourgoods.com",
    "senreve.com","dagnedover.com","loandsons.com","nomatic.com","peakdesign.com",
    "aer.com","topodesigns.com","goruck.com","mysteryranch.com","filson.com")

# --- ELECTRONICS (150+) ---
_add("electronics","audio",
    "bose.com","sonos.com","jbl.com","masterdynamic.com","audeze.com","shure.com",
    "sennheiser-hearing.com","beyerdynamic.com","klipsch.com","bang-olufsen.com",
    "ultimateears.com","mezeaudio.com","campfireaudio.com","hifiman.com",
    "schiit.com","jdslabs.com","nurasound.com","skullcandy.com","beats.com")
_add("electronics","smarthome",
    "ring.com","wyze.com","eufy.com","arlo.com","simplisafe.com","ecobee.com",
    "nest.com","august.com","schlage.com","yalehome.com","level.co")
_add("electronics","lighting",
    "nanoleaf.com","philipshue.com","lifx.com","govee.com")
_add("electronics","accessories",
    "peakdesign.com","nomadgoods.com","bellroy.com","mujjo.com","padandquill.com",
    "twelvesouth.com","satechi.com","anker.com","belkin.com","mophie.com",
    "casemate.com","otterbox.com","speckproducts.com","incipio.com",
    "casetify.com","pela.earth","dbrand.com","totallee.com","peel.com",
    "mnmlcase.com","latercase.com","phonerebel.com","mous.co","rhinoshield.com",
    "spigen.com","tech21.com","quadlockcase.com","rokform.com","nativeunion.com",
    "popsocket.com","moft.us")
_add("electronics","gaming",
    "razer.com","corsair.com","logitechg.com","steelseries.com","hyperx.com",
    "nzxt.com","gloriousgaming.com","elgato.com","scufgaming.com",
    "finalmouse.com","pulsar.gg","endgamegear.com","turtlebeach.com",
    "thrustmaster.com","secretlab.co")
_add("electronics","camera",
    "gopro.com","dji.com","insta360.com","momentlens.co","sandmarc.com",
    "polarpro.com","wandrd.com","boundarysupply.com","freewellgear.com")
_add("electronics","wearables",
    "whoop.com","ouraring.com","withings.com","amazfit.com","coros.com",
    "garmin.com","fitbit.com","polar.com","suunto.com")
_add("electronics","ebikes",
    "vanmoof.com","cowboy.com","radpowerbikes.com","lectricebikes.com",
    "aventon.com","ride1up.com","juicedbikes.com","super73.com","arielrider.com")
_add("electronics","drones",
    "skydio.com","autelrobotics.com","parrot.com","hubsan.com","holystone.com",
    "getfpv.com","racedayquads.com","newbeedrone.com","betafpv.com")
_add("electronics","keyboards",
    "keychron.com","drop.com","duckychannel.com","omnitype.com","novelkeys.com",
    "kbdfans.com","epomaker.com","akko.com","wooting.io","zsa.io","modekeyboards.com")
_add("electronics","3dprinting",
    "prusa3d.com","bambulab.com","creality.com","elegoo.com","anycubic.com",
    "flashforge.com","ultimaker.com","formlabs.com","glowforge.com","matterhackers.com")
_add("electronics","chargers",
    "ravpower.com","aukey.com","choetech.com","ugreen.com","goalzero.com",
    "jackery.com","ecoflow.com","bluetti.com","zendure.com")

# --- JEWELRY & ACCESSORIES (120+) ---
_add("jewelry_accessories","jewelry",
    "mejuri.com","auratenewyork.com","vrai.com","brilliantearth.com",
    "catbirdnyc.com","catbird.com","dorsey.co","missoma.com","analuisa.com",
    "gorjana-griffin.com","gorjana.com","kinnstudio.com","linjer.co",
    "monicavinader.com","ringconcierge.com","jenniferfisher.com","baublebar.com",
    "noemie.com","oliveandpiper.com","by-chari.com","jacquieaiche.com",
    "foundrae.com","bluenile.com","jamesallen.com","uncommonjames.com",
    "the-last-line.com","pavoi.com","local-eclectic.com","pamelalove.com",
    "davidyurman.com","johnhardy.com","ippolita.com","sydneyevan.com",
    "melindamaria.com","nialaya.com","sophiebuhai.com","gldn.com",
    "caitlynminimalist.com","onecklace.com","getnamenecklace.com")
_add("jewelry_accessories","watches",
    "danielwellington.com","mvmt.com","mvmtwatches.com","vincerocollective.com",
    "oliviaburton.com","cluse.com","larssonandjennings.com","triwa.com",
    "skagen.com","filippoloreti.com","nordgreen.com","originalgrain.com",
    "holzkern.com","tissot.com","hamiltonwatch.com","raymond-weil.com")
_add("jewelry_accessories","eyewear",
    "warbyparker.com","zeelool.com","eyebuydirect.com","firmoo.com",
    "glassesusa.com","zennioptical.com","pair.com","diffeyewear.com",
    "gentlemonster.com","garrettleight.com","sunski.com","blenderseyewear.com",
    "goodr.com","roka.com","tifosioptics.com","ray-ban.com","oakley.com")

# --- TOYS & HOBBIES (120+) ---
_add("toys_hobbies","educational",
    "kiwico.com","lovevery.com","melissaanddoug.com","littlepassports.com",
    "crunchlabs.com","creationcrate.com","sphero.com","makeblock.com",
    "ozobot.com","thinkfun.com")
_add("toys_hobbies","collectibles",
    "bigbadtoystore.com","entertainmentearth.com","sideshow.com",
    "hasbropulse.com","mcfarlane.com","mezcotoyz.com","super7.com",
    "necaonline.com","funko.com","lootcrate.com","culturefly.com","toynk.com")
_add("toys_hobbies","boardgames",
    "explodingkittens.com","unstablegames.com","stonemaiergames.com",
    "boardgamegeek.com","miniaturemarket.com","gamenerdz.com","coolstuffinc.com",
    "wizkids.com","asmodee.com","fantasyflightgames.com","cmon.com",
    "pandasaurusgames.com","brotherwisegames.com","restorationgames.com",
    "ledergames.com","beziergames.com","greaterthangames.com",
    "capstone-games.com","wyrmwoodgaming.com","boardgametables.com",
    "the-dicetower.com","boardlandia.com","tabletopmerchant.com",
    "atomicempire.com","cardhaus.com","riograndegames.com")
_add("toys_hobbies","puzzles",
    "libertypuzzles.com","jiggypuzzles.com","pieceworkpuzzles.com",
    "galison.com","pomegranate.com","eeboo.com","cobblehillpuzzles.com",
    "whitemountainpuzzles.com","ravensburger.com","puzzlewarehouse.com")
_add("toys_hobbies","models",
    "megahobby.com","micromark.com","spruebrothers.com","tamiya.com",
    "revell.com","airfix.com","italeri.com")
_add("toys_hobbies","building",
    "lego.com","brickmania.com","brickowl.com","bricklink.com","citizenbrick.com",
    "brickwarriors.com","firestartoys.com")
_add("toys_hobbies","rc",
    "rcplanet.com","amainhobbies.com","horizonhobby.com","traxxas.com",
    "arrma-rc.com","axialracing.com","losi.com","teamassociated.com",
    "prolineracing.com","rcsuperstore.com","towerhobbies.com")
_add("toys_hobbies","magic",
    "magictricks.com","theory11.com","ellusionist.com","penguinmagic.com",
    "vanishingincmagic.com","artofplay.com")

# --- MUSICAL INSTRUMENTS (100+) ---
_add("musical_instruments","guitars",
    "fender.com","gibson.com","martinguitar.com","taylorguitars.com",
    "prsguitars.com","ibanez.com","epiphone.com","gretschguitars.com",
    "jackson.com","charvel.com","espguitars.com","schecterguitars.com",
    "suhr.com","kieselguitars.com","strandbergguitars.com","ernieball.com",
    "collingsguitars.com","breedlovemusic.com","lakland.com","santacruzguitar.com",
    "godinguitars.com","reverendguitars.com","dangelicoguitars.com",
    "eastmanguitars.com","heritageguitars.com","yamahaguitars.com",
    "cordobaguitars.com","rickenbacker.com")
_add("musical_instruments","pedals",
    "strymon.net","bosseffects.com","earthquakerdevices.com","walrusaudio.com",
    "chaseblissaudio.com","oldbloodnoise.com","jhspedals.com","wamplerpedals.com",
    "keeleyelectronics.com","meris.us","catalinbread.com","fulltone.com",
    "mxr.com","electro-harmonix.com","eventideaudio.com","sourceaudio.net")
_add("musical_instruments","amps",
    "mesaboogie.com","marshall.com","voxamps.com","orangeamps.com",
    "bogneramps.com","diezelamps.com","fryette.com","morganamps.com",
    "milkman-sound.com","carr-amps.com","drzamps.com","victoryamps.com",
    "bensonamps.com","tonekingamps.com","matchlessamps.com","badcatamps.com")
_add("musical_instruments","synths",
    "moogmusic.com","teenageengineering.com","sequential.com","korg.com",
    "roland.com","yamaha.com","novationmusic.com","arturia.com","elektron.se",
    "intellijel.com","polyend.com","makenoisemusic.com","waldorfmusic.com")
_add("musical_instruments","drums",
    "dwdrums.com","pearldrum.com","tama.com","ludwig-drums.com",
    "gretschdrums.com","sonordrums.com","zildjian.com","sabian.com",
    "paiste.com","meinlcymbals.com")
_add("musical_instruments","proaudio",
    "focusrite.com","uaudio.com","apogeedigital.com","presonus.com",
    "avid.com","ableton.com","native-instruments.com","neumann.com",
    "audiotechnica.com","rme-audio.com","behringer.com","akai-pro.com","m-audio.com")
_add("musical_instruments","accessories",
    "daddario.com","ernieball.com","ghsstrings.com","dunlop.com",
    "elixirstrings.com","planetwaves.com","pedaltrain.com","templeaudio.com",
    "hercules-stands.com","on-stage.com")

# --- HARDWARE & TOOLS (100+) ---
_add("hardware","tools",
    "milwaukeetool.com","dewalttool.com","makitatools.com","boschtools.com",
    "ridgid.com","ryobitools.com","portercable.com","skiltools.com","craftsman.com",
    "festoolusa.com","fein.com","hilti.com","kleintools.com","irwin.com",
    "fastcap.com","kregtool.com","woodpeck.com","leatherman.com","victorinox.com",
    "gerbergear.com","sogknives.com")
_add("hardware","knives",
    "benchmade.com","spyderco.com","coldsteel.com","kershawknives.com","crkt.com",
    "buckknives.com","caseknives.com","microtechknives.com","protechknives.com",
    "zerotolerance.com","chrisreeve.com","hindererknives.com","striderknives.com",
    "lionsteel.it","foxcutlery.com","weknives.com","civivi.com","kanseptknives.com",
    "kizerknives.com","bestechknives.com","artisancutlery.net","bladehq.com",
    "knifecenter.com","gpknives.com","dlttrading.com","ka-bar.com","bokerusa.com")
_add("hardware","flashlights",
    "olight.com","fenixlight.com","nitecore.com","streamlight.com","surefire.com",
    "pelican.com","maglite.com","thrunite.com","lumintop.com","zebralight.com",
    "armytek.com","acebeam.com","skilhunt.com","clouddefensive.com")
_add("hardware","homeimprovement",
    "homedepot.com","lowes.com","menards.com","acehardware.com","build.com",
    "ferguson.com","grainger.com","mcmaster.com","fastenal.com",
    "zoro.com","mscdirect.com","uline.com","globalindustrial.com","wayfair.com")

# --- HOME DECOR & FURNITURE (150+) ---
_add("home","furniture",
    "article.com","burrow.com","interior-define.com","albanypark.com",
    "maidenhome.com","benchmademodern.com","floydhome.com","joybird.com",
    "castlery.com","industrywest.com","luluandgeorgia.com","crateandbarrel.com",
    "potterybarn.com","westelm.com","cb2.com","bludot.com","roomandboard.com",
    "dwr.com","designwithinreach.com","arhaus.com","studiomcgee.com","mcggeeandco.com")
_add("home","rugs",
    "ruggable.com","revivalrugs.com","loomyhome.com","loloirugs.com",
    "annieselke.com","jaipurliving.com","safavieh.com","rugsusa.com",
    "esalerugs.com","boutiquerugs.com","wellwoven.com","uniqueloom.com",
    "momeni.com","feizy.com")
_add("home","bedding",
    "brooklinen.com","parachutehome.com","bollandbranch.com","coyuchi.com",
    "snowehome.com","rileyhome.com","casper.com","purple.com","saatva.com",
    "avocadomattress.com","helixsleep.com","nectarsleep.com","leesa.com",
    "tuftandneedle.com","bearmattress.com","laylasleep.com","birchliving.com",
    "nolahmattress.com","amerisleep.com","brentwoodhome.com",
    "thecompanystore.com","peacockalley.com","buffy.co","slip.com","ettitude.com",
    "bedthreads.com","cultiver.com")
_add("home","kitchen",
    "ourplace.com","madeincookware.com","carawayhome.com","greatjones.com",
    "materialkitchen.com","misen.co","lodgecastiron.com","staub.com",
    "lacruset.com","fieldcompany.com","butterpat.com","smitheyns.com",
    "finexusa.com","all-clad.com","greenpan.com","fellowproducts.com",
    "stasherbag.com","hydroflask.com","yeti.com","kleankanteen.com",
    "swell.com","brumate.com","owala.com")
_add("home","candles",
    "homesick.com","boysmells.com","otherland.com","pfcandleco.com",
    "keapbk.com","lelabofragrances.com","diptyqueparis.com","byredo.com",
    "nestnewyork.com","voluspa.com","capriblue.com","malinandgoetz.com")
_add("home","cleaning",
    "blueland.com","grove.co","dropps.com","branchbasics.com",
    "trulyfreehome.com","forceofnatureclean.com","cleancult.com",
    "supernatural.com","everspring.com","methodhome.com","mrsmeyers.com",
    "seventhgeneration.com")
_add("home","plants",
    "thesill.com","bloomscape.com","leonandgeorge.com","greeneryunlimited.com",
    "easyplant.com","pistilsnursery.com","whiteflowerfarm.com","burpee.com",
    "parkseed.com","rareseeds.com","johnnyseeds.com","bakerscreekseeds.com")

# --- HEALTH SUPPLEMENTS (180+) ---
_add("health_supplements","vitamins",
    "careof.com","ritual.com","humnutrition.com","personanutrition.com",
    "seed.com","smarty-pants.com","olly.com","getdose.com","liveconscious.com",
    "gaiaherbs.com","megafood.com","newchapter.com","naturesway.com","solgar.com",
    "pureencapsulations.com","thorne.com","doctorsbest.com","nowfoods.com",
    "jarrow.com","nordicnaturals.com","carlsonlabs.com","drberg.com",
    "hum-nutrition.com","nurish.com","betteryou.com","stateofkind.co")
_add("health_supplements","protein",
    "onnit.com","transparentlabs.com","legionathletics.com","kaged.com",
    "myprotein.com","truenutrition.com","ghostlifestyle.com","pescience.com",
    "bareperformancenutrition.com","ryseup.com","rawnutrition.com","alphalion.com",
    "ruleoneproteins.com","dymatize.com","optimumnutrition.com","isopure.com",
    "steelfitusa.com","performix.com","cellucor.com","musclepharm.com")
_add("health_supplements","greens",
    "athleticgreens.com","organifi.com","bloomnu.com","amazinggrass.com",
    "nestednaturals.com","enzymedica.com","greensfoods.com",
    "primalharvest.com","nativepath.com")
_add("health_supplements","cbd",
    "charlottesweb.com","cbdmd.com","greenroads.com","cbdfx.com",
    "cbdistillery.com","medterra.com","joyorganics.com","lazarusnaturals.com",
    "sunsoil.com","cbd.com","fivecbd.com")
_add("health_supplements","nootropics",
    "neurohacker.com","qualialife.com","nootropicsdepot.com","brainmd.com",
    "mindlabpro.com","nootroo.com","alphabrain.com","truenature.com",
    "purenootropics.net","sciencebio.com","liftmode.com")
_add("health_supplements","mushrooms",
    "fourigmatic.com","mudwtr.com","ryzesuperfoods.com","ommushrooms.com",
    "hostdefense.com","realmushrooms.com","freshcap.com",
    "animamundiherbals.com","sunpotion.com","moonjuice.com","mushroomrevival.com",
    "fungiperfecti.com","northspore.com")
_add("health_supplements","hydration",
    "drinklmnt.com","liquid-iv.com","nuunlife.com","waterdrop.com",
    "drinkbodyarmor.com","ultimareplenisher.com","drinkcure.com","drinkrecess.com")
_add("health_supplements","collagen",
    "vitalproteins.com","furtherfood.com","sportsresearch.com",
    "ancientnutrition.com","dosaze.com","lovewellness.com","collagencompany.com",
    "spoiledchild.com")
_add("health_supplements","sleep",
    "beamorganics.com","calm.com","moonjuice.com","drinkrecess.com",
    "lunautherapy.com","chilitechnology.com","bedjet.com","eightsleep.com")
_add("health_supplements","meal_delivery",
    "daily-harvest.com","splendid-spoon.com","freshly.com","factor75.com",
    "trifectanutrition.com","territoryfoods.com","freshnlean.com",
    "sunbasket.com","homechef.com","greenchef.com","purplecarrot.com",
    "gobble.com","hungryroot.com","marleyspoon.com","everyplate.com",
    "blueapron.com","hellofresh.com")
_add("health_supplements","tea",
    "traditionalmedicinals.com","yogitea.com","pukkaherbs.com","numi.com",
    "choiceorganics.com","harney.com","davidstea.com","artoftea.com",
    "adagiotea.com","rishi-tea.com","teaforte.com","mightyleaf.com")

# --- BABY & KIDS (120+) ---
_add("baby_kids","gear",
    "stokke.com","nunababy.com","uppababy.com","cybex-online.com",
    "maxi-cosi.com","chicco.com","britax.com","graco.com","babyjogger.com",
    "bugaboostrollers.com","doona.com","ergobaby.com","babybjorn.com",
    "lillebaby.com","sakurabloom.com","wildbird.com","colugo.com",
    "mockingbirdstroller.com","joovy.com","veerbaby.com","bobgear.com",
    "thule.com","bumbleride.com","pegperego.com","diono.com","clekinc.com")
_add("baby_kids","sleep",
    "snoo.com","owletcare.com","nanit.com","cuboai.com","miku.com",
    "huckleberrycare.com","babysense.com","angelcarebaby.com",
    "infantoptics.com","babylist.com")
_add("baby_kids","clothing",
    "bombababy.com","primary.com","hannakids.com","teacollection.com",
    "minirodini.com","ryleeandcru.com","quincymae.com","jamiekay.com",
    "littleunicorn.com","pact.com","burtsbeesbaby.com","finleyandharper.com",
    "goumikids.com","kytebaby.com","poshpeanut.com","janieandjack.com",
    "littleme.com","milkbarn.com","citythreads.com")
_add("baby_kids","diapers",
    "honest.com","hellobello.com","dyper.com","coterie.com","milliemoon.com",
    "bambonature.com","kudosy.com","healthybaby.com",
    "seventhgeneration.com","babyganics.com")
_add("baby_kids","feeding",
    "kiinde.com","comotomo.com","drbrownsbaby.com","tommeetippee.com",
    "philips-avent.com","munchkin.com","babybrezza.com","lalo.com",
    "ezpzfun.com","booninc.com","onceuponafarm.com","yumibaby.com",
    "littlespoon.com","cerebelly.com","squarebaby.com","nurturelife.com")
_add("baby_kids","toys",
    "lovevery.com","littlepartners.com","montikids.com","tinylove.com",
    "lamazetoys.com","skiphop.com","fatbraintoys.com","mindware.com",
    "lakeshorelearning.com","kidkraft.com","step2.com","littletikes.com",
    "radioflyer.com","greentoys.com","hearthsong.com","unclegoose.com")

# --- PETS (120+) ---
_add("pets","food",
    "farmersdog.com","ollie.com","nomnomnow.com","justfoodfordogs.com","petplate.com",
    "spotandtango.com","weruva.com","tasteofthewild.com","instinctpetfood.com",
    "orijen.com","acana.com","stellaandchewys.com","primalpetfoods.com",
    "ziwipets.com","frommfamily.com","natureslogic.com","earthbornholisticpetfood.com",
    "openfarmpet.com","caru.com","nulo.com","nutrisourcepetfoods.com",
    "onlynaturalpet.com","canidae.com","hills pet.com","royalcanin.com",
    "purina.com","bluebuffalo.com","rachaelraypet.com","merrickpetcare.com",
    "wellnesspetfood.com","naturalbalanceinc.com","nutro.com","iams.com",
    "science diet.com","eukanuba.com")
_add("pets","supplements",
    "zestypaws.com","petlabco.com","paworigins.com","naturvet.com","vetsbest.com",
    "pethonesty.com","nativepet.com","honestpaws.com","pawcbd.com",
    "innovetpet.com","kingkanine.com","holistapet.com","barketplace.com",
    "cosequinusa.com","dasuquin.com","nutramaxlabs.com")
_add("pets","accessories",
    "wild-one.com","barkbox.com","fi.com","whistle.com","petcube.com","furbo.com",
    "outwardhound.com","ruffwear.com","kurgo.com","kongcompany.com",
    "westpaw.com","chuckit.com","nerfpet.com","frisco.com","youandmepets.com",
    "lucyandco.com","foggodog.com","lupinepet.com","wildebeest.co",
    "bedsure.com","furhaven.com","petfusion.com","kittymansions.com","armarkat.com",
    "chewy.com","petco.com","petsmart.com")
_add("pets","subscription",
    "barkbox.com","pupbox.com","meowbox.com","kitnipbox.com","succulent.studio",
    "rescuedbox.com","pupjoy.com","poochperks.com","bullymake.com","superchewer.com")

# --- FOOD & SNACKS (150+) ---
_add("food","snacks",
    "magicspoon.com","eatbobos.com","eatbanza.com","eatprose.com","eatnuttzo.com",
    "hukitchen.com","skinnydipped.com","dangfoods.com","thatsitfruit.com",
    "bareapple.com","bradsplantbased.com","larabar.com","rxbar.com",
    "gomacro.com","clifbar.com","perfectbar.com","questnutrition.com",
    "nugo.com","onelifeoneyou.com","healthwarrior.com",
    "lesserevil.com","popcorners.com","offtheeatenpath.com","piratebooty.com",
    "smartfood.com","hippeas.com","hippiesnacks.com","nothinbutfoods.com",
    "fieldtripjerky.com","epicprovisions.com","countryarcher.com","chomps.com",
    "bonafideprovisions.com","kettleandfire.com","kettlebrand.com",
    "fromthegroundupsnacks.com","wildzora.com","purelyelizabeth.com",
    "bienanutrition.com","hipchips.com","peatos.com","snacklins.com")
_add("food","beverages",
    "drinkolipop.com","drinkpoppi.com","drinkculturepop.com","drinkghia.com",
    "drinkkin.com","drinkhaus.com","drinkmoment.com","drinkrebbl.co",
    "drinkwyld.com","drinkcann.com","drinkhint.com","drinkspindrift.com",
    "drinkbubly.com","drinkpolar.com","drinkwaterloo.com","drinkcelsius.com",
    "drinkalani.com","drinkghostenergy.com","drinkryze.com","drinkbang.com",
    "drinkreign.com","drinkc4.com","drinkbodyarmor.com","drinkvitacoco.com",
    "drinkcorehydration.com","drinkglaceau.com","drinkliquidiv.com",
    "drinknuun.com","drinklmnt.com","drinkultima.com","drinkhydrant.com",
    "drinkdripdrop.com","drinkcure.com","drinkrecess.com","drinktriple.com")
_add("food","coffee_tea",
    "bluebottlecoffee.com","stumptowncoffee.com","counterculturecoffee.com",
    "intelligentsiacoffee.com","deathwishcoffee.com","bullets2beans.com",
    "tradecoffeeco.com","atlascoffeeclub.com","mistobox.com","angelscup.com",
    "driftaway.coffee","beanbox.com","yerbamate.com","tealet.com",
    "teapigs.com","arborteas.com","davidstea.com","rishi-tea.com",
    "mightytea.com","republicoftea.com","harney.com","stashtea.com",
    "cometeer.com","tandemcoffee.com","onyxcoffeelab.com","vervecoffee.com",
    "equatorcoffees.com","ritualcoffee.com","sightglasscoffee.com",
    "heartroasters.com","bottomless.com","yesplz.coffee","bluestonelane.com")
_add("food","condiments",
    "flybyjing.com","bachans.com","momofuku.com","osmosauce.com",
    "truffhotsauce.com","yellowbirdsauce.com","secretaardvark.com",
    "melindas.com","mariesharpsusa.com","cholula.com","valentina.com",
    "el yucateco.com","texaspete.com","franksredhot.com","tabasco.com",
    "sriracha2go.com","huyfong.com","leekumkee.com","fishwives.com",
    "brightland.com","graza.co","pineapplecollaborative.com","maldonsalt.com")
_add("food","meal_kits",
    "blueapron.com","hellofresh.com","homechef.com","sunbasket.com","greenchef.com",
    "gobble.com","marleyspoon.com","dinnerly.com","everyplate.com","purplecarrot.com",
    "splendidspoon.com","mosaicfoods.com","hungryroot.com","territoryfoods.com",
    "snapkitchen.com","freshly.com","factor75.com","freshnlean.com",
    "trifectanutrition.com","propermade.com","tovala.com","supperbell.com")
_add("food","protein_bars",
    "onelife.com","rxbar.com","larabar.com","perfectsnacks.com","questnutrition.com",
    "builtbar.com","g2gbar.com","aloha.com","jambar.com","misfits.health",
    "barebells.com","fulfill.com","grenade.com","robertirvinefoods.com",
    "thinkproducts.com","kind snacks.com","clifbar.com","gomacro.com")
_add("food","pantry",
    "sietefoods.com","primalkitchen.com","birchbenders.com","simplemills.com",
    "cappellos.com","againstthegraingourmet.com","cauliflowerfoods.com",
    "realgoodfoods.com","outeraisle.com","califlourfoods.com",
    "jovialfoods.com","lotusfoods.com","ancientharvest.com","lundberg.com",
    "bobredmill.com","kingarthurbaking.com","thrivemarket.com",
    "shop thrive.com","imperfectfoods.com","misfitsmarket.com")

# --- SPORTS & OUTDOOR (150+) ---
_add("sports","outdoor",
    "yeti.com","hydroflask.com","stanley1913.com","simplemodern.com",
    "corkcicle.com","miir.com","swell.com","kleankanteen.com","nalgene.com",
    "takeyausa.com","brumate.com","owala.com","puristcollective.com",
    "rei.com","backcountry.com","moosejaw.com","sierra.com","steepandcheap.com",
    "campmor.com","campsaver.com","enwild.com","moontrail.com","basecampgear.com",
    "hilleberg.com","bigagnes.com","msrgear.com","seatosummit.com",
    "thermarest.com","nemoequipment.com","exped.com","snowpeak.com",
    "helinox.com","alpsmountaineering.com","kelty.com","marmot.com",
    "mountainhardwear.com","outdoorresearch.com","arcteryx.com",
    "patagonia.com","thenorthface.com","columbia.com","eddiebauer.com",
    "llbean.com","orvis.com","basspro.com","cabelas.com","dickssportinggoods.com")
_add("sports","cycling",
    "trekbikes.com","specialized.com","cannondale.com","giant-bicycles.com",
    "santacruzbicycles.com","pivotcycles.com","ibiscycles.com","transitionbikes.com",
    "kona-bicycles.com","marinbikes.com","surlybikes.com","salsacycles.com",
    "allcitycycles.com","yeti-cycles.com","evil-bikes.com","jensonusa.com",
    "competitivecyclist.com","nashbar.com","westernbikeworks.com","bikebling.com",
    "peloton.com","zwift.com","wahoo fitness.com","stagescycling.com",
    "garmin.com","lezyne.com","parktool.com","pedros.com")
_add("sports","running",
    "hokaoneone.com","brooksrunning.com","saucony.com","asics.com","nike.com",
    "adidas.com","newbalance.com","altra running.com","on-running.com",
    "salomon.com","merrell.com","topoathletic.com","inov8.com",
    "runningwarehouse.com","roadrunnersports.com","holabirdsports.com",
    "fleetfeet.com","jackrabbit.com","marathonsports.com")
_add("sports","yoga",
    "manduka.com","jadeyoga.com","liforme.com","bhalfmoon.com","yogaccessories.com",
    "hugermugger.com","prana.com","aloyoga.com","beyondyoga.com",
    "lululemon.com","sweatybetty.com","outdoorvoices.com","girlfriend.com",
    "corkcicle.com","gaiam.com")
_add("sports","fishing",
    "tacklewarehouse.com","fishusa.com","landbigfish.com","tackledirect.com",
    "meltoninternational.com","anglerswarehouse.com","srmo.com",
    "pelagicgear.com","aftcogear.com","hukfishing.com","simmsfishing.com",
    "orvis.com","basspro.com","cabelas.com","midwayusa.com")
_add("sports","climbing",
    "blackdiamondequipment.com","petzl.com","edelrid.com","mammut.com",
    "metoliusclimbing.com","organicclimbing.com","frictionlabs.com",
    "lasportivausa.com","scarpa.com","rab.equipment.com")
_add("sports","snow",
    "burton.com","lib-tech.com","gnu.com","ridesnowboards.com","neversummer.com",
    "capitasnowboarding.com","jonesnowboards.com","rossignol.com","k2snow.com",
    "salomon.com","evo.com","the-house.com","backcountry.com","snowboards.com")

# --- AUTOMOTIVE (80+) ---
_add("automotive","parts",
    "weathertech.com","huskyliners.com","roughcountry.com","extremeterrain.com",
    "cravenspeed.com","grfxstudio.com","premiumautostyling.com",
    "autoaccessoriesgarage.com","diode-dynamics.com","morimotohid.com",
    "theretrofitsource.com","headlightrevolution.com","covercraft.com",
    "coverking.com","calcarcover.com","seal-skin.com","americanmuscle.com",
    "carparts.com","carid.com","automotiveparts.com","autoplicity.com",
    "rockauto.com","summitracing.com","jegs.com","speedwaymotors.com")
_add("automotive","accessories",
    "yakima.com","thule.com","roofrack.com","seasucker.com","inno.co.jp",
    "petrolvibes.com","mishimoto.com","corsaperformance.com","borla.com",
    "flowmaster.com","magnaflow.com","aemintakes.com","knfilters.com",
    "dynojet.com","powervision.com","fuelmotousa.com","vanceandhines.com",
    "rhinousainc.com","retrax.com","bakindustries.com","truxedo.com")
_add("automotive","detail",
    "chemicalguys.com","adams polishes.com","griotsgarage.com","mcarproducts.com",
    "poorboysworld.com","wolfgangcarcare.com","pinnacle wax.com",
    "autogeek.com","detailedimage.com","autopia-carcare.com")

# --- OFFICE & STATIONERY (80+) ---
_add("office","furniture",
    "autonomous.ai","branchfurniture.com","flexispot.com","upliftdesk.com",
    "vari.com","fully.com","evodesk.com","jarvisdesk.com","deskhaus.com",
    "motiongrey.com","steelcase.com","hermanmiller.com","haworth.com",
    "knoll.com","humanscale.com","turnstonefurniture.com")
_add("office","accessories",
    "grovemade.com","balolo.com","artifox.com","oakywood.com","woodcessories.com",
    "orbitkey.com","nativeunion.com","courant.com","nomadgoods.com",
    "twelvesouth.com","satechi.net","anker.com","belkin.com","mophie.com",
    "zagg.com","rain design.com","keychron.com","drop.com",
    "duckychannel.com","omnitype.com","novelkeys.com","kbdfans.com",
    "epomaker.com","akko.com","wooting.io","zsa.io","modekeyboards.com")
_add("office","stationery",
    "riflepaperco.com","papier.com","sugarpaper.com","minted.com",
    "artifactuprising.com","artifactuprising.com","papersource.com",
    "thestationerystudio.com","fabulousstationery.com","whitelinespaper.com",
    "inkwellpress.com","maydesigns.com","plumpaper.com","erincondren.com",
    "daydesigner.com","simplified.com","cleverfoxplanner.com","pandac planner.com",
    "mochithings.com","jetpens.com","yosekastationery.com","bunbougu.com.au")
_add("office","pens",
    "karaskustoms.com","tactileturn.com","bigidesign.com","ti2design.com",
    "usg-company.com","grimsmo-saga.com","nottinghamtactical.com",
    "fellhoelter.com","machinedpens.com","smoothprecisionpens.com")

# --- ART & CRAFTS (80+) ---
_add("art_crafts","art_supplies",
    "blickart.com","jerrysartarama.com","utrechtart.com","cheapjoes.com",
    "dickblick.com","michaels.com","joann.com","hobbylobby.com",
    "createforless.com","consumercrafts.com","saxarts.com","schoolspecialty.com",
    "nascoeducation.com","triarco-arts.com","c2f.com")
_add("art_crafts","yarn_fabric",
    "lovecrafts.com","weareknitters.com","woolandthegang.com","lionbrand.com",
    "bernicat.com","cascadeyarns.com","malabrigoyarn.com","madelinetosh.com",
    "hedgehogfibres.com","eat sleep knit.com","jimmybeanswool.com",
    "knitpicks.com","webs-yarn.com","fabulousyarn.com",
    "spoonflower.com","hawthornesupplyco.com","fabric.com","moodfabrics.com",
    "blackbirdfabrics.com","stonemountainfabric.com")
_add("art_crafts","embroidery",
    "dmc.com","sublimestitching.com","emblibrary.com","urbanthreads.com",
    "jjneedles.com","needlelovers.com","needlepoint.com","stitchpeople.com")
_add("art_crafts","leather",
    "tandyleather.com","weaverleathersupply.com","springfieldleather.com",
    "leatherhidesonline.com","buckleguy.com","rmleathersupply.com",
    "districtleathersupply.com","hideanddrink.com","corterleather.com")
_add("art_crafts","pottery",
    "clay-king.com","theceramicshop.com","bigceramicstore.com","aardvarkclay.com",
    "continentalclay.com","highwaterclays.com","kruegerpottery.com",
    "ceramicartsnetwork.com","amaco.com","speedballart.com","maycocolors.com")

# ============================================================
# V2 EXPANSION: 2,000+ additional curated DTC brands
# ============================================================

# --- APPAREL V2 (300+ more) ---
_add("apparel","activewear","underarmour.com","reebok.com","puma.com","champion.com",
    "bandier.com","michelefranzese.com","tracksmith.com","janji.com","wolaco.com",
    "hilma.co","dharmabums.com.au","lskd.co","musclenation.com","vqfit.com",
    "sculptactivewear.com","bloch.com","capezio.com","discountdance.com","dancewearsolutions.com",
    "movementally.com","sleeperband.com","wearfigs.com","jockey.com","hanes.com",
    "bonds.com.au","calvinklein.com","tommy.com","levi.com","levis.com",
    "wrangler.com","lee.com","gap.com","oldnavy.com","bananarepublic.com",
    "athleta.com","uniqlo.com","hm.com","zara.com","mango.com","cos.com",
    "massimodutti.com","bershka.com","pullandbear.com","stradivarius.com",
    "oysho.com","weekday.com","monki.com","andotherstories.com","arket.com",
    "nanushka.com","ganni.com","goldsignjeans.com","agolde.com","grlfrnd.com",
    "re-done.com","frame-store.com","motherdenim.com","citizensofhumanity.com",
    "paige.com","rag-bone.com","veronicabeard.com","alicelouise.com",
    "aliceandolivia.com","rebeccataylor.com","dvf.com","theory.com","helmutlang.com",
    "acnestudios.com","isabelmarant.com","maisonkitsune.com","ami-paris.com",
    "apc.fr","margarethowell.com","mhlshop.com","studionicholson.com",
    "jacquemus.com","jilsander.com","louisvuitton.com","gucci.com","prada.com",
    "dior.com","fendi.com","miumiu.com","jacquemus.com","bottegaveneta.com",
    "balenciaga.com","celines.com","balmain.com","givenchy.com","loewe.com",
    "saintlaurent.com","versace.com","armani.com","emporioarmani.com","giorgioarmani.com",
    "dolcegabbana.com","ferragamo.com","miumiu.com","etro.com","moschino.com",
    "alexandermcqueen.com","viviennewestwood.com","commedesgarcons.com",
    "maisonmargiela.com","jilsander.com","lanvin.com","thombrowne.com",
    "jacquemus.com","patou.com","barbour.com","baracuta.com","gloverall.com",
    "belstaff.com","schott-nyc.com","vansonleathers.com","langlitz.com",
    "ahlcg.com","nudiejeans.com","acnestudios.com","samsoe.com","stinegoya.com",
    "saks.com","nordstrom.com","neimanmarcus.com","bloomingdales.com",
    "shopbop.com","mytheresa.com","farfetch.com","matchesfashion.com","ssense.com",
    "net-a-porter.com","modaoperandi.com","23wards.com","vestiairecollective.com",
    "therealreal.com","poshmark.com","depop.com","thredup.com","grailed.com",
    "tradesy.com","vinted.com","mercari.com","stockx.com","goat.com",
    "kidizen.com","threadup.com","vinted.com","depop.com","carousell.com")

_add("apparel","womens",
    "mondayswimwear.com","jcrew.com","anntaylor.com","loft.com","talbots.com",
    "chicos.com","whbm.com","whitehouseblackmarket.com","express.com",
    "modcloth.com","uniquevintage.com","tobi.com","francescas.com",
    "abercrombie.com","hollisterco.com","ae.com","pacsun.com","tillys.com",
    "zara.com","urbanoutfitters.com","anthropologie.com","asos.com",
    "missselfridge.com","topshop.com","dorothyperkins.com","burton.co.uk","oasis-stores.com",
    "warehousefashion.com","allsaints.com","reiss.com","tedbaker.com",
    "nastygal.com","boohoo.com","prettylittlething.com","missguided.com",
    "fashionnova.com","windsorstore.com","lulus.com","showpo.com",
    "hello-molly.com","petalandpup.com","lulus.com","revolve.com","shopbop.com",
    "fwrd.com","jane.com","memebox.com","yesstyle.com","chuu.us",
    "stylenanda.com","mixxmix.com","kooding.com","wconcept.com",
    "todayshop.com","lotsofbutter.com","wusastore.com","alexa.com","levi.com",
    "madison-reed.com","renttherunway.com","nuuly.com","armoire.style",
    "letote.com","gwynniebee.com","dia.com","stitchfix.com","trunkclub.com",
    "daily-look.com","wantable.com","shortstorybox.com","eloquii.com",
    "universalstandard.com","torrid.com","lanebryant.com","citychiconline.com",
    "additionelle.com","eloquii.com","asoscurve.com","prettysmallshoes.com",
    "longtallsally.com","petitestudio.com","shoptiques.com","bando.com",
    "francescas.com","altardstate.com","veronicam.com","lucyinthesky.com",
    "beginningboutique.com","saboskirt.com","forloveandlemons.com",
    "lovebonito.com","theclothingcove.com","venus.com","metrostyle.com",
    "goodnightmacaroon.com","shophopes.com","reddressboutique.com",
    "toadandco.com","title nine.com","sundancenow.com","fillyflair.com",
    "eshatki.com","eshakti.com","eileenfisher.com","marinelayer.com","alp n rock.com")

_add("apparel","mens",
    "todd-snyder.com","eastdane.com","mrporter.com","nomanwalksalone.com",
    "unionmadegoods.com","lostandfoundtoronto.com","machusonline.com",
    "bodega.com","conceptshop.com","havenshop.com","corridor.com",
    "nanamica.com","manastash.com","snowpeak.com","white mountaineering.com",
    "visvim.com","engineeredgarments.com","filson.com","woolrich.com","pendleton-usa.com",
    "patagonia.com","thenorthface.com","arcteryx.com","mountainhardwear.com",
    "outdoorresearch.com","adidas.com","nike.com","newbalance.com","asics.com",
    "brooksbrothers.com","ralphlauren.com","tommyhilfiger.com","nordstrom.com",
    "jcrew.com","bonobos.com","untuckit.com","mizzenandmain.com","ministryofsupply.com",
    "oliversapparel.com","outlier.nyc","missionworkshop.com","arcadebelts.com",
    "grip6.com","slidebelt.com","ansoon.co","bullionbelts.com","hanksbelts.com",
    "glassybelts.com","missionbelt.com","groovelife.com","carhartt-wip.com",
    "brixton.com","obeyclothing.com","thenorthface.com","wesc.com","elementbrand.com",
    "billabong.com","quiksilver.com","roxy.com","volcom.com","ripcurl.com",
    "proclub.com","shakawear.com","freshivy.com","levi.com","gap.com",
    "uniqlo.com","hm.com","zara.com","massimodutti.com","buckmason.com",
    "taylorstitch.com","flintandtinder.com","propercloth.com","spierandmackay.com",
    "charles tyrwhitt.com","tmlewin.com","etonshirts.com","stensonshirts.com",
    "ledbury.com","yatesandco.com","hammer made.com","stateandliberty.com",
    "mizzenandmain.com","bonobos.com","everlane.com","fahertybrand.com",
    "rhone.com","ten thousand.cc","oliversapparel.com","mylesapparel.com",
    "reigningchamp.com","johnelliott.com","representclo.com","kotn.com",
    "pact.com","tentree.com","outerknown.com")

_add("apparel","shoes",
    "nike.com","adidas.com","newbalance.com","converse.com","vans.com",
    "reebok.com","puma.com","asics.com","saucony.com","brooksrunning.com",
    "hokaoneone.com","on-running.com","salomon.com","merrell.com","keenfootwear.com",
    "timberland.com","dr-martens.com","redwingshoes.com","thursdayboots.com",
    "tecovas.com","ariat.com","tonylama.com","justinboots.com","danpostboots.com",
    "duluthtrading.com","wolverine.com","carolina boots.com","chippewaboots.com",
    "bogsfootwear.com","crocs.com","birkenstock.com","ugg.com","sorel.com",
    "teva.com","chacos.com","rainbow sandals.com","olukai.com","reef.com",
    "sanuk.com","toms.com","bobsfromskechers.com","skechers.com","clarks.com",
    "rockport.com","ecco.com","naturalizer.com","lifestride.com","easy spirit.com",
    "florsheim.com","johnstonmurphy.com","allen-edmonds.com","aldenshoe.com",
    "carminashoemaker.com","meermin.com","loake.com","church-footwear.com",
    "crockettandjones.com","edwardgreen.com","frye.com","stevemadden.com",
    "aldo.com","callitspring.com","ninewest.com","sam edelman.com","francosarto.com",
    "vince.com","alexanderwang.com","jimmychoo.com","louboutin.com",
    "aquazzura.com","gianvitorossi.com","manoloblahnik.com","rogervivier.com",
    "stuartweitzman.com","christianlouboutin.com","louisvuitton.com",
    "gucci.com","prada.com","balenciaga.com","ysl.com","versace.com")

_add("apparel","streetwear",
    "supremenewyork.com","bape.com","bathingape.com","off---white.com","essentialsofficial.com",
    "ericemanuel.com","livinthemargins.com","pleasuresnow.com","section8.co",
    "alwaysdowhatyoushouldad.com","marketatmos.com","undefeated.com","rsvpgallery.com",
    "bodega.com","concepts.com","havenshop.com","doverstreetmarket.com",
    "unionlosangeles.com","rsvpgallery.com","socialstatuspgh.com","amateurstore.com",
    "awake-ny.com","justdon.com","palmangels.com","heronpreston.com",
    "alyxstudio.com","casablancaparis.com","off---white.com","icecream.com",
    "billionaireboysclub.com","cactusplantfleamarket.com","charlieconstantino.com",
    "fuckingawesomestore.com","biancachandon.com","whoisjacov.com",
    "golfwang.com","asapmob.com","vlone.co","fearofgod.com","rhude.com")

_add("apparel","sustainable",
    "ableclothing.com","whimsyandrow.com","christydawn.com","doen.co","mate the label.com",
    "amourvert.com","nathalie.com","tonle.com","bodenusa.com","alicea.com",
    "studiosucre.com","knownsupply.com","wearthree.com","coyuchi.com",
    "pact.com","tentree.com","kotn.com","outerknown.com","everlane.com",
    "reformation.com","cuyana.com","patagonia.com","eileenfisher.com",
    "amourvert.com","peopletree.co.uk","thoughtclothing.com","finisterre.com",
    "passengerclothing.com","wearenika.com","sezane.com","majesticfilatures.com",
    "lauren manoogian.com","elderstatesman.com","fillmorethelabel.com",
    "filippak.com","byfreasth.com","bassike.com","kowtowclothing.com",
    "studiadelaide.com","ninetypercent.com","mother of pearl.co.uk",
    "mara hoffman.com","stinegoya.com","ganni.com","saks potts.com",
    "hope-sthlm.com","our legacy.com","teurn studios.com","masscob.com",
    "ilovevelvet.com","bode.com","emilylevine.com","milleetrose.com")

_add("apparel","swimwear",
    "hermes.com","chanel.com","dior.com","versace.com","moschino.com",
    "solidandstriped.com","mikoh.com","mollygodard.com","loveshackfancy.com",
    "zimmermann.com","alessandra rich.com","johannaortiz.com","agua bendita.com",
    "lspace.com","beachriot.com","hampton suns.com","sleepingwithjaguars.com",
    "marysia.com","miraclesuit.com","magicsuit.com","lascana.com",
    "swimsuitsforall.com","aerin rose.com","voda swim.com","bleu rod beattie.com",
    "norma kamali.com","gottex.com","mikoh.com","ondademar.com",
    "acacia swimwear.com","somerset.com","jeanelise.com","deakinandblue.com",
    "lyraswim.com","wearewear.com","voyage et cie.com","cupshe.com",
    "zaful.com","shein.com","dippindaisys.com","kulikoo.com","saltycrush.com")

_add("apparel","socks_underwear",
    "stance.com","bombas.com","pairofthieves.com","saxxunderwear.com",
    "meundies.com","cdlp.com","frankandroot.com","thebureaubelfast.com",
    "intimissimi.com","calvinklein.com","hugoboss.com","tommyhilfiger.com",
    "emporioarmani.com","vvd.co","nakedsoul.com","diesel.com","aubade.com",
    "agentprovocateur.com","lascana.com","bluebella.com","lonelylabel.com",
    "chantelle.com","simoneperele.com","prima-donna.com","mariejo.com",
    "wacoal.com","fantasie.com","freya.com","panache.com","elomilingerie.com",
    "curvykate.com","gossard.com","natori.com","hankypanky.com","commando.com",
    "somaintimates.com","lively.com","thirdlove.com","cuup.com","parade.com",
    "organicbasics.com","weardixie.com","falke.com","bresciani.com","pantherella.com",
    "mazaringo.com","tuck.com","johnsmedley.com","sunspel.com","jamesperse.com")

_add("apparel","workwear_outdoor",
    "duluthtrading.com","carhartt.com","ariat.com","cathartt.com",
    "engelbert-strauss.com","snickersworkwear.com","hellyhansen.com","dickies.com",
    "redkap.com","walls.com","keyapparel.com","roundhouse.com","lc-king.com",
    "prisonblues.com","gostwear.com","workngear.com","refrigiwear.com",
    "blaklader.com","bjornklader.com","kansasworkwear.com","mascotworkwear.com",
    "diestateleather.com","grailersleather.com","thethylads.com","schott-nyc.com",
    "langlitzleathers.com","vansonleathers.com","foxtaileather.com","kincorleather.com",
    "misterfreedom.com","buzzricksons.com","eastmanleather.com","simonsleather.com")

# --- ELECTRONICS V2 (200+ more) ---
_add("electronics","audio",
    "dynaudio.com","focal.com","kef.com","bowerswilkins.com","denon.com","marantz.com",
    "yamaha.com","sony.com","apple.com","samsung.com","lg.com","google.com",
    "amazon.com","mackie.com","qsc.com","jblpro.com","electrovoice.com","dbtechnologies.com",
    "rcf.it","turbosound.com","funktion-one.com","meyer sound.com","l-acoustics.com",
    "martin-audio.com","zuaudio.com","vandersteen.com","martinlogan.com","magnepan.com",
    "totemacoustic.com","galloacoustics.com","devialet.com","naimaudio.com",
    "luxman.com","mcintoshlabs.com","accuphase.com","burmester.de","gryphon-audio.com",
    "wilsonaudio.com","sonusfaber.com","audioquest.com","wireworldcable.com",
    "cardas.com","nordost.com","transparentcable.com","mitcables.com",
    "avrevolution.com","rega.co.uk","project-audio.com","clearaudio.de","vpiindustries.com",
    "orrtofon.com","shure.com","goldring.co.uk","grado.com","audio-technica.com",
    "austrianaudio.com","heddphone.com","danclarkaudio.com","warwickacoustics.com")

_add("electronics","smarthome",
    "abode.com","frontpointsecurity.com","link interactive.com","vivint.com","alarm.com",
    "adt.com","bluebyadt.com","cove.com","covesmart.com","scoutalarm.com",
    "getkisi.com","latch.com","igloohome.co","nukihome.com","yalehome.com",
    "schlage.com","level.co","august.com","lockstate.com","remotelock.com",
    "smartthings.com","hubitat.com","home-assistant.io","wink.com","inovelli.com",
    "zoozzwaveus.com","zoozzwave.com","aeotec.com","fibaro.com","zwave.com",
    "homey.app","knx.org","crestron.com","control4.com","savant.com",
    "lutron.com","leviton.com","eaton.com","legrand.com","brilliant.tech",
    "mysa.com","sinope.com","stelpro.com","emporiaweather.com","rainmachine.com",
    "rachio.com","wyze.com","ring.com","blink.com","eufy.com","arlo.com","swann.com")

_add("electronics","gaming",
    "playstation.com","xbox.com","nintendo.com","steampowered.com","valvesoftware.com",
    "epicgames.com","blizzard.com","ubisoft.com","ea.com","activision.com","take2games.com",
    "bethesda.com","rockstargames.com","square-enix.com","bandainamco.com",
    "sega.com","capcom.com","konami.com","koeitecmo.com","atlus.com",
    "ganeworld.com","gamestop.com","fry's electronics.com","microcenter.com",
    "newegg.com","bhphotovideo.com","adorama.com","focuscamera.com","uniquephoto.com",
    "pcpartpicker.com","ibuypower.com","cyberpowerpc.com","originpc.com","falcon-nw.com",
    "mainframe.com","pugetsystems.com","digitalstorm.com","maingear.com",
    "velocitymicro.com","nzxt.com","coolermaster.com","corsair.com","asus.com",
    "msi.com","gigabyte.com","evga.com","xfx.com","sapphiretech.com",
    "powercolor.com","zotac.com","pny.com","gskill.com","crucial.com",
    "kingston.com","corsair.com","teamgroup.com","samsung.com","western digital.com",
    "seagate.com","sandisk.com","adata.com","crucial.com","sabrent.com")

_add("electronics","camera",
    "sony.com","canon.com","nikon.com","fujifilm.com","olympus.com","panasonic.com",
    "leica.com","hasselblad.com","phaseone.com","pentax.com","ricoh.com",
    "tamron.com","sigma.com","rokinon.com","samyang.com","zeiss.com",
    "venuslens.com","venuslens.net","laowalens.com","mitakon.com",
    "peakdesign.com","wandrd.com","boundarysupply.com","shimodadesigns.com",
    "fstopgear.com","lowepro.com","thinktankphoto.com","manfrotto.com",
    "gitzo.com","3leggedthing.com","reallyrightstuff.com","profoto.com",
    "elinchrom.com","broncolor.com","godox.com","flashpoint.com","westcott.com",
    "lumecube.com","aputure.com","nanlite.com","rotolight.com","arri.com",
    "red.com","blackmagicdesign.com","panasonic.com","canon.com","atomos.com",
    "smallhd.com","tvlogic.com","swit.com","dji.com","freeflysystems.com")

_add("electronics","wearables",
    "apple.com","samsung.com","garmin.com","fitbit.com","whoop.com","ouraring.com",
    "suunto.com","polar.com","withings.com","coros.com","amazfit.com",
    "fossil.com","misift.com","skagen.com","michaelkors.com","diesel.com",
    "tagheuer.com","montblanc.com","movado.com","tissot.com","citizenwatch.com",
    "seikousa.com","casio.com","timex.com","boltt.com","fastrack.com",
    "noise.com","boat-lifestyle.com","honor.com","huawei.com","oppo.com",
    "xiaomi.com","oneplus.com","google.com","nokia.com","tcl.com","zeblaze.com",
    "ticwatch.com","mobvoi.com","mymemory.com","waoo.com","hifuture.com")

_add("electronics","peripherals",
    "logitech.com","microsoft.com","apple.com","das keyboard.com","wasdkeyboards.com",
    "codekeyboards.com","filco.com","realforce.com","topre.com","hhkeyboard.com",
    "leopold.com","ikbc.com","x-bows.com","cloudnine.com","kinesis-ergo.com",
    "ergodox-ez.com","moonlander.com","oritype.com","ultimate hacking keyboard.com",
    "razer.com","corsair.com","steelseries.com","hyperx.com","logitechg.com",
    "gloriousgaming.com","benq.com","eizo.com","necdisplay.com","viewsonic.com",
    "asus.com","acer.com","hp.com","lenovo.com","dell.com","gigabyte.com",
    "msi.com","samsung.com","lg.com","apple.com","thinkvision.com",
    "startech.com","anker.com","satechi.com","caldigit.com","owc.com","elgato.com",
    "tplink.com","netgear.com","d-link.com","asus.com","linksys.com",
    "google.com","eero.com","ubnt.com","tp-link.com","arubanetworks.com")

# --- JEWELRY V2 (150+ more) ---
_add("jewelry_accessories","jewelry",
    "tiffany.com","cartier.com","bulgari.com","vancleefarpels.com","harrywinston.com",
    "chaumet.com","boucheron.com","mellerio.com","piaget.com","chopard.com",
    "graff.com","tasaki.com","mikimoto.com","tasaki-america.com","debeers.com",
    "forevermark.com","tacori.com","simongjewelry.com","verlas.com","whiteflash.com",
    "leibish.com","fancycolordiamonds.com","cleanorigin.com","doamore.com",
    "benbridge.com","tappers.com","ross-simons.com","jared.com","kay.com",
    "zales.com","peoplesjewelers.com","helzbergdiamonds.com","macys.com",
    "shop.kenanddana design.com","starlighthjewelry.com","brilliantearth.com",
    "jamesallen.com","bluenile.com","vrai.com","nobleandstone.com","bario neal.com",
    "pamelalove.com","jenniferfisher.com","meganmcduffee.com","aureumcollective.com",
    "yunnjewelry.com","harwellgodfrey.com","ilj jewelry.com","misfitdiamonds.com",
    "pointnopointstudio.com","wanderset.com","sophiebuhai.com","jade traversy.com",
    "alixyang.com","ekejewelry.com","locollection.com","lunaandstella.com",
    "coldpicnic.com","staxjewelry.com","ringbomber.com","eddieborgo.com",
    "miansai.com","gilesandbrother.com","martingro.com","gorjana.com",
    "pamelalove.com","nialaya.com","johnhardy.com","davidyurman.com",
    "ippolita.com","templeofinca.com","loren stewart.com","janeleslie.com",
    "phillipgavriel.com","calleen cordero.com","babettejewelry.com","allisonkau.com",
    "tura sugden.com","farisjewelry.com","anitako.com","adinasjewels.com",
    "parnia.com","wolfandbadger.com","melindamaria.com","krissceylon.com",
    "flonty.com","astera.com","craftdlondon.com","lottie nyc.com","roxanne_assoulin.com",
    "ciate.com","pitchjewelry.com","shylee rose.com","l l boutique.com")

_add("jewelry_accessories","watches",
    "rolex.com","omega.com","breitling.com","iwc.com","panerai.com","tagheuer.com",
    "patek.com","audemarspiguet.com","vacheron-constantin.com","jaeger-lecoultre.com",
    "cartier.com","piaget.com","chopard.com","hublot.com","richardmille.com",
    "breguet.com","blancpain.com","glashutte-original.com","a-lange.com","ulysse-nardin.com",
    "girard-perregaux.com","zenith-watches.com","bellross.com","oris.com","longines.com",
    "radowatches.com","hamiltonwatch.com","tissotwatches.com","mi.do.com","certina.com",
    "seikousa.com","citizenwatch.com","casio.com","orientwatchusa.com","invictawatch.com",
    "movadogroup.com","timex.com","fossil.com","skagen.com","danielwellington.com",
    "mvmt.com","shinola.com","weisswatch.com","oakandoscar.com","voroband.com",
    "noduswatches.com","halioswatches.com","martenero.com","axiwatches.com",
    "brew watch.com","detroitwatches.com","lamberto.com","michelsen-watch.com",
    "laco.de","stowa.de","sinn.de","damasko.de","archeim.com","nomos-glashuette.com",
    "junghans.de","meistersinger.com","lehmans.com","ritmo.com","changeyou.com")

_add("jewelry_accessories","eyewear",
    "ray-ban.com","persol.com","oliverpeoples.com","garrettleight.com",
    "moscot.com","sama eyewear.com","warbyparker.com","eyebuydirect.com",
    "zennioptical.com","glassesusa.com","firmoo.com","zeelool.com",
    "lenscrafters.com","targetoptical.com","costco.com","walmart.com",
    "sunglasshut.com","solsticesunglasses.com","americanoptical.com",
    "randolphusa.com","aoeyewear.com","sunski.com","blenderseyewear.com",
    "goodr.com","nativesunglasses.com","mauijim.com","costadelmar.com",
    "kaenon.com","spyoptic.com","electriccalifornia.com","vonzipper.com","dragonalliance.com",
    "arnette.com","oakley.com","smithoptics.com","rudyproject.com",
    "bolle.com","carrera.com","polaroid.com","tedbaker.com","gucci.com",
    "prada.com","ray-ban.com","versace.com","dior.com","chanel.com",
    "tomford.com","burberry.com","ysl.com","dolcegabbana.com","fendi.com",
    "givenchy.com","alexandermcqueen.com","balmain.com","tiffany.com","montblanc.com")

# --- TOYS & HOBBIES V2 (150+ more) ---
_add("toys_hobbies","boardgames",
    "magic.wizards.com","pokemoncenter.com","yugioh.com","cardfight-online.com",
    "finalfantasytcg.com","dragonshield.com","ultrapro.com","maydaygames.com",
    "sleevedominance.com","decktutor.com","mtgcards.com","cardkingdom.com",
    "tcgplayer.com","starcitygames.com","channelfireball.com","abugames.com",
    "trollandtoad.com","coolstuffinc.com","miniaturemarket.com","gamenverdz.com",
    "boardgamebliss.com","meeplemart.com","boardgameco.com","boardgames.ca",
    "oxfordgames.com","warhousetablegames.com","boardgameoracle.com",
    "tabletop gaming store.com","davinci games.com","999 games.com",
    "rulesofplay.com","gaya games.com","crowdgames.com","meeple.house",
    "tggames.com","cogumelos.com","stratego.com","monopoly.com","scrabble.com",
    "risk.com","catan.com","carcassonne.com","czechgames.com","strongholdgames.com",
    "hans-im-glueck.de","lookout-spiele.de","porter-games.com","asmodee.com",
    "pandasaurusgames.com","capstone-games.com","feuerland-spiele.de","fantasyflightgames.com")

_add("toys_hobbies","educational",
    "bambinomoon.co","tinker.co","snapcircuits.net","makeymakey.com","littlebits.cc",
    "adafruit.com","sparkfun.com","seeedstudio.com","arduino.cc","raspberrypi.com",
    "microbit.org","bloggercode.com","tynker.com","code.org","scratch.mit.edu",
    "codakid.com","codemonkey.com","lightbot.com","roboturtle.com","khanacademy.org",
    "brilliant.org","outschool.com","wonderville.com","khanacademylabs.org",
    "melscience.com","subscription-box.org","stemcell.com","meadowbrook.com",
    "kiwi.co","creationcrate.com","groovelabs.com","codewizardshq.com",
    "junilearning.com","codecombat.com","codemeister.com","mydoh.co",
    "greenlight.com","gohenry.com","busykid.com","copperbank.com","current.com")

_add("toys_hobbies","collectibles",
    "shopdisney.com","disneystore.com","universalorlando.com","wbshop.com",
    "mattel.com","hasbropulse.com","funko.com","entertainmentearth.com",
    "bigbadtoystore.com","sideshow.com","hottoys.com","threezerohk.com",
    "mezcotoyz.com","super7.com","necaonline.com","mcfarlane.com",
    "dccomics.com","marvel.com","starwars.com","potterybarnkids.com",
    "animation.com","popcultcha.com","collectiblesdirect.com","archonia.com",
    "komokomodo.com","toyorigins.com","mytoy.co.uk","kidrobot.com",
    "toywiz.com","toynk.com","ee.toys","geminiscollectibles.com","monsters in motion.com",
    "forbiddenplanet.com","midtowncomics.com","midtown comics.com","thingsfromanotherworld.com",
    "zavvi.com","popinabox.com","thepopcollective.com","plasticempire.com",
    "booksofwonder.com","mintoys.com","retro-toy.com","bigpop.com","heroes collectibles.com",
    "collectables.com","hobbiescollectibles.com","snapsuits.com","dinosaur.com")

_add("toys_hobbies","models",
    "hobbylinc.com","modelcars.com","modelroundup.com","scalefinishes.com",
    "modelroundup.com","kitmaker.com","scalemates.com","internethobbies.com",
    "micromark.com","megahobby.com","hobbylinc.com","spruebrothers.com",
    "scalehobbyist.com","hobbyworld-usa.com","hobbysearch.com","1999.co.jp",
    "hlj.com","amiami.com","tokyomodelshop.com","plazajapan.com",
    "hobbyterra.com","model-space.com","metalearth.com","fascinations.com",
    "metallic-time.com","piececool.com","timemicro.com","mu-models.com",
    "deagostini.com","eaglemoss.com","agoramodels.com","model-space.com",
    "diecastmodelswholesale.com","diecastdirect.com","toywonders.com","3000toys.com",
    "fairytalemodels.com","modeltoycars.com","americanscalemodels.com")

_add("toys_hobbies","puzzles",
    "jigsawpuzzles.com","puzzle warehouse.com","jigsawpuzzlesdirect.co.uk","puzzlefun.com",
    "puzzleyou.com","puzzleplanet.com","ceaco.com","springbok-puzzles.com",
    "masterpiecesinc.com","buffalogames.com","eurographicspuzzles.com",
    "sunsout.com","aquariuspuzzles.com","heye-puzzle.com","schmidtpuzzles.com",
    "treflpuzzles.com","castorlandpuzzles.com","jeka puzzles.com","clementoni.com",
    "educaborras.com","javipuzle.com","legpuzz.com","newyorkpuzzle.com",
    "pomegranate.com","artandfablepuzzleco.com","eeboo.com","mudpuppy.com",
    "crocodilecreek.com","puzzlelibrarian.com","puzzlebox.com","playroom.com",
    "wirecutter.com","puzzlecube.com","thepuzzlepeople.com","potluckpress.com",
    "malfyn.com","woodenpuzzles.com","woodpuzzles.com","magicpuzzlecompany.com")

_add("toys_hobbies","rc",
    "teamassociated.com","tlr.com","xray.com","serpent.com","mugenseiki.com",
    "hotbodies.com","sworkz.com","agama-rc.com","tekno-rc.com","kyosho.com",
    "tamiya.com","hpiracing.com","modelsport.com","wheelspinmodels.co.uk",
    "amainhobbies.com","horizonhobby.com","rcplanet.com","towerhobbies.com",
    "omnModels.com","rcmart.com","asiatees.com","rc-race-shop.com",
    "prolineracing.com","jconcepts.com","louise-rc.com","fastrax-rc.com",
    "sweepracing.com","contactrc.com","teamorion.com","tekin.com",
    "hobbywing.com","castlecreations.com","maclan-racing.com","reventon-esc.com",
    "smc-racing.com","gensace.com","dynamite-rc.com","reedyrc.com")

# --- MUSICAL INSTRUMENTS V2 (150+ more) ---
_add("musical_instruments","guitars",
    "anderson-guitarworks.com","tomandersonguitars.com","suhr.com","tylerguitars.com",
    "james tyler guitars.com","nashguitars.com","lslguitars.com","xotic.us",
    "melancon guitars.com","warrior guitars.com","mayones.com","skervesenguitars.com",
    "aristidesinstruments.com","blackmachineguitars.com","orkeby.se",
    "liuteria.it","dunableguitars.com","esp guitars.com","ltdguitars.com",
    "dean guitars.com","bcrich.com","kramerguitars.com","steinberger.com",
    "parkersguitars.com","virginiaguitars.com","hussanddalton.com","bourgeoisguitars.com",
    "froggybottomguitars.com","goodallguitars.com","taylorguitars.com",
    "lariveeguitars.com","lowdenguitars.com","beardsellguitars.com","ferrington guitars.com",
    "mcphersonguitars.com","rainsong.com","emerald guitars.com","journeyinstruments.com",
    "klosguitars.com","enya-music.com","matt black guitar.com","airlineguitars.com",
    "harmony.co","guildguitars.com","ovationguitars.com","takamine.com",
    "alvarezguitars.com","blueridgeguitars.com","recordingking.com",
    "seagullguitars.com","simonandpatrick.com","artandlutherie.com",
    "norman guitars.com","easton guitars.com","breedloveguitars.com")

_add("musical_instruments","pedals",
    "analogman.com","keeleyelectronics.com","wamplerpedals.com","jhspedals.com",
    "earthquakerdevices.com","walrusaudio.com","oldbloodnoise.com","chasebliss.com",
    "strymon.net","meris.us","eventideaudio.com","boss.info",
    "mxr.com","electricharmonix.com","ibanez.com","digitech.com","dod.com",
    "line6.com","fractalaudio.com","kemper-amps.com","neuraldsp.com","quadcortex.com",
    "headrushfx.com","hotoneaudio.com","moore audio.com","nuxefx.com",
    "tc-helicon.com","tc-electronic.com","xotic.us","vertexeffects.com",
    "bjfeguitars.com","mad professor amplification.com","fulltone.com",
    "rodenbergguitars.com","okko-fx.com","providence-ltd.com","free the tone.com",
    "onecontrol.com","truetone.com","voodoolab.com","cioks.com","strymon.net",
    "missionengineering.com","ernieball.com","dunlop.com","morley pedals.com",
    "sourceaudiopedals.com","red panda lab.com","cooperfx.com","dr scientist sounds.com",
    "spaceman effects.com","fairfieldcircuitry.com","montrealassembly.com",
    "smallsoundbigsound.com","industrialectric.com","dirgemachines.com")

_add("musical_instruments","amps",
    "fender.com","marshall.com","voxamps.com","orangeamps.com","mesaboogie.com",
    "peavey.com","fryette.com","soldano.com","bogneramps.com","diezelamps.com",
    "drzamps.com","carr-amps.com","morganamps.com","milkman-sound.com",
    "victoryamps.com","tonekingamps.com","matchlessamps.com","badcatamps.com",
    "dividedby13.com","two-rock.com","bludotone.com","dumble-clones.com",
    "ceriatone.com","mojotone.com","rivera.com","egnateramps.com",
    "hughes-and-kettner.com","engl-amps.com","laboga.pl","krankamps.com",
    "ampeg.com","aguitaramps.com","swartamps.com","bensonamps.com",
    "fenderaudio.com","allenamps.com","headstrongamps.com","clark amplification.com",
    "vintagesoundamps.com","lazyjprojects.com","reevesamps.com","hiwatt.org",
    "parkamps.com","cornfordamps.com","koch-amps.com","petersamps.com",
    "catalinbread.com","quilterlabs.com","blu guitar.com","bluguitar.com",
    "yamaha.com","roland.com","boss.info","line6.com","fender.com")

_add("musical_instruments","synths",
    "moogmusic.com","korg.com","roland.com","yamaha.com","teenage.engineering",
    "sequential.com","oberheim.com","dsi.com","arturia.com","elektron.se",
    "nordkeyboards.com","clavia.se","waldorfmusic.com","novationmusic.com",
    "akai-pro.com","native-instruments.com","ableton.com","presonus.com",
    "focusrite.com","apogeedigital.com","uaudio.com","rme-audio.com",
    "motu.com","antelopeaudio.com","lynxstudio.com","merging.com","prismsound.com",
    "cranesong.com","burlaudio.com","dave smith instruments.com","tomoberheim.com",
    "studioelectronics.com","baloran.com","black-corporation.com","deckardsdream.com",
    "makenoisemusic.com","intellijel.com","verbos electronics.com","xaocdevices.com",
    "instruomodular.com","mutable-instruments.net","wmd-devices.com","industrialmusicelectronics.com",
    "modularaddict.com","perfectcircuit.com","ctrl-mod.com","detroitmodular.com",
    "analoguehaven.com","schneidersladen.de","signalsounds.com","elevatorsound.com")

_add("musical_instruments","drums",
    "drumcenternh.com","memphisdrumshop.com","drumshop.co.uk","steveweissmusic.com",
    "lone star percussion.com","columbuspercussion.com","forksdrumcloset.com",
    "2112percussion.com","chicagomusicexchange.com","drummersuperstore.com",
    "drumflip.com","drummax.com","drummerswarehouse.com","musiciansfriend.com",
    "guitarcenter.com","sweetwater.com","samash.com","zzounds.com",
    "reverb.com","ebay.com","drumfactory.com","drumsonsale.com","interstatemusic.com",
    "vicfirth.com","pro-mark.com","zildjian.com","sabian.com","paiste.com",
    "meinlcymbals.com","ufip.com","turkishcymbals.com","istanbulcymbals.com",
    "bosphoruscymbals.com","masterworkcymbals.com","soultonecymbals.com",
    "dreamcymbals.com","remo.com","evansdrumheads.com","aquariandrumheads.com",
    "attackdrumheads.com","code drumheads.com","dwdrums.com","pdpdrums.com",
    "gretschdrums.com","tama.com","pearldrum.com","mapexdrums.com",
    "sonordrums.com","yamaha.com","ludwig-drums.com","sakae-drums.com",
    "premier-drums.com","nataldrums.com","canopusdrums.com","taye.com","ddrum.com")

_add("musical_instruments","proaudio",
    "neumann.com","akg.com","sennheiser.com","beyerdynamic.com","shure.com",
    "audiotechnica.com","rode.com","dpamicrophones.com","astonmics.com","warmaudio.com",
    "se electronics.com","lautenaudio.com","miktek.com","telefunken-elektroakustik.com",
    "soyuzmicrophones.com","brauner-microphones.com","manleylabs.com","universalaudio.com",
    "solidstatelogic.com","neve.com","rupertneve.com","api audio.com",
    "manleylabs.com","chandlerexclusive.com","tridentaudiodevelopments.com",
    "audient.com","focusrite.com","presonus.com","behringer.com","mackie.com",
    "allen-heath.com","soundcraft.com","midasconsoles.com","digico.biz",
    "avid.com","steinberg.net","cakewalk.com","ableton.com","presonus.com",
    "focal.com","barefootsound.com","atc.com","pmc-speakers.com",
    "genelec.com","adam-audio.com","eve-audio.com","hedd.audio",
    "dynaudio.com","krksys.com","yamaha.com","jblpro.com","tannoy.com")

# --- HARDWARE & TOOLS V2 (150+ more) ---
_add("hardware","tools",
    "dewalt.com","milwaukeetool.com","makitatools.com","boschtools.com","ryobitools.com",
    "ridgid.com","portercable.com","skil.com","craftsman.com","blackanddecker.com",
    "kobalt.com","husky.com","harttools.com","hyper-tough.com","bostitch.com",
    "stanleytools.com","irwin.com","lenox.com","kleintools.com","greenlee.com",
    "idealind.com","flukepro.com","flir.com","extech.com","amprobe.com",
    "southwire.com","gardnerbender.com","wiha.com","wera.de","bondo.com",
    "fein.com","festoolusa.com","metabo.com","hitachi-powertools.com","hilti.com",
    "mklotools.com","martintoolsusa.com","skhandtool.com","proto.com","channel lock.com",
    "vise-grip.com","irwin.com","stanleytools.com","estwing.com","vaughanmfg.com",
    "dalluge.com","stiletto.com","martinez tools.com","snapon.com","mac tools.com",
    "matcotools.com","cornwelltools.com","tooltopia.com","harryepstein.com","toolplanet.com",
    "gemplers.com","lehighvalleyabrasives.com","empireabrasives.com","benchmark abrasives.com",
    "superiorabrasives.com","nortonabrasives.com","3m.com","3mshop.com")

_add("hardware","knives",
    "bladehq.com","knifecenter.com","donrightknives.com","cutleryshoppe.com",
    "dlttrading.com","gpknives.com","recon1.com","knivesshipfree.com",
    "usa-made-blades.com","knifeart.com","nordicknives.com","bladeops.com",
    "knifeworks.com","smkw.com","smoky mountain knife works.com","gunsandknives.com",
    "thrillonknives.com","srmknives.com","sanrenmu.com","besteel.com",
    "two sun knives.com","green thorn knives.com","shirogorov.com",
    "custom knife factory.com","ricky hinderer knives.com","half face blades.com",
    "toor knives.com","winkler knives.com","rmij knives.com","bark river knives.com",
    "lt wright knives.com","fiddleback forge.com","adventure sworn.com","malanika.com",
    "seedy lot.com","bushcraft store.com","ragweed forge.com","thompsons knife.com",
    "agrussell.com","japaneseknifedirect.com","chefknivestogo.com"," japanesechefsknife.com",
    "hocho-knife.com","knifemerchant.com","japanese knife imports.com","carbon knife co.com",
    "bernal cutlery.com","couteliernola.com","tokushuknife.com","sharpedgeshop.com")

_add("hardware","flashlights",
    "surefire.com","streamlight.com","fenixlight.com","olight.com","nitecore.com",
    "thrunite.com","acebeam.com","skilhunt.com","lumintop.com","zebralight.com",
    "armytek.com","malkoffdevices.com","elzetta.com","modlite.com","clouddefensive.com",
    "arisakadefense.com","darksucks.com","oveready.com","frazlabs.com","hdslights.com",
    "foursevens.com","eagletac.com","imalent.com","mateminco.com","astrolux.com",
    "emisar.com","noctigon.com","ff-light.com","convoy flashlight.com",
    "sofirnlight.com","wubenlight.com","wurkkos.com","rovvyang.com","lumentop.com",
    "reylight.net","focusworks.com","darksucks.com","ti mack.com","prometheuslights.com",
    "mechforce.com","copperhead flashlight.com","sigma customs.com","candlepowerforums.com",
    "budgetlightforum.com","flashlightuniversity.com","parametrek.com","1lumen.com")

_add("hardware","homeimprovement",
    "homedepot.com","lowes.com","menards.com","acehardware.com","truevalue.com",
    "doitbest.com","orgill.com","emser tile.com","houzz.com","build.com",
    "faucetdirect.com","lightingdirect.com","plumbersstock.com","homeperfect.com",
    "decorplanet.com","qualitybath.com","plumbtile.com","builderssurplus.com",
    "absolutehome.com","americantinshop.com","signaturehardware.com","kingstonbrass.com",
    "elegantadditions.com","watermark-designs.com","californiafaucets.com","newportbrass.com",
    "rok hardware.com","rejuvenation.com","schoolhouse.com","shadesoflight.com",
    "lumens.com","ylighting.com","lightology.com","lightingnewyork.com",
    "bellacor.com","lampsplus.com","1800lighting.com","capital lighting.com",
    "hudsongoods.com","industville.com","bareboneliving.com","cafekitchenstore.com",
    "greenhousemegastore.com","growerssupply.com","tractorsupply.com","harborfreight.com",
    "northerntool.com","grizzly.com","woodcraft.com","rockler.com","leevalley.com",
    "lie-nielsen.com","veritastools.com","garrettwade.com","the-home-depot.com")

# --- HEALTH SUPPLEMENTS V2 (200+ more) ---
_add("health_supplements","vitamins",
    "gnc.com","vitaminshoppe.com","vitacost.com","iherb.com","swansonvitamins.com",
    "puritan.com","luckyvitamin.com","allstarhealth.com","netrition.com","gap.com",
    "vitaminworld.com","healthspan.co.uk","hollandandbarrett.com","dollarnutrition.com",
    "peapod.com","herbalife.com","isagenix.com","beachbody.com","plexusworldwide.com",
    "arbonne.com","doterra.com","youngliving.com","melaleuca.com",
    "usana.com","kyani.com","lifevantage.com","jeunesseglobal.com",
    "amway.com","neolife.com","mannatech.com","modere.com",
    "nowfoods.com","solgar.com","naturesway.com","gaiaherbs.com",
    "gardenoflife.com","megafood.com","newchapter.com","countrylifevitamins.com",
    "enzymatic therapy.com","source naturals.com","jarrow.com","doctorsbest.com",
    "california gold nutrition.com","swansonvitamins.com","pureencapsulations.com",
    "thorne.com","dfhtyme.com","designsforhealth.com","orthomolecularproducts.com",
    "metagenics.com","integrative therapeutics.com","xymogen.com","cellcorebiosciences.com",
    "microbe formulas.com","bio-botanical research.com","seekinghealth.com","drberg.com",
    "drjockers.com","drruscio.com","drhyman.com","drhardick.com","drperlmutter.com",
    "mindbodygreen.com","goop.com","poosh.com","thebeautychef.com","welleco.com")

_add("health_supplements","protein",
    "myprotein.com","bulk.com","truenutrition.com","optimumnutrition.com",
    "bsn.com","isagenix.com","herbalife.com","usana.com","shakeology.com",
    "310nutrition.com","idealshape.com","idealprotein.com","slimfast.com",
    "atkins.com","keto.org","ketologic.com","perfectketo.com","ketobars.com",
    "nutrishopusa.com","supplementhunt.com","fitnessfirst.com","t-nation.com","muscleandstrength.com",
    "bodybuilding.com","prosource.com","supplementwarehouse.com","vitacost.com",
    "a1supplements.com","bestpricenutrition.com","dpsnutrition.net","musclefeast.com",
    "canadianprotein.com","smartpowders.com","purebulk.com","hardrhino.com",
    "nuts.com","bulkpowders.co.uk","proteinworks.com","bulkpowders.com",
    "theproteinworks.com","reflex nutrition.com","phd nutrition.com","grenade.com",
    "usn.com","scitec nutrition.com","biotechusa.com","applied nutrition.com","warrior.com")

_add("health_supplements","cbd",
    "charlottesweb.com","cbdmd.com","greenroads.com","cbdfx.com","cbd american shaman.com",
    "purekana.com","diamondcbd.com","cbdistillery.com","medterra.com","joyorganics.com",
    "lazarusnaturals.com","cbd.com","green gorilla.com","endoca.com",
    "socialcbd.com","penguincbd.com","fab cbd.com","sabaidee.com",
    "katscbd.com","nuleafnaturals.com","populum.com","cbd.co",
    "hempbombs.com","justcbdstore.com","cbd wellness.com","pluscbd oil.com",
    "elixinol.com","receptra.com","veritasfarms.com","sagely.com","zatural.com",
    "cbd lion.com","cbd genesis.com","hempworx.com","ctfo.com","hemplucid.com",
    "sunsoil.com","extract labs.com","brown girl jane.com","golde.com","beambotanicals.com",
    "lazarus naturals.com","papa and barkley.com","mary's medicinals.com","dosist.com",
    "cbd wellness.com","sagely naturals.com","holistapet.com","honestpaws.com","innovetpet.com")

_add("health_supplements","nootropics",
    "nootropicsdepot.com","nootropicsource.com","pure nootropics.com","science.bio",
    "newmind.com","botany.bio","ceretropic.com","absorbyourhealth.com",
    "liftmode.com","nootropics.com","paradigm peptides.com","peptidesciences.com",
    "limited life nootropics.com","health naturals.com","vitamonk.com","peaknootropics.com",
    "intellimeds.net","british-supplements.com","mindnutrition.com","brainzyme.com",
    "nootrobox.com","hvmn.com","nootroo.com","mindlabpro.com","neurohacker.com",
    "qualia.com","onnit.com","brainmd.com","davincilabs.com","plexusworldwide.com",
    "thrivous.com","nourihealth.com","zhounutrition.com","forestleaf.com",
    "nootropics.co","nootropicsunlimited.com","nootropicgeek.com","nootropicsexpert.com",
    "bestnootropic.org","nootropicsreview.org","nootriment.com","nootropicboost.com",
    "nootropicsexperience.com","brain boost.com","cognizin.com","neuriva.com","prevagen.com")

_add("health_supplements","greens",
    "athleticgreens.com","organifi.com","bloomnu.com","amazinggrass.com",
    "green vibrance.com","macro greens.com","kyo-green.com","greens first.com",
    "it works greens.com","balance of nature.com","texas superfood.com","e3live.com",
    "energybits.com","chloella.com","organic burst.com","natural flow.com",
    "supergreen tonik.com","jocko fuel.com","wholesome wellness.com","peak performance.com",
    "phytomulti.com","raw organic wheatgrass.com","barleens.com","re-lyte.com",
    "garden of life.com","new chapter.com","nature's way.com","source naturals.com",
    "solgar.com","mega food.com","innate response.com","enzymedica.com",
    "standard process.com","mediherb.com","gaia herbs.com","herb pharm.com",
    "wish garden.com","urban moonshine.com","bach remedies.com","rescue remedy.com")

_add("health_supplements","meal_delivery",
    "sprigandtarkin.com","gourmet prep.com","sprig.com","munchery.com",
    "naturebox.com","graze.com","bulkbox.com","munchpak.com","trytheworld.com",
    "universalyums.com","snackcrate.com","boka.com","sweetjuly.com","greystone.com",
    "pepperplate.com","plantoeat.com","e-meals.com","gatheredtable.com","cooksmarts.com",
    "paprikaapp.com","cooklist.co","mealime.com","tasty.co","sidechef.com",
    "bigoven.com","yummly.com","epicurious.com","allrecipes.com","food52.com",
    "tasteofhome.com","delish.com","bonappetit.com","savoryonline.com","thekitchn.com",
    "smittenkitchen.com","pinchofyum.com","halfbakedharvest.com","minimalistbaker.com",
    "cookieandkate.com","ohsheglows.com","loveandlemons.com","101cookbooks.com",
    "simplyrecipes.com","seriouseats.com","thespruceeats.com","foodnetwork.com")

_add("health_supplements","collagen",
    "greatlakesgelatin.com","vitalproteins.com","neo cell.com","youtheory.com","reserveage.com",
    "ancientnutrition.com","bulletproof.com","primal kitchen.com","further food.com",
    "sportsresearch.com","california gold nutrition.com","doctorsbest.com","nowfoods.com",
    "thorne.com","pure encapsulations.com","natural factors.com","life extension.com",
    "dual health.com","codeage.com","forestleaf.com","zhounutrition.com",
    "healthy origins.com","swanson vitamins.com","piping rock.com","puritan.com",
    "dr axe.com","mindbodygreen.com","organifi.com","beauty collagen.com",
    "collagen for her.com","collagen co.com","bare blaze.com","bubs naturals.com",
    "ancestral supplements.com","perfect supplements.com","vibrant health.com",
    "healthy cell.com","care of.com","ritual.com","persona nutrition.com","hum nutrition.com")

_add("health_supplements","probiotics",
    "seed.com","ritual.com","care of.com","humnutrition.com","persona.com",
    "garden of life.com","megafood.com","newchapter.com","naturesway.com",
    "nowfoods.com","solgar.com","jarrow.com","doctorsbest.com","thorne.com",
    "pure encapsulations.com","culturelle.com","align.com","florastor.com",
    "renew life.com","hyperbiotics.com","dr formulas.com","1md.org",
    "lovebug probiotics.com","biokult.com","udo's choice.com","genestra brands.com",
    "ortho molecular.com","klaire labs.com","metagenics.com","integrative therapeutics.com",
    "just thrive.com","sacred life.com","probiogen.com","probulin.com",
    "olixy.com","gutify.com","blisprobiotics.com","optibacprobiotics.com",
    "activia.com","yakult.com","danactive.com","lifeway kefir.com","goodbelly.com")

_add("health_supplements","tea",
    "davidstea.com","teavana.com","adagio.com","harney.com","rishi-tea.com",
    "artoftea.com","mightyleaf.com","teaforte.com","revolutiontea.com",
    "tazo.com","twinings.com","bigelowtea.com","celestial seasonings.com",
    "stashtea.com","republicoftea.com","pg tips.com","yorkshiretea.com",
    "typhoo.com","barrys tea.com","lyons tea.com","dilmah tea.com",
    "ahmadtea.com","taylors of harrogate.com","clipper teas.com","pukkaherbs.com",
    "yogitea.com","traditionalmedicinals.com","choiceorganicteas.com","numitea.com",
    "goodearthtea.com","tealuxe.com","teafixation.com","teavana.com","steepster.com",
    "theteaspot.com","smithtea.com","mighty leaf.com","vahtdamteas.com",
    "vahdam.com","teamakersoflondon.com","teapigs.com","herbalistalchemi.com")

# --- BABY & KIDS V2 (150+ more) ---
_add("baby_kids","gear",
    "babybjorn.com","ergobaby.com","infantino.com","jeep.com","chicco.com",
    "babyzen.com","silvercrossbaby.com","inglesina.com","quinny.com","joolz.com",
    "orbitbaby.com","4moms.com","mamaroo.com","mimoglider.com","fisher-price.com",
    "brightstarts.com","oball.com","vtech.com","leapfrog.com","babyeinstein.com",
    "lamaze.com","tiny love.com","skiphop.com","nuby.com","munchkin.com",
    "tommeetippee.com","drbrownsbaby.com","philips.com","avent.com","spectra-baby.com",
    "medela.com","lansinoh.com","haakaa.com","elvie.com","willowpump.com",
    "freemie.com","bamboobies.com","kindredbravely.com","hatchcollection.com",
    "dockatot.com","snugglemeorganic.com","boppee.com","nestedbean.com",
    "sleepingbaby.com","love to dream.com","zipadee-zip.com","magicsleepsuit.com",
    "woolino.com","kytebaby.com","goumi.com","posh peanut.com","little sleepies.com",
    "magneticme.com","pehr.com","monicaandandy.com","burt's bees baby.com","honestbaby.com")

_add("baby_kids","sleep",
    "snoo.com","owletcare.com","nanit.com","cuboai.com","miku.com",
    "babysense.com","angelcarebaby.com","infantoptics.com","babylist.com","hatchbaby.com",
    "happiestbaby.com","doona.com","4moms.com","mamaroo.com","rockaroo.com",
    "babybjorn.com","tulasleep.com","baby merlin's magicsleepsuit.com","nestedbean.com",
    "dreamlandbabyco.com","bebcare.com","levana.com","motorola baby.com",
    "safety1st.com","summerinfant.com","hiccapop.com","babysmile.com",
    "fridababy.com","little remedys.com","boudreaux'sbuttpaste.com","desitin.com",
    "weledababy.com","mustela.com","tubby todd.com","evereden.com","pipettebaby.com",
    "earthmamaorganics.com","mommy's bliss.com","zarbees.com","matys.com",
    "wellements.com","childlife.com","boiron.com","hyland's.com","gerber.com",
    "beech-nut.com","earth's best.com","plum organics.com","happybaby.com","onceuponafarm.com")

_add("baby_kids","clothing",
    "janelya.com","mishaandpuff.com","ourother.co","winterwaterfactory.com",
    "baobab collection.com","the simple folk.com","rileyandcru.com","quincymae.com",
    "jamie kay.com","little creative factory.com","ardenis.com","wilsonandsylvie.com",
    "hux baby.com","headster.com","bobo choses.com","tiny cottons.com",
    "duns sweden.com","bean'sprout.com","melijoe.com","alexandalexa.com",
    "jojo maman bebe.com","vertbaudet.com","cyrillus.com","petit bateau.com",
    "jacadi.com","bonpoint.com","catimini.com","junior gaultier.com","kenzo kids.com",
    "burberry children.com","gucci kids.com","dolce gabbana junior.com","fendi kids.com",
    "little marc jacobs.com","stella mc cartney kids.com","hm kids.com","zara kids.com",
    "gap kids.com","old navy kids.com","j crew crewcuts.com","the childrens place.com",
    "carters.com","oshkosh.com","gymboree.com","crazy8.com","janieandjack.com",
    "sugar and jade.com","mes kids.com","target.com","walmart.com","costco.com")

_add("baby_kids","toys",
    "learningresources.com","melissaanddoug.com","lakeshorelearning.com","discountschoolsupply.com",
    "constructiveplaythings.com","kaplantoys.com","guidecraft.com","community playthings.com",
    "beckertoy.com","galt toys.com","dantoy.com","knex.com","plusplus.com",
    "zoob.com","magformers.com","magnatiles.com","picassotiles.com","geomag.com",
    "playmags.com","playmathtoys.com","schleich.com","papousa.com","le toy van.com",
    "john crane.com","big jigs.com","orange tree toys.com","tenderleaftoys.com",
    "sebrainterior.com","olie woohoo.com","tender leaf toys.com","manaola.com","le toyvan.com",
    "wobbel.eu","wobbel board.com","weannaki.com","kokoa.com","valtech.com","fatbraintoys.com",
    "mindware.com","clarkson toys.com","toytoise.com","wow toys.com","b toys.com",
    "green toys.com","villagetoy.com","schylling.com","toysmith.com","unclegoose.com",
    "wubbanub.com","angel dear.com","jellycat.com","gund.com","steiff.com","douglascompany.com")

# --- HOME DECOR V2 (200+ more) ---
_add("home","furniture",
    "ikea.com","wayfair.com","overstock.com","allmodern.com","article.com",
    "burrow.com","floydhome.com","albanypark.com","joybird.com","interior define.com",
    "benchmade modern.com","maidenhome.com","insideweather.com","campaign.com",
    "sabai.design","medleyhome.com","apt2b.com","modshop.com","franceandson.com",
    "kardiel.com","roveconcepts.com","article.com","polyandbark.com","sofa works.com",
    "dallas sofa mart.com","first-oak.com","thefutureperfect.com","rh modern.com",
    "four hands.com","hookerfurniture.com","flexsteel.com","lazboy.com",
    "ethanallen.com","bassettfurniture.com","bernhardtdesign.com","centuryfurniture.com",
    "bakerfurniture.com","hickorychair.com","hancockandmoore.com","bradington young.com",
    "stickley.com","thomas moser.com","mackintosh.com","conranshop.com","tomdixon.net",
    "kartell.com","vitra.com","hermanmiller.com","knoll.com","steelcase.com",
    "hay.com","muuto.com","fermliving.com","normann-copenhagen.com","menu.com",
    "boconcept.com","norr11.com","fredercia.com","carlhansen.com","capellin.com")

_add("home","bedding",
    "brooklinen.com","parachutehome.com","bollandbranch.com","coyuchi.com",
    "snowehome.com","rileyhome.com","linenspa.com","mellanni.com",
    "nestbedding.com","silkandsnow.com","yogabed.com","dreamcloudsleep.com",
    "nolahmattress.com","amerisleep.com","brentwoodhome.com","laylasleep.com",
    "puffy.com","tempurpedic.com","simmons.com","serta.com","sealy.com",
    "stearnsandfoster.com","aierloom.com","kingsdown.com","beautyrest.com",
    "sleeplikethedead.com","sleepfoundation.org","sleepjunkie.com","mattressnerd.com",
    "the strategist mattress.com","goodhousekeeping.com","consumerreports.org",
    "overstock.com","wayfair.com","amazon.com","macys.com","bedbathandbeyond.com",
    "target.com","walmart.com","costco.com","sam'sclub.com","nordstrom.com",
    "neimanmarcus.com","saks.com","bloomingdales.com","potterybarn.com","crateandbarrel.com",
    "westelm.com","cb2.com","restorationhardware.com","williamssonoma.com","anthropologie.com")

_add("home","kitchen",
    "williamssonoma.com","sur la table.com","crateandbarrel.com","potterybarn.com",
    "westelm.com","food52.com","hedleyandbennett.com","greatjones.com",
    "mamasaidcook.com","chefn.com","oxo.com","chefman.com","instantpot.com",
    "ninjakitchen.com","cosori.com","cuisinart.com","kitchenaid.com","breville.com",
    "smeg.com","vitamix.com","blendtec.com","ninja.com","nutribullet.com",
    "nutri ninja.com","magic bullet.com","hamiltonbeach.com","proctor silex.com",
    "blackanddecker.com","oster.com","sunbeam.com","dash.com","elite gourmet.com",
    "zwilling.com","henckels.com","wusthof.com","shun.com","global-knife.com",
    "miyabi.com","victorinox.com","cutco.com","pamperedchef.com","lecreuset.com",
    "staub.com","lodgecastiron.com","fieldcompany.com","smitheyironware.com",
    "finexusa.com","butterpat.com","all-clad.com","mauviel.com","falkcopper.com",
    "debuyer.com","matferbourgeat.com","emilehenry.com","apilco.com","revolution cooking.com")

_add("home","candles",
    "yankeecandle.com","woodwick.com","chesapeakebaycandle.com","swancreek candle.com",
    "bridgewatercandle.com","trappcandles.com","illuminations.com","candlelight.com",
    "rootcandles.com","beeswaxcandles.com","diptyqueparis.com","jo malone.com",
    "lelabo.com","byredo.com","cire trudon.com","fornasetti.com","voluspa.com",
    "nestnewyork.com","pfcandleco.com","boy smells.com","otherland.com",
    "homesick.com","capri blue.com","capriblue.com","hotelcollection.com",
    "antropologie.com","apotheke.com","linari.com","neomorganics.com","thisworks.com",
    "aroma360.com","mala the brand.com","kanesso.com","elleshop.com","truebrothers.com",
    "cabi candles.com","votivo.com","rosy rings.com","lafco.com","thymes.com",
    "mrsmeyers.com","methodhome.com","grovecollaborative.com","publix.com")

_add("home","cleaning",
    "norwex.com","ecos.com","melaleuca.com","happymammoth.com","branchbasics.com",
    "cleanhappens.com","dr bronners.com","salsuds.com","bubbles.com",
    "kinsley gray.com","saje.com","by humboldt.com","puracy.com","babyganics.com",
    "honest.com","methodhome.com","mrsmeyers.com","seventhgeneration.com",
    "seventh generation.com","everspring.com","cleancult.com","blueland.com",
    "dropps.com","trulyfreehome.com","supernatural.com","forceofnatureclean.com",
    "humblebrands.com","goodcleanlove.com","lovehomeandplanet.com","methodhome.com",
    "ecover.com","biokleen.com","natulim.com","mollyssuds.com","rockingreensoap.com",
    "charleyssoap.com","thelaundreess.com","tide.com","all-laundry.com","gain.com",
    "downy.com","bounce.com","snuggle.com","shout.com","oxyclean.com",
    "thespruce.com","cleanmama.com","cleanmyspace.com","melissa maker.com")

_add("home","plants",
    "pistilsnursery.com","leonandgeorge.com","greeneryunlimited.com","thesill.com",
    "bloomscape.com","easyplant.com","whiteflowerfarm.com","burpee.com",
    "parkseed.com","johnnyseeds.com","rareseeds.com","bakerscreekseeds.com",
    "gardeners.com","territorialseed.com","highmowingseeds.com","southernexposure.com",
    "adaptive seeds.com","seed savers exchange.com","swallowtailgardenseeds.com",
    "botanicalinterests.com","reneesgarden.com","floretflowers.com","johnnyseeds.com",
    "dutchbulbs.com","brentandbeckysbulbs.com","vanengelen.com","colorblends.com",
    "tulipworld.com","brecks.com","kvanbourgondien.com","michiganbulb.com",
    "springhillnursery.com","gurneys.com","gardenharvestsupply.com",
    "planetnatural.com","arbico-organics.com","groworganic.com","peacefulvalley.com",
    "homedepot.com","lowes.com","menards.com","acehardware.com","tractorsupply.com")

# --- BEAUTY & SKINCARE (200+ new) ---
_add("beauty","skincare",
    "sephora.com","ulta.com","dermstore.com","skinstore.com","bluemercury.com",
    "spacenk.com","cultbeauty.com","lookfantastic.com","feelunique.com",
    "thehut.com","skincareexpress.com","lovelyskin.com","skinactives.com",
    "cosmeticmarket.com","glowrecipe.com","drunkelEphant.com","sundayriley.com",
    "tatcha.com","caudalie.com","summerfridays.com","tower28beauty.com",
    "supergoop.com","glowrecipe.com","laneige.com","innisfree.com","sulwhasoo.com",
    "amorepacific.com","missha.com","cosrx.com","beautyofjoseon.com","klairs.com",
    "tirtir.com","anua.com","mizon.com","bentoncosmetics.com","purito.com",
    "islabis.com","centellian.com","drjart.com","firstaidbeauty.com","herocosmetics.com",
    "peachandlily.com","thenueco.com","medicube.com","kravebeauty.com","versedskin.com",
    "goodmolecules.com","theordinary.com","inkeylist.com","paulaschoice.com",
    "dermalogica.com","skinmedica.com","skinceuticals.com","obagi.com","eltamd.com",
    "avene.com","laroche-posay.com","vichy.com","bioderma.com","uyiage.com",
    "biologique-recherche.com","isclinical.com","zo skinhealth.com","murad.com","perriconemd.com",
    "renskincare.com","olehenriksen.com","fresh.com","kiehls.com","origins.com",
    "clinique.com","esteelauder.com","lancome.com","shiseido.com","diorbeauty.com")

_add("beauty","makeup",
    "sephora.com","ulta.com","glossier.com","milk makeup.com","kosas.com",
    "iliabeauty.com","meritbeauty.com","westmanatelier.com","charlottetilbury.com",
    "pat mcgrath.com","natashadenona.com","beautybakerymakeup.com","juviasplace.com",
    "colourpop.com","morphe.com","nyxcosmetics.com","elfcosmetics.com",
    "maybelline.com","lorealparis.com","covergirl.com","revlon.com",
    "rimmellondon.com","wetnwildbeauty.com","essencemakeup.com","catrice.com",
    "hudabeauty.com","anastasiabeverlyhills.com","toofaced.com","tartecosmetics.com",
    "nars.com","mac.com","bobbibrown.com","urbandecay.com","smashbox.com",
    "benefitcosmetics.com","clinique.com","esteelauder.com","lancome.com",
    "yslbeauty.com","dior.com","chanel.com","tomford.com","armani-beauty.com",
    "gucci beauty.com","givenchybeauty.com","bobbibrown.com","hourglass.com",
    "jouercosmetics.com","bitebeauty.com","bareminerals.com","kvd beauty.com","fentybeauty.com",
    "rarebeauty.com","hauslabs.com","violettefr.com","jonesroadbeauty.com","saie.com")

_add("beauty","hair",
    "macadamia hair.com","gussi hair.com","function of beauty.com","prose.com",
    "aquis.com","kitsch.com","slip.com","maneclub.com","briogeohair.com",
    "amika.com","igk.com","ouai.com","olaplex.com","verbproducts.com",
    "livingproof.com","kerastase.com","shu uemura.com","moroccanoil.com",
    "oribe.com","christophe robin.com","leonor greyl.com","rahuabeauty.com",
    "davines.com","aveda.com","bumbleandbumble.com","paimitchell.com",
    "redken.com","matrix.com","lorealprofessionnel.com","wella.com",
    "goldwell.com","schwarzkopf.com","tigi.com","bedhead.com","johnfrieda.com",
    "nexus.com","ogxbeauty.com","sheamoisture.com","mielleorganics.com","camillerose.com",
    "buntanicals.com","asiamn.com","patternbeauty.com","breadbeautysupply.com",
    "curlssmith.com","bouncecurl.com","floraandcurls.com","innersensebeauty.com",
    "curls.com","missjessies.com","mixedchicks.com","kinkychicks.com","jessicurl.com")

_add("beauty","bath_body",
    "dove.com","nivea.com","vaseline.com","aveeno.com","cetaphil.com",
    "cerave.com","vanicream.com","eucerin.com","la roche-posay.com","avene.com",
    "loccitane.com","sabon.com","rituals.com","bondino.com","thebodyshop.com",
    "bathandbodyworks.com","philosophy.com","soldejaneiro.com","byredo.com",
    "jo malone.com","diptyqueparis.com","le labo.com","aesopskin.com","malinandgoetz.com",
    "necessaire.com","salt and stone.com","oars and alps.com","nativecos.com",
    "schmidts.com","every man jack.com","dr squatch.com","huron.com","cardon.com",
    "bravemen.com","brickell men's products.com","anthony.com","jack black.com",
    "ursa major.com","oars and alps.com","corpus naturals.com","saltair.com",
    "flamingo.com","billie.com","leaf shave.com","athena club.com","harrys.com",
    "dollarshaveclub.com","bombayshavingcompany.com","rockwellrazors.com","supply.co",
    "onebladeshave.com","hensonshaving.com","alleyoop.com","leaf shave.com")

_add("beauty","fragrance",
    "sephora.com","ulta.com","fragrancenet.com","fragrancex.com","luckyscent.com",
    "twistedlily.com","olfactoryfactory.com","scentbird.com","scentbox.com",
    "luxury scent box.com","scent split.com","the perfumed court.com","surrendertochance.com",
    "fumerie.com","indigo perfume.com","tigerlily perfume.com","ministryofscent.com",
    "osswaldny.com","aedes.com","barneys.com","nordstrom.com","bloomingdales.com",
    "neimanmarcus.com","saksfifthavenue.com","harrods.com","selfridges.com","libertylondon.com",
    "printemps.com","galerieslafayette.com","kleinperfumery.com","camden gray.com",
    "bulk apothecary.com","newdirections aromatics.com","eden botanicals.com","whitelotusaromatics.com",
    "naturesgift.com","stillpointaromatics.com","aromatics.com","mountainroseherbs.com",
    "starwest-botanicals.com","frontiercoop.com","mountain rose.com","bulkherbstore.com",
    "herbco.com","pacificbotanicals.com","organicfacts.com","rawmaterial.com",
    "aromandina.com","florihana.com","youngliving.com","doterra.com","planttherapy.com")

# --- MORE SPORTS (150+ more) ---
_add("sports","outdoor",
    "rei.com","backcountry.com","moosejaw.com","campsaver.com","steepandcheap.com",
    "enwild.com","basecampgear.com","campman.com","outdoorgearlab.com","switchbacktravel.com",
    "cleverhiker.com","thetrek.com","sectionhiker.com","hikingwithdave.com","backpackinglight.com",
    "garagegrowngear.com","hikelight.com","zpacks.com","hyperlitemountaingear.com",
    "gossamergear.com","mountainlaureldesigns.com","enlightenedequipment.com","ugqoutdoor.com",
    "hammockgear.com","war bonnet outdoors.com","dutchwaregear.com","rippedgear.com",
    "kammok.com","eaglesnestoutfitters.com","hennessyhammock.com","clarkjunglehammock.com",
    "lawsonhammock.com","sierradesigns.com","mec.ca","taigaworks.com","equipuk.com",
    "alpkit.com","terra nova equipment.com","rab.equipment.com","bergan's.no","norrona.com",
    "66north.com","klattermusen.com","haglofs.com","peakdesign.com","fjallraven.com",
    "hellyhansen.com","hhmountain.com","stio.com","flylowgear.com","trewgear.com",
    "freefly apparel.com","duckworthco.com","voormi.com","buckknives.com","leatherman.com")

_add("sports","cycling",
    "performancebike.com","jensonusa.com","competitivecyclist.com","westernbikeworks.com",
    "nashbar.com","bikebling.com","planetcyclery.com","biketiresdirect.com",
    "worldwidecyclery.com","theproscloset.com","mikesbikes.com","eriksbikeshop.com",
    "wheelandsprocket.com","bikesonline.com","chainreactioncycles.com",
    "wiggle.com","probikeshop.com","bike-discount.de","bike24.com",
    "merlincycles.com","tredz.co.uk","evanscycles.com","rutlandcycling.com",
    "winstanleysbikes.co.uk","leisurelakesbikes.com","freewheel.co.uk",
    "ribblecycles.co.uk","planetx.co.uk","orrobikes.com","canyon.com",
    "cervorthos.com","bianchi.com","wilier.com","colnago.com","pinarello.com",
    "3t.bike","factor bikes.com","openup.com","cielo.ch","cinelli.it",
    "light-bikes.com","intend-bc.com","trickstuff.com","magura.com","shimano.com",
    "sram.com","hopetech.com","trpbrakes.com","industrynine.com","chrisking.com",
    "philwood.com","whiteind.com","paulcomp.com","velo-orange.com","simworks.com")

_add("sports","fitness",
    "peloton.com","tondal.com","echelon.com","nordictrack.com","proform.com",
    "bowflex.com","schwinnfitness.com","nautilus.com","octanefitness.com",
    "precor.com","lifefitness.com","technogym.com","matrixfitness.com","freemotionfitness.com",
    "starvac.com","cybexintl.com","truefitness.com","body solid.com","powertecfitness.com",
    "roguefitness.com","titan.fitness","repfitness.com","fringe sport.com",
    "getrxd.com","garagegymreviews.com","bells of steel.com","prxperformance.com",
    "torquefitness.com","sorinex.com","elitefts.com","legendfitness.com",
    "forceusa.com","inspirefitness.com","freeformfitness.com","cdnsportlab.com",
    "kengurupro.com","pitbullgym.com","americanbarbell.com","vulcanstrength.com",
    "wrighthand.com","strengthshopusa.com","valorfitness.com","bolton fitness.com",
    "bodeefit.com","gymboxfitness.com","gorillafitness.com","epicfitness.com")

_add("sports","water_sports",
    "surfline.com","swellinfo.com","magicseaweed.com","surf-forecast.com",
    "surfrider.org","wetsuitwarehouse.com","surfstitch.com","cleanlinesurf.com",
    "southcoast.com","surfstationstore.com","realwatersports.com","missionbeachsurf.com",
    "islesurfboards.com","channel islands surfboards.com","lostsurfboards.com",
    "pyzelsurf.com","dahawaii.com","rustysurfboards.com","almerick.com",
    "quiksilver.com","billabong.com","ripcurl.com","vissla.com","sisstr.com",
    "neasurf.com","xcelwetsuits.com","onedesh.com","needessentials.com","epatagonia.com",
    "oceanrodeo.com","mysticboarding.com","ion-products.com","ride engine.com",
    "cabrinha.com","naish.com","slingshotsports.com","corekites.com",
    "duotonesports.com","ozonekites.com","ocean rodeo.com","flysurfer.com","liquidsurf.com")

# --- LUXURY & DESIGNER (150+ more) ---
_add("apparel","luxury",
    "hermes.com","chanel.com","louisvuitton.com","gucci.com","prada.com","dior.com",
    "fendi.com","bottegaveneta.com","balenciaga.com","valentino.com","alexandermcqueen.com",
    "givenchy.com","ysl.com","saintlaurent.com","celine.com","loewe.com","jacquemus.com",
    "jilsander.com","lanvin.com","thombrowne.com","moncler.com","canadagoose.com",
    "brunellocucinelli.com","lora piana.com","kiton.com","isai.it","cesareattolini.com",
    "stefanoricci.com","brioni.com","tomford.com","giorgioarmani.com","emporioarmani.com",
    "versace.com","etro.com","missoni.com","robertocavalli.com","moschino.com",
    "dolcegabbana.com","salvatoreferragamo.com","bulgari.com","cartier.com",
    "tiffany.com","van cleefandarpels.com","harrywinston.com","piaget.com","chopard.com",
    "bellacara.com","forum.com","theoutnet.com","yoox.com","gilt.com","ruelala.com",
    "farfetch.com","ssense.com","mytheresa.com","matchesfashion.com","italist.com",
    "lncc.com","antonioli.eu","pollyanna.com","tessabit.com","cettire.com",
    "endclothing.com","thewebster.com","slamjam.com","vrients.com","vooberlin.com")

# --- AUTOMOTIVE V2 (100+ more) ---
_add("automotive","parts",
    "4wheelparts.com","quadratec.com","northridge4x4.com","polyperformance.com",
    "metalcloak.com","claytonoffroad.com","rustysoffroad.com","rockkrawler.com",
    "iconvehicledynamics.com","kingoffroad.com","foxfactory.com","bilstein.com",
    "oldmanemu.com","arbusa.com","superiorengineering.com","skyjacker.com",
    "procompusa.com","rancho.com","monroe.com","kyb.com","koni.com",
    "belltech.com","spohn.net","ridetech.com","speedwaymotors.com","jegs.com",
    "summitracing.com","rockauto.com","carparts.com","1aauto.com","detroitaxle.com",
    "mopar.com","fordpartsgiant.com","toyotapartsdeal.com","hondapartsnow.com",
    "subarupartsdeal.com","vwdirectparts.com","bmwpartspros.com","mercedespartscenter.com",
    "turnermotorsport.com","ecstuning.com","fcp euro.com","pelicanparts.com","autohausaz.com",
    "ipdusa.com","bpracing.com","andysautosport.com","carid.com","autoanything.com")

_add("automotive","detailing",
    "mcarproducts.com","poorboysworld.com","pinnaclewax.com","wolfgangcarcare.com",
    "autogeek.com","detailedimage.com","autopia-carcare.com","autodetailing.com",
    "detailking.com","detailersdomain.com","obsessedgarage.com","theragcompany.com",
    "microfibertech.com","chemicalguys.com","griotsgarage.com","adamspolishes.com",
    "meguires.com","mothers.com","turtlewax.com","zainostore.com","p21sonline.com",
    "sonax.com","carpro-us.com","gyeonusa.com","kamikaze-collection.com",
    "optimumcarcare.com","pbls.com","blackwow.com","detailers helper.com",
    "stjames1912.com","ammonyc.com","detailgarage.com","lrpmotorsports.com",
    "obsessive detail.com","detailershelper.com","supremebath.com","polishangel.us",
    "gtechniq.com","22ple.com","feynlab.com","cquartz.com","iglcoatings.com","ceramicpro.com",
    "modesta.co","drbeasleys.com","gallonproducts.com","detailsupply.com","detailing.com")

# ============================================================
# GENERATION
# ============================================================

def load_domains(filepath):
    if not filepath.exists():
        return set()
    with open(filepath) as f:
        data = json.load(f)
    if isinstance(data, list):
        items = data
    else:
        items = data.get("merchants", data.get("invalid", []))
    return {d["domain"].lower() if isinstance(d, dict) else d.lower() for d in items}


def generate():
    DATA.mkdir(parents=True, exist_ok=True)

    indexed = load_domains(MERCHANTS)
    invalid = load_domains(INVALID)
    candidates = load_domains(CANDIDATES) if CANDIDATES.exists() else set()
    all_known = indexed | invalid | candidates

    print(f"Indexed: {len(indexed)} | Invalid: {len(invalid)} | Candidates: {len(candidates)}")

    new_candidates = []
    seen = set()
    for domain, cat, subcat in BRANDS:
        dl = domain.lower()
        if dl in all_known or dl in seen:
            continue
        seen.add(dl)
        new_candidates.append({"domain": domain, "category": cat, "subcategory": subcat, "source": "curated_dtc"})

    print(f"Total brands: {len(BRANDS)} → New candidates: {len(new_candidates)}")

    cats = Counter(c["category"] for c in new_candidates)
    for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25} {n:>5}")

    # Save expanded candidates
    existing_list = []
    if CANDIDATES.exists():
        with open(CANDIDATES) as f:
            data = json.load(f)
        existing_list = data if isinstance(data, list) else data.get("merchants", [])

    merged = existing_list + new_candidates
    with open(CANDIDATES, "w") as f:
        json.dump({"description": "US Shopify merchant candidates (curated DTC)",
                    "count": len(merged), "merchants": merged,
                    "updated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)

    # Save temp curated
    with open(CURATED, "w") as f:
        json.dump({"description": "BUY-11202 curated DTC candidates",
                    "count": len(new_candidates), "merchants": new_candidates,
                    "generated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)

    print(f"\nExpanded candidates: {CANDIDATES} ({len(merged)} total)")
    print(f"Curated temp: {CURATED} ({len(new_candidates)} entries)")
    est = int(len(new_candidates) * 0.32)
    print(f"Estimated valid (32% hit): {est}")
    return new_candidates

# ============================================================
# VALIDATION
# ============================================================

async def validate_domain(domain, timeout=8):
    import aiohttp
    url = f"https://{domain}/products.json"
    headers = {"User-Agent": "BuyWhere-Discovery/1.0", "Accept": "application/json"}
    try:
        connector = aiohttp.TCPConnector(ssl=False, force_close=True)
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout_obj) as ses:
            async with ses.get(url, headers=headers, allow_redirects=True) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json()
                        if isinstance(data, dict) and "products" in data:
                            return True, f"ok:{len(data['products'])}"
                        return False, "bad_structure"
                    except Exception:
                        return False, "bad_json"
                return False, f"http_{resp.status}"
    except asyncio.TimeoutError:
        return False, "timeout"
    except Exception as e:
        msg = str(e).lower()
        if "certificate" in msg or "ssl" in msg:
            return False, "ssl"
        if "name or service" in msg or "nodename" in msg:
            return False, "dns"
        if "connection refused" in msg:
            return False, "refused"
        return False, f"error:{msg[:60]}"


async def validate_batch(candidates, concurrency=25, timeout=8):
    sem = asyncio.Semaphore(concurrency)
    async def one(c):
        async with sem:
            ok, reason = await validate_domain(c["domain"], timeout)
            c["valid"] = ok
            c["reason"] = reason
            c["validated_at"] = datetime.now(timezone.utc).isoformat()
            if ok and ":" in reason:
                c["product_count"] = int(reason.split(":")[1])
            return c

    tasks = [one(c) for c in candidates]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    valid, invalid = [], []
    for r in results:
        if isinstance(r, Exception):
            invalid.append({"domain": "unknown", "error": str(r)})
        elif r.get("valid"):
            valid.append(r)
        else:
            invalid.append(r)
    return valid, invalid


def validate(limit=0, concurrency=30):
    with open(CURATED) as f:
        data = json.load(f)
    candidates = data.get("merchants", []) if isinstance(data, dict) else data

    existing = load_domains(MERCHANTS)
    invalid_known = load_domains(INVALID)

    to_check = [c for c in candidates
                if c["domain"].lower() not in existing
                and c["domain"].lower() not in invalid_known]

    if limit:
        to_check = to_check[:limit]

    print(f"Validating {len(to_check)} candidates (concurrency={concurrency})")
    print(f"  Existing merchants: {len(existing)}")
    print(f"  Known invalid: {len(invalid_known)}\n")

    chunk = 200
    all_valid, all_invalid = [], []

    for i in range(0, len(to_check), chunk):
        ch = to_check[i:i + chunk]
        print(f"Chunk {i//chunk + 1}: {i+1}-{i+len(ch)} of {len(to_check)}...")
        v, iv = asyncio.run(validate_batch(ch, concurrency))
        all_valid.extend(v)
        all_invalid.extend(iv)
        rate = len(v) / len(ch) * 100 if ch else 0
        print(f"  Valid: {len(v)} | Invalid: {len(iv)} | Hit: {rate:.1f}%")
        print(f"  Running: {len(all_valid)} valid, {len(all_invalid)} invalid\n")

    total = len(all_valid) + len(all_invalid)
    hit_rate = len(all_valid) / total * 100 if total else 0
    print(f"\n{'='*60}")
    print(f"VALIDATION COMPLETE — {len(all_valid)} valid / {len(all_invalid)} invalid ({hit_rate:.1f}%)")

    cats = Counter(c.get("category", "unknown") for c in all_valid)
    print(f"\nValid by category:")
    for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25} {n:>4}")

    # Merge into merchants
    if all_valid:
        existing_list = []
        if MERCHANTS.exists():
            with open(MERCHANTS) as f:
                md = json.load(f)
            existing_list = md if isinstance(md, list) else md.get("merchants", [])

        existing_map = {}
        for m in existing_list:
            if isinstance(m, dict):
                existing_map[m["domain"].lower()] = m
            else:
                existing_map[m.lower()] = {"domain": m}

        merged = 0
        for v in all_valid:
            domain = v["domain"].lower()
            slug = domain.replace(".", "").replace("-", "")
            if domain not in existing_map:
                existing_map[domain] = {
                    "domain": v["domain"],
                    "source": f"shopify_{slug}",
                    "country": "US", "currency": "USD",
                    "category": v.get("category", "unknown"),
                    "subcategory": v.get("subcategory"),
                    "source_attribution": "curated_dtc",
                    "last_validated": v.get("validated_at"),
                    "product_count": v.get("product_count", 0),
                }
                merged += 1

        merchants = sorted(existing_map.values(), key=lambda m: m.get("category", ""))
        with open(MERCHANTS, "w") as f:
            json.dump({"description": "US Shopify merchant catalog",
                        "count": len(merchants), "merchants": merchants,
                        "updated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)
        print(f"\nMerged {merged} new merchants → catalog: {len(merchants)}")

    # Update invalid file
    if all_invalid:
        for iv in all_invalid:
            d = iv.get("domain", "").lower()
            if d and d not in invalid_known:
                invalid_known.add(d)
        inv_list = sorted([{"domain": d} for d in invalid_known], key=lambda x: x["domain"])
        with open(INVALID, "w") as f:
            json.dump({"invalid": inv_list, "count": len(inv_list),
                       "updated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)
        print(f"Invalid file updated: {len(invalid_known)} total")

    return all_valid, all_invalid


def main():
    ap = argparse.ArgumentParser(description="BUY-11202: DTC brand discovery + validation")
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=30)
    args = ap.parse_args()

    do_gen = args.generate or args.all
    do_val = args.validate or args.all

    if do_gen:
        generate()
    if do_val:
        validate(args.limit, args.concurrency)
    if not do_gen and not do_val:
        ap.print_help()


if __name__ == "__main__":
    main()
