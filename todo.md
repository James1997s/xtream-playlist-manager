
- [ ] Update only the GitHub playlist workflow/file to use the confirmed Xtream source securely
- [ ] Validate and publish the refreshed GitHub `playlist.m3u` raw URL

- [ ] Retry the GitHub-only Xtream source update and regenerate `playlist.m3u` without exposing credentials

- [ ] Directly regenerate and push the GitHub `playlist.m3u` from the confirmed Xtream source, accepting exposed stream credentials

- [ ] Retry the Xtream M3U export now and push it only after complete integrity validation

- [ ] Replace only the old Xtream credential path in the existing GitHub `playlist.m3u` and push the validated result

- [ ] Replace the previous GitHub playlist credentials with the newly supplied Xtream account and push the validated update

- [ ] Find and measure a compatible XMLTV EPG source for the GitHub playlist
- [ ] Add the EPG reference and matched channel IDs to `playlist.m3u` if coverage is reliable

- [ ] Add one broad international XMLTV EPG reference as a close match to the GitHub M3U and publish the update

- [ ] Verify XMLTV feed structure and compare guide channel IDs/names against the GitHub M3U
- [ ] Report actual IPTV-player compatibility and EPG coverage limitations

- [ ] Create an automatic M3U-to-XMLTV channel mapping script with normalization, confidence scores, ambiguous candidates, and unmatched output
- [ ] Run the mapping script against the current GitHub playlist and XMLTV feed and document the results

- [ ] Apply only high-confidence XMLTV IDs to the GitHub M3U and publish the completed EPG mapping

- [ ] Replace current Xtream credentials with `try96528` / `00608496` in the existing GitHub M3U and preserve all channel metadata and EPG mappings

- [ ] Create an exact clone of the current playlist as `momslist.m3u`, validate byte-for-byte equivalence, and push it to GitHub

- [ ] Add VOD entries from the Xtream source to `playlist.m3u` and refresh `momslist.m3u` as the exact updated clone
- [ ] Validate that existing live channels, EPG reference, and mapped XMLTV IDs remain intact

- [ ] Fetch VOD from the supplied Xtream login and append movies/series while preserving the live channels and EPG mappings

- [ ] Fetch Xtream series episode details and append TV-show VOD entries to both GitHub playlists

- [x] Complete the accelerated TV-show VOD merge using successfully returned Xtream series data

- [x] Organize TV-show episodes by show and season in both GitHub playlists and preserve the grouping in future generator output

- [ ] Audit Xtream series coverage against the current GitHub M3U and report missing or partially fetched shows without modifying playlists

- [x] Fetch any missing Xtream series details and generate a complete 17,000+ series M3U regardless of file size
- [x] Reduce the GitHub playlist export below the normal repository file-size limit while preserving maximum practical content coverage
- [ ] Remove all series/show VOD entries from playlist.m3u and momslist.m3u while preserving Live TV, Movies, and EPG data
