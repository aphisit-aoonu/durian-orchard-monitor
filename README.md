# Durian Orchard Monitor

Spotting durians on the tree with a camera, following each fruit as the camera moves,
and working out how a small orchard could be harvested with one machine on a rail.

![Durians found on six trees](docs/gallery.jpg)

A one-minute walkthrough: [`docs/demo.mp4`](docs/demo.mp4)

## Why

Durian growers lose money when fruit is cut too early, and nobody can remember which fruit
set on which day across hundreds of trees. Harvesting is also dangerous: someone climbs
10 metres up and lowers each fruit on a rope.

The long-term idea is one inspection cart that runs on a rail past every tree, a short pole
cutter with a catch bag, and one collection point. It assumes trees topped at about 6 m, which
growers already do so they can harvest without climbing. For old trees of 10 m and more I found
no machine that does this, so the system only tells the climbing crew which trees are due.
This repo is the software side, plus a simulation of the rest so the idea can be checked on paper first.

## What works today

**Finding fruit, no training.** An open-vocabulary detector (OWLv2) finds durians from the text
prompt "a durian fruit". The gallery above is six Wikimedia Commons photos: close up, far away,
against the sky, and young fruit. A cleanup step removes the usual duplicate boxes (a box on part
of a fruit, or one box spanning two fruits).

**One id per fruit while the camera moves.** Handheld video breaks naive tracking: every time
the camera pans, the same fruit gets a new number, and panning looks like falling. The tracker
estimates camera motion from the background (ORB features + RANSAC) and matches fruit in
camera-compensated coordinates. On a test clip of a farmer harvesting, it follows one fruit
from the branch all the way down the rope and reports it once as "lowered from the tree".

**Honest limits.** Very close to the fruit, near and far things move differently and the motion
estimate breaks down, so the running count over-counts. A camera on a rail cart moves along a
straight line at a steady distance, which is exactly the case where this works, and is one more
reason for the rail design.

Ripeness is **not** guessed from skin colour. I tried it: mature durians are still green,
and it mislabelled most fruit. The plan is to count days from flowering instead (Monthong is
about 120 days).

## The orchard, simulated

![Orchard plan](docs/sim_plan_en.png)

A 48-tree plot (8 x 6, 9 m by 10 m spacing, about 3.3 rai). The rail runs down every second
alley, so one pass serves the row on each side:

- 423 m of rail, no tree more than 5 m from it, never through a canopy (checked in tests)
- At 0.5 m/s with a 30 s camera stop per tree, one full round takes about 38 minutes

![One inspection round](docs/sim_round_frame.jpg)

[`docs/sim_round_en.mp4`](docs/sim_round_en.mp4) plays one round: the cart stops at trees with
ready fruit, the pole cutter cuts the stem, the fruit drops 0.3 m into the bag on the cutter head,
the pole lowers it into the basket, and at the end the collection point weighs, counts and notifies
the truck. **Which fruit is ready is random in the simulation.** Distances and timings come from the plan.

## More of the orchard, simulated

**Getting the fruit down.** Drawn to scale for a 3 kg durian. On a tree topped at 6 m, a pole of
4.2 m reaches the fruit drawn (6.4 m at the longest reach in the plan) and the fruit meets the bag
at 2.4 m/s; the same fruit dropped from 4 m hits the ground at 8.9 m/s. On an old 12 m tree the fruit
hangs at 10 m, would land at 14 m/s and would need a 10.3 m pole, and no machine is claimed for it.
The cart itself is not designed: holding 3 kg 5 m to the side puts 147 N·m on it.

![Getting the fruit down](docs/sim_catch_en.png)

**Tree height and cutting calendar.** Each tree's height against the 6 m reach (which trees to top
first), and which trees come due each week, counted as 120 days after full bloom for Monthong.
Heights and bloom dates are simulated.

![Tree height and cutting calendar](docs/sim_height_en.png)

**Soil moisture by zone.** 12 zones with one sensor and one valve each, 14 simulated days with rain.
Watering only the zones that are dry used 68% less water than watering every zone every two days, and
had far fewer waterlogged zone-days (23 vs 105), which matters because durian roots rot in standing
water. Weather and sensor values are simulated.

![Soil moisture](docs/sim_irrigation_en.png)

## Run it

Python 3.10+. A GPU helps (about 2.7 s per image on a GTX 1650, much slower on CPU).

```bash
pip install -r requirements.txt
python -m pytest

python -m scripts.fetch_commons                      # CC photos from Wikimedia Commons
python -m scripts.photo_gallery                      # out/gallery.jpg + credits

python -m scripts.video_demo analyse my_tree.mp4     # slow: detection + camera motion, cached
python -m scripts.video_demo render my_tree.mp4 en   # fast: annotated clip (en or th)

python -m scripts.sim_plan en                        # orchard plan
python -m scripts.sim_video en                       # one simulated round
python -m scripts.sim_catch en                       # topped tree vs old tall tree, to scale
python -m scripts.sim_height en                      # tree heights and cutting calendar
python -m scripts.sim_irrigation en                  # 14 days of zone watering
```

## Layout

```
durian/
  detector.py   OWLv2 wrapper + duplicate-box cleanup
  motion.py     camera motion between frames
  tracker.py    one id per fruit, lowered-fruit events
  layout.py     orchard grid and rail route, in metres
  catch.py      impact speed, pole length, load on the cart
  growth.py     tree height against the reach, days to harvest
  irrigation.py zone watering simulation
  plan_draw.py  top-down drawing
  render.py     shared drawing style
scripts/        command-line entry points
tests/
```

## Next

1. Real footage from one tree, filmed the same way every week, to test counting against a hand count
2. A small durian-specific model, fast enough for a live camera
3. Flowering dates per tree and a weekly "ready to cut" list

## Credits

Topping durian trees to 3.5–6 m so they can be harvested from the ground is existing grower
practice: [Amarin TV, Rayong grower](https://www.amarintv.com/news/social/134992),
[NSTDA on canopy control](https://www.nstda.or.th/agritec/durian-shape/).

Gallery photos are from Wikimedia Commons under CC BY / CC BY-SA licences. Authors and links
are in [`docs/gallery_credits.txt`](docs/gallery_credits.txt). The gallery image is shared under
CC BY-SA 4.0 for that reason.

Aphisit Aoonu · [LinkedIn](https://www.linkedin.com/in/aphisit-aoonu/)
