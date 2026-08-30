# M3U-to-XMLTV Channel Mapping

`map_epg.py` creates a reviewable mapping between M3U channel names and XMLTV channel IDs. It normalizes case, accents, punctuation, country prefixes, quality labels, regional suffixes, and common provider noise before scoring candidates.

## Usage

```bash
python3 scripts/map_epg.py \
  --m3u playlist.m3u \
  --xmltv /path/to/epg.xml \
  --out epg-map.json
```

The command writes JSON and CSV files. Each record contains the M3U title, the selected XMLTV ID and name, a score, confidence level, matching reason, and up to three alternative candidates.

The default thresholds are conservative. Scores of `0.92` or higher are labelled `high` and are suitable for automatic review. Scores from `0.80` through `0.9199` are labelled `review` and should be checked before writing `tvg-id` values into the playlist. Lower scores remain `unmatched`.

## Latest measured run

Against the current 11,774-entry GitHub playlist and the downloaded XMLTV feed containing 15,702 channels, the mapper produced 820 high-confidence matches, 281 review candidates, and 10,673 unmatched channels. The playlist currently has no `tvg-id` attributes, so the mapper uses normalized names rather than provider IDs.

The output is intentionally review-first. Do not automatically apply review or unmatched records to a production playlist without checking that the guide channel is the same broadcaster, territory, and feed variant.
