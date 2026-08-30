# EPG Research Findings

The playlist currently contains 11,774 `#EXTINF` entries and 11,774 playable URLs, but no `tvg-id` attributes. The channel names are largely provider-prefixed, such as `USA AMC`, and every entry currently uses `group-title="Live TV"`.

The iptv-org EPG project documents utilities for downloading XMLTV data from many sources and states that its channel data comes from the iptv-org database. Its repository documentation is available at https://github.com/iptv-org/epg and the project’s guide is linked there.

The candidate URL `https://iptv-epg.github.io/` currently returns a GitHub Pages 404, so it is not suitable as an EPG endpoint.

Because the playlist has no stable tvg-id values and the provider account’s channel names/regions are not guaranteed to match a public guide’s IDs, no EPG source has yet been proven to cover all channels. Coverage must be measured before adding a guide reference; adding a generic URL without matched IDs would produce unreliable or empty programme data.
