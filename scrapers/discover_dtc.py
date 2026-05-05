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
