# Shelf art

The pictures Shelf (a game launcher for the ZX Spectrum Next) shows for games it has no picture of. Shelf asks this site for a picture by
the game's title; the pictures are here in a convenient form and a build turns them into the two small files Shelf downloads.

## Add a picture

1. Put a picture in `pictures/` named after the game: `pictures/Manic Miner.png` (PNG, BMP, GIF or JPG, under 500 KB).
   On the web: *Add file > Upload files* in `pictures/` makes the pull request for you.
2. Choose a screenshot of the game itself, about twice as wide as tall. Shelf shows 72x36 pixels, so detail does not matter;
   a recognisable scene does. A title card, a publisher's logo or a loading screen is rarely much use.
3. Open the pull request. A check lists any problem and shows what Shelf will make of it. Fill in the template's questions.

Names do not have to match exactly: `Manic Miner`, `ManicMiner` and `manic_miner` are the same game to Shelf (only letters and digits
count, whatever the case), and only the first 30 characters of a name are looked at.

## How it works

- `tools/check.py` runs on every pull request and posts what it found (it never runs anything from the pull request but the pictures).
- When a pull request is merged, `tools/mkpack.py` rebuilds everything from `pictures/` into `art.idx` (a sorted list of title keys)
  and `art.pak` (the pictures as Shelf stores them) and publishes them with GitHub Pages. Format: Shelf's `docs/art-fetch.md`.
- `tools/mkpack.py` here is a copy of the one in Shelf's repo; its title key has to stay the same as Shelf's.

## Takedowns

The pictures are screenshots; if you are the owner of one and want it gone, open an issue and it will be removed.
